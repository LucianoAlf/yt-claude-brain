"""Faz o Gemini ASSISTIR um video (visual + audio juntos), com verificacao automatica.

Por que existe: intermediarios que fatiam o audio antes de entregar ao modelo perdem
conteudo em silencio. Este script nao fatia: manda o video para a API do Gemini, que
processa frames e trilha juntos.

Por que verifica: medido em video real, o Gemini confirma ~87% das citacoes que
apresenta como verbatim — o resto e parafrase. E o timestamp erra ~17s tipico, com
casos de 90s. A verificacao cruza cada citacao contra a legenda original do YouTube:
o que bate vira CONFIRMADO com o timestamp REAL corrigido; o que nao bate vira
NAO CONFIRMADO e deve ser descartado.

Uso:
    set GEMINI_API_KEY=...
    python gemini-assistir.py <url-ou-arquivo> "<pergunta>" [inicio] [fim]

    python gemini-assistir.py https://youtu.be/ID "Resuma com timestamps"
    python gemini-assistir.py https://youtu.be/ID "O que aparece na tela?" 0s 600s
    python gemini-assistir.py video.mp4 "Descreva a edicao" --sem-verificacao

Notas:
  - Verificacao so roda com URL do YouTube que tenha legenda; arquivo local nao tem
    verdade-base para cruzar, e o script avisa.
  - ~5.500 tokens de video por minuto. Video de 55 min = ~300k tokens.
  - Afirmacao VISUAL nao e verificavel por legenda. Para conferir tela num instante,
    extraia o frame:  ffmpeg -ss <segundos> -i video.mp4 -frames:v 1 saida.jpg
"""
import base64, json, mimetypes, os, re, subprocess, sys, tempfile, time
import unicodedata, urllib.error, urllib.request

API = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
INLINE_LIMIT = 20 * 1024 * 1024
MIN_QUOTE_WORDS = 4        # citacao curta demais gera falso positivo
MATCH_THRESHOLD = 0.60     # fracao de palavras da citacao presentes na janela


# ---------------------------------------------------------------- Gemini

def _key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        sys.exit("GEMINI_API_KEY nao definida no ambiente.")
    return k


def _post(url, payload, timeout=1800):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def upload_file(path, key):
    """Sobe arquivo grande pela File API e espera ficar ACTIVE."""
    size = os.path.getsize(path)
    mime = mimetypes.guess_type(path)[0] or "video/mp4"
    start = urllib.request.Request(
        f"{API.replace('/v1beta', '/upload/v1beta')}/files?key={key}",
        data=json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(start, timeout=120) as r:
        up = r.headers["X-Goog-Upload-URL"]
    with open(path, "rb") as f:
        put = urllib.request.Request(
            up, data=f.read(),
            headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"},
        )
        info = json.loads(urllib.request.urlopen(put, timeout=1800).read())["file"]
    for _ in range(120):
        st = json.loads(urllib.request.urlopen(f"{API}/{info['name']}?key={key}", timeout=60).read())
        if st.get("state") == "ACTIVE":
            return info["uri"], mime
        if st.get("state") == "FAILED":
            sys.exit("Gemini falhou ao processar o arquivo.")
        time.sleep(5)
    sys.exit("Timeout esperando o arquivo ficar ACTIVE.")


def build_part(src, key):
    if src.startswith(("http://", "https://")):
        return {"file_data": {"file_uri": src}}
    if not os.path.exists(src):
        sys.exit(f"Arquivo nao encontrado: {src}")
    if os.path.getsize(src) <= INLINE_LIMIT:
        mime = mimetypes.guess_type(src)[0] or "video/mp4"
        with open(src, "rb") as f:
            return {"inline_data": {"mime_type": mime, "data": base64.b64encode(f.read()).decode()}}
    uri, mime = upload_file(src, key)
    return {"file_data": {"file_uri": uri, "mime_type": mime}}


def watch(src, prompt, start=None, end=None, max_tokens=32768):
    key = _key()
    media = build_part(src, key)
    if start or end:
        vm = {}
        if start: vm["start_offset"] = start
        if end: vm["end_offset"] = end
        media["video_metadata"] = vm
    payload = {"contents": [{"parts": [media, {"text": prompt}]}],
               "generationConfig": {"maxOutputTokens": max_tokens}}

    last = None
    for model in MODELS:
        for attempt in (1, 2, 3):
            try:
                t0 = time.time()
                r = _post(f"{API}/models/{model}:generateContent?key={key}", payload)
                cand = r["candidates"][0]
                txt = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
                u = r.get("usageMetadata", {})
                sys.stderr.write(f"[{model}] {time.time()-t0:.0f}s | tokens={u.get('totalTokenCount')} "
                                 f"| finish={cand.get('finishReason')}\n")
                if cand.get("finishReason") == "MAX_TOKENS":
                    sys.stderr.write("AVISO: resposta truncada — aumente max_tokens.\n")
                return txt
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode()[:200]}"
                sys.stderr.write(f"[{model}] tentativa {attempt}: {last}\n")
                if e.code not in (429, 500, 503):
                    break
                time.sleep(8 * attempt)
            except Exception as e:
                last = f"{type(e).__name__}: {e}"
                sys.stderr.write(f"[{model}] tentativa {attempt}: {last}\n")
                break
    sys.exit(f"Todos os modelos falharam. Ultimo erro: {last}")


# ---------------------------------------------------------- Verificacao

