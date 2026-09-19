# -*- coding: utf-8 -*-
"""Faz um agente ASSISTIR um video local (baixado, gravado, WhatsApp) com precisao
verificavel. Imagem e som juntos, como um modelo multimodal — e conferido.

Claude nao aceita video como entrada. Quem assiste e o Gemini, que processa os
quadros e a trilha de audio juntos. O que este script acrescenta e a parte que o
Gemini nao faz sozinho: provar o que ele afirmou.

  1. GEMINI      assiste em blocos de 10 min      -> o que aparece e o que e dito
  2. WHISPER     transcreve o audio, sozinho      -> confirma cada citacao e CORRIGE
                                                     o timestamp (fonte independente)
  3. FFMPEG      frame no meio de cada intervalo  -> prova do que estava em quadro

Nenhuma camada depende do modelo acertar tempo. O modelo so olha e descreve.

Uso:
    python assistir-local.py <video> [pasta_saida] [--idioma pt] [--whisper small]
                             [--sem-whisper] [--manter-upload]

Saida:
    <pasta>/relatorio.md       timeline + tabela de verificacao
    <pasta>/frames/*.jpg       prova visual — LEIA cada um com a tool Read
    <pasta>/transcricao.txt    transcricao independente, com timestamp

Precisa de: ffmpeg, ffprobe, python 3.9+, GEMINI_API_KEY no ambiente.
Transcricao: OPENAI_API_KEY no ambiente (Whisper pela API, ~US$0,006/min) OU o pacote
faster-whisper instalado (roda local, gratis, mais lento). Sem nenhum dos dois, as
citacoes saem sem conferencia — e o relatorio avisa.
"""
import io, json, mimetypes, os, re, subprocess, sys, tempfile, time, unicodedata
import urllib.error, urllib.request, uuid

API = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
BLOCO = 600          # 10 min: acima disso o modelo perde precisao temporal
MATCH = 0.60         # fracao de palavras para considerar citacao confirmada
MAX_FRAMES = 24      # frames de prova

# Pedir INTERVALOS, nao "a cada minuto": forcar uma descricao por minuto derrubou
# a precisao visual para ~60% em teste; intervalos levaram a 100%, mesmo custo.
PROMPT = (
    "Assista este trecho com imagem E som. Liste CADA mudanca relevante de quadro "
    "(corte, troca de tela, nova acao, nova pessoa falando) com timestamp MM:SS "
    "ABSOLUTO do video original, no formato 'INICIO - FIM'. Para cada intervalo, "
    "use exatamente estes rotulos:\n"
    "Quadro: o que esta em quadro — pessoas, acao, cenario; se for gravacao de tela, "
    "o nome do aplicativo.\n"
    "Texto na tela: TRANSCREVA o texto legivel (titulos, legendas, rotulos, itens). "
    "Escreva 'nenhum' se nao houver.\n"
    "Fala: uma CITACAO VERBATIM entre aspas do que e dito nesse intervalo.\n"
    "Som: musica, ruido, tom de voz, silencio — so se for relevante.\n"
    "Escreva 'ilegivel' se nao der para ler. NUNCA invente texto, numero ou nome."
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def log(m):
    sys.stderr.write(m + "\n"); sys.stderr.flush()


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def secs(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def hhmm(s):
    s = int(s)
    return f"{s // 60:02d}:{s % 60:02d}"


# ------------------------------------------------------------------ entrada

def sondar(video):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
            "-of", "json", video])
    if r.returncode:
        sys.exit(f"ffprobe nao leu o arquivo: {r.stderr[-300:]}")
    j = json.loads(r.stdout)
    dur = float(j["format"]["duration"])
    audio = any(s.get("codec_type") == "audio" for s in j.get("streams", []))
    return dur, audio


def extrair_audio(video, destino):
    """Mono 16 kHz 32 kbps: pequeno o bastante para a API (~14 MB por hora)."""
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vn", "-ac", "1",
        "-ar", "16000", "-b:a", "32k", destino])
    return destino if os.path.exists(destino) and os.path.getsize(destino) > 0 else None


# ------------------------------------------------------- transcricao independente

