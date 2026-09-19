"""Pipeline completo para um agente ASSISTIR um video do YouTube com precisao verificavel.

Executa as tres camadas, cada uma com sua propria fonte de verdade:

  1. GEMINI  em blocos, direto da URL       -> o que aparece na tela e o que e dito
  2. LEGENDA pt-orig do proprio video       -> confirma cada citacao e CORRIGE o timestamp
  3. FFMPEG  frames nos instantes afirmados -> prova do que estava na tela

Nenhuma camada depende do modelo acertar tempo. O modelo so olha e descreve.

Uso:
    set GEMINI_API_KEY=...
    python assistir-youtube.py <url> [pasta_saida]

Saida:
    <pasta>/relatorio.md   timeline + tabela de verificacao
    <pasta>/frames/*.jpg   frames nos pontos medios dos intervalos (LEIA com a tool Read)
    <pasta>/transcricao.txt

Precisa de: yt-dlp, ffmpeg, ffprobe, python 3.8+, GEMINI_API_KEY (ai.google.dev).
"""
import io, json, os, re, subprocess, sys, time, unicodedata, urllib.error, urllib.request

API = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
BLOCO = 600          # 10 min: acima disso o modelo perde precisao temporal
MATCH = 0.60         # fracao de palavras para considerar citacao confirmada
MAX_FRAMES = 20      # frames amostrados para conferencia visual

