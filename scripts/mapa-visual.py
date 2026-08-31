"""Mapa visual de um video com timestamp verificavel por construcao.

O PROBLEMA que isto resolve:
    Perguntar a um modelo "o que aparece na tela em 22:00?" exige que ele seja
    temporalmente preciso sobre milhares de frames. Medido em video real, ele erra
    ~40% das afirmacoes visuais, com deriva de cerca de um minuto.

A INVERSAO:
    1. ffmpeg acha as trocas de tela  -> o timestamp e VERDADE, nao opiniao
    2. extrai o frame naquele instante
    3. o modelo so DESCREVE a imagem  -> nao precisa saber "quando"

    O modelo nunca mais informa timestamp. Ele so olha uma figura e conta o que ve.
    Isso torna o modelo PECA SUBSTITUIVEL: qualquer modelo de visao serve.

Uso:
    set GEMINI_API_KEY=...
    python mapa-visual.py <video.mp4> [inicio_seg] [fim_seg]

    python mapa-visual.py ok720.mp4
    python mapa-visual.py ok720.mp4 1200 1800

Saida: timeline em markdown com timestamp exato + descricao literal de cada tela,
       incluindo o TEXTO legivel de diagramas — que e o conteudo real de tutorial.
"""
import base64, json, os, re, subprocess, sys, tempfile, time
import urllib.error, urllib.request

API = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-flash"]

SCENE_THRESHOLD = 0.25   # sensibilidade do scdet; menor = mais cortes
FLOOR_SECONDS = 45       # piso: garante frame a cada N s mesmo sem corte detectado
MIN_GAP = 12             # nunca dois frames a menos de N s um do outro
BATCH = 8                # imagens por chamada
FRAME_WIDTH = 1024       # largura do frame enviado (precisa ler texto de diagrama)

PROMPT = """Voce recebe {n} frames de um mesmo video, cada um rotulado com seu timestamp.

Para CADA frame, na ordem, escreva:
- **[timestamp]** — qual aplicativo/tela e (nome literal se visivel: Excalidraw, Slack,
  navegador, terminal, WhatsApp, camera do apresentador...)
- O TEXTO LEGIVEL na tela, transcrito literalmente: titulos, rotulos de diagrama,
  itens de lista, nomes de arquivo, abas. Se for um diagrama, descreva as caixas,
  as setas e o que liga o que.
- Se nao conseguir ler algo, escreva "ilegivel". NUNCA invente texto ou numero.

Nao resuma, nao agrupe frames, nao pule nenhum. Um bloco por frame.
Nao mencione timestamps diferentes dos que eu forneci."""


def _key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        sys.exit("GEMINI_API_KEY nao definida.")
    return k


def duration(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", video], capture_output=True, text=True)
    return float(out.stdout.strip())


def scene_times(video, ini, fim):
    """Trocas de tela reais, via filtro scdet do ffmpeg. Esta e a verdade-base."""
    cmd = ["ffmpeg", "-v", "info", "-nostats"]
    if ini: cmd += ["-ss", str(ini)]
    cmd += ["-i", video]
    if fim: cmd += ["-t", str(fim - (ini or 0))]
    cmd += ["-vf", f"scdet=threshold={SCENE_THRESHOLD*100}", "-an", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ts = []
    for m in re.finditer(r"lavfi\.scd\.time:\s*([\d.]+)", r.stderr):
        ts.append(float(m.group(1)) + (ini or 0))
    if not ts:  # fallback: alguns builds usam outro formato
        for m in re.finditer(r"scene_score.*?time:([\d.]+)", r.stderr):
            ts.append(float(m.group(1)) + (ini or 0))
    return ts


def build_timeline(video, ini, fim):
    """Cortes de cena + piso uniforme, deduplicados por MIN_GAP."""
    ini = ini or 0
    fim = fim or duration(video)
    cand = set(scene_times(video, ini, fim))
    t = ini
    while t < fim:                      # piso: diagrama que cresce devagar nao dispara scdet
        cand.add(t); t += FLOOR_SECONDS
    out = []
    for t in sorted(cand):
        if not out or t - out[-1] >= MIN_GAP:
            out.append(round(t, 1))
    return out


def extract(video, times, outdir):
    paths = []
    for t in times:
        p = os.path.join(outdir, f"t{int(t):06d}.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", video,
                        "-frames:v", "1", "-vf", f"scale={FRAME_WIDTH}:-1", "-q:v", "3", p],
                       capture_output=True)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            paths.append((t, p))
    return paths


def fmt(s):
    s = int(s)
    return f"{s//60:02d}:{s%60:02d}"


def describe(batch, key):
    parts = []
    for t, p in batch:
        parts.append({"text": f"--- frame em {fmt(t)} ---"})
        with open(p, "rb") as f:
            parts.append({"inline_data": {"mime_type": "image/jpeg",
                                          "data": base64.b64encode(f.read()).decode()}})
    parts.append({"text": PROMPT.format(n=len(batch))})
    payload = {"contents": [{"parts": parts}],
               "generationConfig": {"maxOutputTokens": 8192}}
    last = None
    for model in MODELS:
        for attempt in (1, 2, 3):
            try:
                req = urllib.request.Request(
                    f"{API}/models/{model}:generateContent?key={key}",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"})
                r = json.loads(urllib.request.urlopen(req, timeout=600).read())
                c = r["candidates"][0]
                return "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}"
                sys.stderr.write(f"  [{model}] tent{attempt}: {last}\n")
                if e.code not in (429, 500, 503): break
                time.sleep(8 * attempt)
            except Exception as e:
                last = f"{type(e).__name__}: {str(e)[:120]}"
                sys.stderr.write(f"  [{model}] tent{attempt}: {last}\n"); break
    return f"_(falha ao descrever este lote: {last})_"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    video = sys.argv[1]
    ini = float(sys.argv[2]) if len(sys.argv) > 2 else None
    fim = float(sys.argv[3]) if len(sys.argv) > 3 else None
    key = _key()

    sys.stderr.write("[1/3] detectando trocas de tela com ffmpeg...\n")
    times = build_timeline(video, ini, fim)
    sys.stderr.write(f"      {len(times)} instantes (cortes de cena + piso de {FLOOR_SECONDS}s)\n")

    tmp = tempfile.mkdtemp(prefix="frames-")
    sys.stderr.write("[2/3] extraindo frames...\n")
    frames = extract(video, times, tmp)
    sys.stderr.write(f"      {len(frames)} frames em {FRAME_WIDTH}px\n")

    sys.stderr.write(f"[3/3] descrevendo em lotes de {BATCH}...\n")
    print(f"# Mapa visual — {os.path.basename(video)}\n")
    print(f"Timestamps vindos do **ffmpeg**, nao do modelo. {len(frames)} instantes.\n")
    for i in range(0, len(frames), BATCH):
        lote = frames[i:i + BATCH]
        sys.stderr.write(f"      lote {i//BATCH+1}/{(len(frames)+BATCH-1)//BATCH} "
                         f"({fmt(lote[0][0])}-{fmt(lote[-1][0])})\n")
        print(describe(lote, key))
        print()


if __name__ == "__main__":
    main()