def whisper_api(audio, idioma, key):
    """Whisper pela API da OpenAI, com timestamp por palavra."""
    limite = 24 * 1024 * 1024
    pedacos = [(audio, 0.0)]
    if os.path.getsize(audio) > limite:            # fatia em 20 min
        pasta = tempfile.mkdtemp(prefix="wsp-")
        sh(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-f", "segment",
            "-segment_time", "1200", "-c", "copy", os.path.join(pasta, "p%03d.mp3")])
        pedacos = [(os.path.join(pasta, f), i * 1200.0)
                   for i, f in enumerate(sorted(os.listdir(pasta)))]
    palavras, segs = [], []
    for caminho, off in pedacos:
        limite_b = uuid.uuid4().hex
        campos = {"model": "whisper-1", "response_format": "verbose_json",
                  "language": idioma}
        corpo = io.BytesIO()
        for k, v in campos.items():
            corpo.write(f"--{limite_b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
        for g in ("word", "segment"):
            corpo.write(f"--{limite_b}\r\nContent-Disposition: form-data; name=\"timestamp_granularities[]\"\r\n\r\n{g}\r\n".encode())
        corpo.write(f"--{limite_b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode())
        corpo.write(open(caminho, "rb").read())
        corpo.write(f"\r\n--{limite_b}--\r\n".encode())
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/transcriptions", data=corpo.getvalue(),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": f"multipart/form-data; boundary={limite_b}"})
        j = json.loads(urllib.request.urlopen(req, timeout=900).read())
        for w in j.get("words", []):
            palavras.append((w["start"] + off, w["word"]))
        for s in j.get("segments", []):
            segs.append((s["start"] + off, s["text"].strip()))
    return palavras, segs


def whisper_local(audio, idioma, modelo):
    """faster-whisper na CPU. Gratis e privado; ~0,3-1x o tempo real no modelo small."""
    from faster_whisper import WhisperModel
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    it, _ = m.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=True)
    palavras, segs = [], []
    for s in it:
        segs.append((s.start, s.text.strip()))
        for w in (s.words or []):
            palavras.append((w.start, w.word))
    return palavras, segs


def transcrever(video, saida, idioma, modelo, desligado):
    if desligado:
        return [], [], "desligada (--sem-whisper)"
    audio = extrair_audio(video, os.path.join(saida, "audio.mp3"))
    if not audio:
        return [], [], "falhou ao extrair audio"
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    try:
        if key:
            p, s = whisper_api(audio, idioma, key)
            return p, s, "Whisper API (OpenAI)"
    except Exception as e:
        log(f"      Whisper API falhou ({type(e).__name__}); tentando local...")
    try:
        p, s = whisper_local(audio, idioma, modelo)
        return p, s, f"faster-whisper local ({modelo})"
    except ImportError:
        return [], [], "SEM transcritor (instale faster-whisper ou defina OPENAI_API_KEY)"
    except Exception as e:
        return [], [], f"faster-whisper falhou: {type(e).__name__}: {str(e)[:120]}"


# ------------------------------------------------------------------ gemini