# Este prompt e o resultado do teste. Pedir "a cada 1 minuto" derruba a precisao
# visual para ~60%, porque forca uma tela por minuto quando o video troca varias
# vezes no mesmo minuto. Pedir INTERVALOS resolve.
PROMPT = (
    "Assista este trecho. Liste CADA troca de tela com timestamp MM:SS absoluto do video "
    "original, no formato 'INICIO - FIM'. Para cada uma:\n"
    "(a) nome do aplicativo visivel;\n"
    "(b) TRANSCREVA o texto legivel na tela — titulos, rotulos de diagrama, itens, abas. "
    "Se for diagrama, diga as caixas e o que liga o que;\n"
    "(c) uma CITACAO VERBATIM entre aspas do que e dito nesse intervalo.\n"
    "Escreva 'ilegivel' se nao der para ler. NUNCA invente texto, numero ou nome de tela."
)


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def secs(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def hhmm(s):
    s = int(s)
    return f"{s//60:02d}:{s%60:02d}"


# ------------------------------------------------------------------ entrada

def metadata(url):
    r = sh(["yt-dlp", "--skip-download", "--print", "%(title)s\n%(duration)s", url])
    linhas = [l for l in r.stdout.strip().splitlines() if l]
    if len(linhas) < 2:
        sys.exit(f"Nao consegui ler o video.\n{r.stderr[-400:]}")
    return linhas[0], int(float(linhas[-1]))


def legendas(url, saida):
    """Baixa a faixa ORIGINAL. Nunca a traduzida: a traducao automatica corrompe
    termos tecnicos ('Claude' vira 'cloud') e contamina toda a analise."""
    for langs in ("pt-orig", "pt", "en-orig", "en"):
        sh(["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
            "--sub-langs", langs, "--sub-format", "vtt",
            "-o", os.path.join(saida, "leg.%(ext)s"), url])
        v = [f for f in os.listdir(saida) if f.endswith(".vtt")]
        if v:
            v.sort(key=lambda f: (0 if "orig" in f else 1, f))
            return os.path.join(saida, v[0])
    return None


def parse_vtt(path):
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    TS = re.compile(r"^(\d\d):(\d\d):(\d\d)\.\d+\s+-->")
    cues, t = [], None
    for line in raw.splitlines():
        m = TS.match(line)
        if m:
            h, mi, s = (int(v) for v in m.groups()); t = h * 3600 + mi * 60 + s; continue
        if not line.strip() or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or t is None:
            continue
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", "", line)).strip()
        if txt:
            cues.append((t, txt))
    seen, out = set(), []          # legenda rolante repete cada linha
    for t, txt in cues:
        if txt in seen: continue
        seen.add(txt); out.append((t, txt))
    return out


def baixar_video(url, saida):
    """So o formato mais baixo: serve para detectar QUANDO a tela muda e para
    extrair frames de conferencia. Formatos altos costumam dar 403."""
    alvo = os.path.join(saida, "video.mp4")
    for _ in range(4):
        sh(["yt-dlp", "--remote-components", "ejs:github", "-f", "worst",
            "--merge-output-format", "mp4", "-o", alvo, url])
        if os.path.exists(alvo):
            return alvo
        time.sleep(4)
    return None


# ------------------------------------------------------------------ gemini

def gemini(url, ini, fim, key):
    body = {"contents": [{"parts": [
        {"file_data": {"file_uri": url},
         "video_metadata": {"start_offset": f"{ini}s", "end_offset": f"{fim}s"}},
        {"text": PROMPT}]}],
        "generationConfig": {"maxOutputTokens": 16384}}
    for model in MODELS:
        for att in (1, 2, 3):
            try:
                req = urllib.request.Request(
                    f"{API}/models/{model}:generateContent?key={key}",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"})
                r = json.loads(urllib.request.urlopen(req, timeout=1200).read())
                c = r["candidates"][0]
                return "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))
            except urllib.error.HTTPError as e:
                sys.stderr.write(f"    [{model}] HTTP {e.code}\n")
                if e.code not in (429, 500, 503): break
                time.sleep(10 * att)     # 503 e comum em modelo novo e passa
            except Exception as e:
                sys.stderr.write(f"    [{model}] {type(e).__name__}\n"); break
    return ""


def parse_intervalos(txt):
    """Extrai (ini, fim, app, citacao) dos cabecalhos de intervalo."""
    heads = list(re.finditer(r"(\d{1,2}:\d{2})\s*[-–—�]+\s*(\d{1,2}:\d{2})", txt))
    out = []
    for i, m in enumerate(heads):
        seg = txt[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(txt)]
        app = re.search(r"Aplicativo[^:\n]{0,25}:\**\s*([^\n*(]{3,60})", seg)
        cit = re.findall(r'["“]([^"”\n]{15,300})["”]', seg)
        out.append((secs(m.group(1)), secs(m.group(2)),
                    app.group(1).strip(" :*.") if app else "?",
                    cit[0] if cit else None))
    return out


def rechecar_tela(url, t, key):
    """Fallback quando o download falha (403 e comum e imprevisivel).

    Pergunta ao modelo o que ha numa janela de 8s. Numa janela tao curta ele nao
    tem para onde derrapar, entao isso pega discordancia com a afirmacao do bloco.
    E MAIS FRACO que o frame: mesmo modelo, logo nao e prova independente — mas
    na pratica corrigiu erros reais que o bloco tinha cometido."""
    body = {"contents": [{"parts": [
        {"file_data": {"file_uri": url},
         "video_metadata": {"start_offset": f"{t}s", "end_offset": f"{t+8}s"}},
        {"text": "Diga em ate 12 palavras qual aplicativo/tela aparece. Sem explicacao."}]}],
        "generationConfig": {"maxOutputTokens": 800}}   # Gemini 3 gasta orcamento em raciocinio
    for att in (1, 2, 3):
        try:
            req = urllib.request.Request(
                f"{API}/models/{MODELS[0]}:generateContent?key={key}",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=300).read())
            c = r["candidates"][0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in c).strip().replace("\n", " ")[:70]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and att < 3: time.sleep(8); continue
            return ""
        except Exception:
            return ""
    return ""


def concorda(a, b):
    """Duas descricoes de tela apontam para o mesmo app?"""
    pa, pb = set(norm(a).split()), set(norm(b).split())
    pa -= {"o", "a", "de", "do", "da", "em", "no", "na", "e", "aplicativo", "tela", "aparece"}
    pb -= {"o", "a", "de", "do", "da", "em", "no", "na", "e", "aplicativo", "tela", "aparece"}
    return bool(pa & pb)


def localizar(cit, palavras, perto=None):
    """Janela da transcricao que melhor casa com a citacao -> (fracao, segundo_real).

    Fala repetida (um trecho reprisado, um bordao) casa em mais de um lugar. Entre
    as janelas que passam no limiar, fica a mais proxima do tempo que o modelo
    afirmou — senao a "correcao" joga a citacao para a primeira ocorrencia e
    transforma um timestamp certo em errado.
    """
    q = norm(cit).split()
    if len(q) < 4 or not palavras:
        return 0.0, None
    n, qs = len(q), set(q)
    fluxo = [w for _, w in palavras]; tempos = [t for t, _ in palavras]
    best, bt, boas = 0.0, None, []
    for i in range(max(1, len(fluxo) - n + 1)):
        h = sum(1 for w in fluxo[i:i + n] if w in qs) / n
        if h > best:
            best, bt = h, tempos[i]
        if h >= MATCH:
            boas.append((h, tempos[i]))
    if boas and perto is not None:
        topo = max(h for h, _ in boas)
        perto_ok = [(abs(t - perto), h, t) for h, t in boas if h >= topo - 0.15]
        _, h, t = min(perto_ok)
        return h, t
    return best, bt


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else "video-analise"
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("GEMINI_API_KEY nao definida no ambiente.")
    os.makedirs(os.path.join(saida, "frames"), exist_ok=True)

    titulo, dur = metadata(url)
    sys.stderr.write(f"[1/5] {titulo} ({hhmm(dur)})\n")

    sys.stderr.write("[2/5] legenda original...\n")
    vtt = legendas(url, saida)
    cues = parse_vtt(vtt) if vtt else []
    palavras = [(t, w) for t, txt in cues for w in norm(txt).split()]
    with io.open(os.path.join(saida, "transcricao.txt"), "w", encoding="utf-8") as f:
        for t, txt in cues:
            f.write(f"[{hhmm(t)}] {txt}\n")
    sys.stderr.write(f"      {len(cues)} linhas, {len(palavras)} palavras"
                     f"{'' if cues else '  (SEM LEGENDA — citacoes NAO serao verificaveis)'}\n")

    sys.stderr.write("[3/5] video em baixa (para frames)...\n")
    video = baixar_video(url, saida)
    sys.stderr.write(f"      {'ok' if video else 'FALHOU — sem prova visual'}\n")

    blocos = [(i, min(i + BLOCO, dur)) for i in range(0, dur, BLOCO)]
    sys.stderr.write(f"[4/5] Gemini em {len(blocos)} bloco(s) de {BLOCO//60} min...\n")
    intervalos, bruto = [], []
    for ini, fim in blocos:
        sys.stderr.write(f"    {hhmm(ini)}-{hhmm(fim)}\n")
        txt = gemini(url, ini, fim, key)
        bruto.append(txt); intervalos += parse_intervalos(txt)
    intervalos = sorted(set(intervalos))

    sys.stderr.write("[5/5] verificando e extraindo frames...\n")
    linhas, ok, tot, drift = [], 0, 0, []
    for a, b, app, cit in intervalos:
        if cit:
            tot += 1
            sc, real = localizar(cit, palavras, a)
            bom = sc >= MATCH; ok += bom
            if bom and real is not None: drift.append(abs(real - a))
            linhas.append((a, b, app, cit, bom, sc, real))
        else:
            linhas.append((a, b, app, None, None, 0, None))

    passo = max(1, len(intervalos) // MAX_FRAMES)
    amostra = intervalos[::passo][:MAX_FRAMES]
    frames, rechecks = [], []
    if video:
        for i, (a, b, app, _) in enumerate(amostra, 1):
            mid = (a + b) // 2 if b > a else a
            p = os.path.join(saida, "frames", f"f{i:02d}_{hhmm(mid).replace(':','m')}.jpg")
            sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(mid), "-i", video,
                "-frames:v", "1", "-vf", "scale=512:-1", p])
            if os.path.exists(p): frames.append((mid, app, p))
    else:
        sys.stderr.write("      sem video: rechecando telas por janela curta...\n")
        for a, b, app, _ in amostra[:12]:
            mid = (a + b) // 2 if b > a else a
            r = rechecar_tela(url, mid, key)
            if r: rechecks.append((mid, app, r, concorda(app, r)))

    rel = os.path.join(saida, "relatorio.md")
    with io.open(rel, "w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n\n{url} — {hhmm(dur)} — {len(intervalos)} intervalos\n\n")
        f.write("## Timeline\n\n| inicio | fim | tela | citacao | conferida | tempo REAL |\n")
        f.write("|---|---|---|---|---|---|\n")
        for a, b, app, cit, bom, sc, real in linhas:
            mark = "" if bom is None else ("OK" if bom else "**NAO**")
            f.write(f"| {hhmm(a)} | {hhmm(b)} | {app[:40]} | "
                    f"{(cit[:70] + '...') if cit and len(cit) > 70 else (cit or '')} | "
                    f"{mark} {f'{sc:.0%}' if cit else ''} | {hhmm(real) if real is not None else ''} |\n")
        if tot:
            f.write(f"\n**{ok}/{tot} citacoes confirmadas ({ok/tot:.0%}).**")
            if drift:
                import statistics as st
                f.write(f" Erro de timestamp: media {round(st.mean(drift))}s, pior {max(drift)}s.")
            f.write("\n\nDescarte as linhas **NAO** — sao parafrase apresentada como verbatim.\n"
                    "Use a coluna **tempo REAL** como timestamp; a coluna de inicio erra.\n")
        else:
            f.write("\n**Sem legenda: nenhuma citacao pode ser confirmada.**\n")
        if frames:
            f.write("\n## Frames — prova visual\n\n"
                    "A afirmacao de tela do modelo e HIPOTESE; o frame e a prova.\n"
                    "**LEIA cada arquivo abaixo com a tool Read** e confira contra a coluna 'tela'.\n\n")
            for mid, app, p in frames:
                f.write(f"- `{p}` — em {hhmm(mid)}, modelo afirma: **{app[:45]}**\n")
        elif rechecks:
            bate = sum(1 for *_, c in rechecks if c)
            f.write("\n## Telas — recheque por janela curta (fallback)\n\n"
                    "O download falhou (403), entao NAO ha frame para provar. "
                    "Em vez disso cada tela foi reperguntada numa janela de 8s, onde o "
                    "modelo nao tem como derrapar no tempo.\n\n"
                    "**Isto e mais fraco que o frame:** mesmo modelo, logo nao e prova "
                    "independente. Serve para pegar discordancia, nao para confirmar.\n\n")
            f.write("| instante | bloco afirma | janela de 8s | bate |\n|---|---|---|---|\n")
            for mid, app, r, c in rechecks:
                f.write(f"| {hhmm(mid)} | {app[:32]} | {r[:42]} | {'sim' if c else '**NAO**'} |\n")
            f.write(f"\n**{bate}/{len(rechecks)} concordam.** Onde diverge, "
                    "confie na janela de 8s e trate a linha do bloco como suspeita.\n")
        else:
            f.write("\n## Telas\n\nSem frame e sem recheque — **nenhuma afirmacao "
                    "visual foi verificada**. Trate todas como hipotese.\n")
        f.write("\n---\n\n<details><summary>Resposta bruta do modelo</summary>\n\n")
        for t in bruto: f.write(t + "\n\n---\n\n")
        f.write("</details>\n")

    sys.stderr.write(f"\nPRONTO: {rel}\n")
    if tot: sys.stderr.write(f"  citacoes confirmadas: {ok}/{tot} ({ok/tot:.0%})\n")
    sys.stderr.write(f"  frames para conferir: {len(frames)}\n")


if __name__ == "__main__":
    main()