def norm(s):
    """Minusculas, sem acento, so alfanumerico — para comparar transcricoes."""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def fetch_captions(url):
    """Baixa a legenda ORIGINAL (nunca a traduzida) e devolve [(segundo, palavra)]."""
    tmp = tempfile.mkdtemp(prefix="legenda-")
    for langs in ("pt-orig,pt", "en-orig,en", ""):
        cmd = ["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
               "--sub-format", "vtt", "-o", os.path.join(tmp, "v.%(ext)s"), url]
        if langs:
            cmd[6:6] = ["--sub-langs", langs]
        try:
            subprocess.run(cmd, capture_output=True, timeout=180)
        except Exception:
            continue
        vtts = [f for f in os.listdir(tmp) if f.endswith(".vtt")]
        if vtts:
            # prefere a faixa "-orig" quando existir
            vtts.sort(key=lambda f: (0 if "orig" in f else 1, f))
            return parse_vtt(os.path.join(tmp, vtts[0])), vtts[0]
    return [], None


def parse_vtt(path):
    """VTT -> [(segundo, palavra)], sem duplicatas de legenda rolante."""
    raw = open(path, encoding="utf-8", errors="replace").read()
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
    seen, out = set(), []
    for t, txt in cues:
        if txt in seen:
            continue
        seen.add(txt); out.append((t, txt))
    words = []
    for t, txt in out:
        for w in norm(txt).split():
            words.append((t, w))
    return words


def extract_quotes(text):
    """Pega trechos entre aspas retas ou curvas, com no minimo MIN_QUOTE_WORDS palavras."""
    quotes = []
    for m in re.finditer(r'["“‘]([^"”’\n]{12,400})["”’]', text):
        q = m.group(1).strip()
        if len(norm(q).split()) >= MIN_QUOTE_WORDS:
            quotes.append(q)
    return quotes


def nearest_claimed_time(text, quote):
    """Ultimo timestamp MM:SS ou HH:MM:SS que aparece antes da citacao."""
    idx = text.find(quote)
    if idx < 0:
        return None
    best = None
    for m in re.finditer(r"\b(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\b", text[:idx]):
        h, mi, s = m.group(1), int(m.group(2)), int(m.group(3))
        best = (int(h) * 3600 if h else 0) + mi * 60 + s
    return best


def locate(quote, words):
    """Melhor janela da legenda para a citacao. Devolve (fracao_casada, segundo)."""
    q = norm(quote).split()
    if not q or not words:
        return 0.0, None
    n = len(q)
    qset = set(q)
    best, best_t = 0.0, None
    stream = [w for _, w in words]
    times = [t for t, _ in words]
    # janela deslizante do tamanho da citacao, passo 1
    for i in range(0, max(1, len(stream) - n + 1)):
        window = stream[i:i + n]
        hit = sum(1 for w in window if w in qset) / n
        if hit > best:
            best, best_t = hit, times[i]
            if best == 1.0:
                break
    return best, best_t


def fmt(sec):
    return "--:--" if sec is None else f"{sec//60:02d}:{sec%60:02d}"


def verify(analysis, url):
    words, fname = fetch_captions(url)
    if not words:
        return ("\n\n---\n### Verificacao\n"
                "Nao foi possivel obter legenda para este video — as citacoes NAO foram\n"
                "verificadas. Trate todas como nao confirmadas.\n")
    quotes = extract_quotes(analysis)
    if not quotes:
        return ("\n\n---\n### Verificacao\n"
                "Nenhuma citacao entre aspas foi encontrada na resposta. Peca ao modelo\n"
                "CITACAO VERBATIM entre aspas para que a verificacao funcione.\n")

    rows, ok, drift = [], 0, []
    for q in quotes:
        score, real = locate(q, words)
        claimed = nearest_claimed_time(analysis, q)
        good = score >= MATCH_THRESHOLD
        ok += good
        if good and claimed is not None and real is not None:
            drift.append(abs(real - claimed))
        rows.append((good, score, fmt(claimed), fmt(real),
                     (q[:58] + "...") if len(q) > 58 else q))

    out = ["\n\n---", "### Verificacao automatica contra a legenda original",
           f"Fonte da verdade: `{fname}` ({len(words)} palavras)", "",
           "| ? | casou | alegado | REAL | citacao |", "|---|---|---|---|---|"]
    for good, sc, c, r, q in rows:
        out.append(f"| {'OK' if good else 'NAO'} | {sc:.0%} | {c} | **{r}** | {q} |")
    out.append("")
    out.append(f"**{ok}/{len(rows)} citacoes confirmadas** ({ok/len(rows):.0%}).")
    if drift:
        import statistics as st
        out.append(f"Erro de timestamp: media {round(st.mean(drift))}s, "
                   f"mediana {round(st.median(drift))}s, pior {max(drift)}s.")
    if ok < len(rows):
        out.append("\n**Descarte as linhas NAO** — sao parafrase apresentada como verbatim.")
    out.append("Use a coluna **REAL** como timestamp; a coluna alegada erra.")
    out.append("\nAfirmacao VISUAL nao e verificavel por legenda. Para conferir a tela em T:")
    out.append("`ffmpeg -ss <T> -i video.mp4 -frames:v 1 saida.jpg`")
    return "\n".join(out)


# ---------------------------------------------------------------- CLI

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--sem-verificacao"]
    do_verify = "--sem-verificacao" not in sys.argv
    if len(args) < 2:
        sys.exit(__doc__)
    src, prompt = args[0], args[1]
    start = args[2] if len(args) > 2 else None
    end = args[3] if len(args) > 3 else None

    result = watch(src, prompt, start, end)
    print(result)

    if do_verify:
        if src.startswith(("http://", "https://")) and "yout" in src:
            sys.stderr.write("[verificacao] baixando legenda original...\n")
            print(verify(result, src))
        else:
            print("\n\n---\n### Verificacao\nPulada: so roda com URL do YouTube "
                  "(arquivo local nao tem legenda para servir de verdade-base).")