def upload(path, key):
    """Sobe uma vez pela File API; os blocos reaproveitam a mesma URI."""
    size = os.path.getsize(path)
    mime = mimetypes.guess_type(path)[0] or "video/mp4"
    start = urllib.request.Request(
        f"{API.replace('/v1beta', '/upload/v1beta')}/files?key={key}",
        data=json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
        headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(size),
                 "X-Goog-Upload-Header-Content-Type": mime,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(start, timeout=120) as r:
        up = r.headers["X-Goog-Upload-URL"]
    with open(path, "rb") as f:
        put = urllib.request.Request(up, data=f.read(), headers={
            "X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"})
        info = json.loads(urllib.request.urlopen(put, timeout=3600).read())["file"]
    for _ in range(180):
        st = json.loads(urllib.request.urlopen(f"{API}/{info['name']}?key={key}",
                                               timeout=60).read())
        if st.get("state") == "ACTIVE":
            return info["uri"], mime, info["name"]
        if st.get("state") == "FAILED":
            sys.exit("O Gemini falhou ao processar o arquivo.")
        time.sleep(5)
    sys.exit("Timeout esperando o arquivo ficar ACTIVE no Gemini.")


def apagar_upload(nome, key):
    try:
        urllib.request.urlopen(urllib.request.Request(
            f"{API}/{nome}?key={key}", method="DELETE"), timeout=60)
        return True
    except Exception:
        return False


def gemini(uri, mime, ini, fim, dur, key, pergunta=None):
    parte = {"file_data": {"file_uri": uri, "mime_type": mime}}
    if not (ini == 0 and fim >= dur):
        parte["video_metadata"] = {"start_offset": f"{int(ini)}s", "end_offset": f"{int(fim)}s"}
    body = {"contents": [{"parts": [parte, {"text": pergunta or PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 16384}}
    for model in MODELS:
        for att in (1, 2, 3):
            try:
                req = urllib.request.Request(
                    f"{API}/models/{model}:generateContent?key={key}",
                    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                r = json.loads(urllib.request.urlopen(req, timeout=1200).read())
                c = r["candidates"][0]
                return "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))
            except urllib.error.HTTPError as e:
                log(f"    [{model}] HTTP {e.code}")
                if e.code not in (429, 500, 503):
                    break
                time.sleep(10 * att)          # 503 e comum em modelo novo e passa
            except Exception as e:
                log(f"    [{model}] {type(e).__name__}")
                break
    return ""


def parse_intervalos(txt):
    heads = list(re.finditer(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]+\s*(\d{1,2}:\d{2}(?::\d{2})?)", txt))
    out = []
    for i, m in enumerate(heads):
        seg = txt[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(txt)]
        q = re.search(r"Quadro[^:\n]{0,20}:\**\s*([^\n]{3,140})", seg)
        # A citacao vem da linha "Fala:". A primeira coisa entre aspas do intervalo
        # costuma ser texto de botao ou titulo na tela — conferir isso contra o
        # audio da 0% e acusa o modelo de inventar uma fala que ele acertou.
        fala = re.search(r"Fala[^:\n]{0,12}:\**\s*([^\n]+)", seg)
        cit = re.findall(r'["“]([^"”\n]{12,600})["”]', fala.group(1)) if fala else []
        try:
            a, b = secs(m.group(1)), secs(m.group(2))
        except ValueError:
            continue
        out.append((a, b, q.group(1).strip(" :*.") if q else "?", cit[0] if cit else None))
    return out


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


# ------------------------------------------------------------------ principal

def main():
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    def opt(nome, padrao):
        return args[args.index(nome) + 1] if nome in args else padrao
    posic = [a for i, a in enumerate(args)
             if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--idioma", "--whisper"))]
    if not posic:
        sys.exit(__doc__)
    video = posic[0]
    saida = posic[1] if len(posic) > 1 else os.path.splitext(os.path.basename(video))[0] + "-analise"
    idioma, modelo = opt("--idioma", "pt"), opt("--whisper", "small")
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("GEMINI_API_KEY nao definida no ambiente.")
    if not os.path.exists(video):
        sys.exit(f"Arquivo nao encontrado: {video}")
    os.makedirs(os.path.join(saida, "frames"), exist_ok=True)

    dur, tem_audio = sondar(video)
    log(f"[1/5] {os.path.basename(video)} ({hhmm(dur)}, {'com' if tem_audio else 'SEM'} audio)")

    log("[2/5] transcricao independente do audio...")
    if tem_audio:
        palavras_raw, segs, fonte = transcrever(video, saida, idioma, modelo, "--sem-whisper" in flags)
    else:
        palavras_raw, segs, fonte = [], [], "video sem trilha de audio"
    palavras = [(t, w) for t, txt in palavras_raw for w in norm(txt).split()]
    with io.open(os.path.join(saida, "transcricao.txt"), "w", encoding="utf-8") as f:
        for t, txt in segs:
            f.write(f"[{hhmm(t)}] {txt}\n")
    log(f"      {fonte}: {len(palavras)} palavras")
    if dur > 60 and palavras:                         # buraco silencioso se denuncia aqui
        faixas = {}
        for t, _ in palavras:
            faixas[int(t // 60)] = faixas.get(int(t // 60), 0) + 1
        vazias = [m for m in range(int(dur // 60)) if faixas.get(m, 0) < 20]
        if vazias:
            log(f"      atencao: minutos com menos de 20 palavras: {vazias[:12]} "
                "(silencio real ou trecho perdido — confira)")

    log("[3/5] enviando o video ao Gemini...")
    uri, mime, nome = upload(video, key)

    blocos = [(i, min(i + BLOCO, dur)) for i in range(0, int(dur) + 1, BLOCO) if i < dur]
    log(f"[4/5] Gemini assiste em {len(blocos)} bloco(s) de ate {BLOCO // 60} min...")
    intervalos, bruto = [], []
    for ini, fim in blocos:
        log(f"    {hhmm(ini)}-{hhmm(fim)}")
        txt = gemini(uri, mime, ini, fim, dur, key)
        bruto.append(txt); intervalos += parse_intervalos(txt)
    # "MM:SS - MM:SS" solto no meio do texto (ex.: horario citado na tela) vira
    # intervalo sem quadro nem fala; e ruido, nao observacao
    intervalos = sorted({(a, b, q, c) for a, b, q, c in intervalos
                         if a <= dur + 2 and not (q == "?" and not c)})
    if "--manter-upload" not in flags:
        apagar_upload(nome, key)

    log("[5/5] conferindo citacoes e extraindo frames...")
    linhas, ok, tot, drift = [], 0, 0, []
    for a, b, q, cit in intervalos:
        if cit and palavras:
            tot += 1
            sc, real = localizar(cit, palavras, a)
            bom = sc >= MATCH; ok += bom
            if bom and real is not None:
                drift.append(abs(real - a))
            linhas.append((a, b, q, cit, bom, sc, real))
        else:
            linhas.append((a, b, q, cit, None, 0, None))

    passo = max(1, len(intervalos) // MAX_FRAMES)
    frames = []
    for i, (a, b, q, _) in enumerate(intervalos[::passo][:MAX_FRAMES], 1):
        mid = (a + b) / 2 if b > a else a
        mid = min(mid, max(dur - 0.5, 0))
        p = os.path.join(saida, "frames", f"f{i:02d}_{hhmm(mid).replace(':', 'm')}.jpg")
        sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{mid:.2f}", "-i", video,
            "-frames:v", "1", "-vf", "scale=640:-2", p])
        if os.path.exists(p):
            frames.append((mid, q, p))

    rel = os.path.join(saida, "relatorio.md")
    with io.open(rel, "w", encoding="utf-8") as f:
        f.write(f"# {os.path.basename(video)}\n\n{hhmm(dur)} — {len(intervalos)} intervalos — "
                f"transcricao: {fonte}\n\n")
        f.write("## Timeline\n\n| inicio | fim | quadro | fala | conferida | tempo REAL |\n")
        f.write("|---|---|---|---|---|---|\n")
        for a, b, q, cit, bom, sc, real in linhas:
            mark = "" if bom is None else ("OK" if bom else "**NAO**")
            c = (cit[:70] + "...") if cit and len(cit) > 70 else (cit or "")
            f.write(f"| {hhmm(a)} | {hhmm(b)} | {q[:48].replace('|', '/')} | "
                    f"{c.replace('|', '/')} | {mark} {f'{sc:.0%}' if bom is not None else ''} | "
                    f"{hhmm(real) if real is not None else ''} |\n")
        if tot:
            f.write(f"\n**{ok}/{tot} citacoes confirmadas pela transcricao independente "
                    f"({ok / tot:.0%}).**")
            if drift:
                import statistics as st
                f.write(f" Erro de timestamp do modelo: media {round(st.mean(drift))}s, "
                        f"pior {round(max(drift))}s.")
            f.write("\n\nDescarte as linhas **NAO** — parafrase apresentada como verbatim.\n"
                    "Use **tempo REAL** como timestamp; a coluna de inicio erra.\n")
        else:
            f.write(f"\n**Nenhuma citacao pode ser conferida** ({fonte}). Trate as falas "
                    "como aproximadas.\n")
        f.write("\n## Frames — prova visual\n\n"
                "O que o modelo diz que esta em quadro e HIPOTESE; o frame e a prova.\n"
                "**LEIA cada arquivo abaixo com a tool Read** e confira contra a coluna 'quadro'.\n\n")
        for mid, q, p in frames:
            f.write(f"- `{p}` — em {hhmm(mid)}, modelo afirma: **{q[:60]}**\n")
        f.write("\n---\n\n<details><summary>Resposta bruta do modelo</summary>\n\n")
        for t in bruto:
            f.write(t + "\n\n---\n\n")
        f.write("</details>\n")

    log(f"\nPRONTO: {rel}")
    if tot:
        log(f"  citacoes confirmadas: {ok}/{tot} ({ok / tot:.0%})")
    log(f"  frames para conferir: {len(frames)}")


if __name__ == "__main__":
    main()
