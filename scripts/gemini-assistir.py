"""Faz o Gemini ASSISTIR um video (visual + audio juntos), sem chunking.

Por que existe: o plugin claude-video-vision fatia o audio em pedacos de 10 min e
manda cada pedaco como AUDIO. Num teste real ele perdeu ~85% do primeiro pedaco e
reportou sucesso. Este script nao fatia nada: manda o video inteiro para a API do
Gemini, que processa frames e trilha juntos.

Uso:
    set GEMINI_API_KEY=...
    python gemini-assistir.py <url-ou-arquivo> "<pergunta>" [inicio] [fim]

    python gemini-assistir.py https://youtu.be/ID "Resuma com timestamps"
    python gemini-assistir.py https://youtu.be/ID "O que aparece na tela?" 0s 600s
    python gemini-assistir.py video.mp4 "Descreva a edicao"

Notas:
  - URL do YouTube vai direto, sem download. So funciona com video PUBLICO.
  - Arquivo local ate 20 MB vai inline; acima disso sobe pela File API.
  - Custo observado: ~5.500 tokens de video por minuto. Um video de 55 min da
    ~300k tokens, dentro do contexto de 1M dos modelos flash.
"""
import base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

API = "https://generativelanguage.googleapis.com/v1beta"
# Ordem de preferencia. 503 e comum em modelo novo — cai para o proximo.
MODELS = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
INLINE_LIMIT = 20 * 1024 * 1024


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
        f"{API}/files?key={key}",
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

    name, uri = info["name"], info["uri"]
    for _ in range(120):  # ate 10 min esperando o processamento
        st = json.loads(urllib.request.urlopen(f"{API}/{name}?key={key}", timeout=60).read())
        if st.get("state") == "ACTIVE":
            return uri, mime
        if st.get("state") == "FAILED":
            sys.exit("Falha no processamento do arquivo pelo Gemini.")
        time.sleep(5)
    sys.exit("Timeout esperando o arquivo ficar ACTIVE.")


def build_part(src, key):
    if src.startswith(("http://", "https://")):
        return {"file_data": {"file_uri": src}}, None
    if not os.path.exists(src):
        sys.exit(f"Arquivo nao encontrado: {src}")
    if os.path.getsize(src) <= INLINE_LIMIT:
        mime = mimetypes.guess_type(src)[0] or "video/mp4"
        with open(src, "rb") as f:
            return {"inline_data": {"mime_type": mime, "data": base64.b64encode(f.read()).decode()}}, None
    uri, mime = upload_file(src, key)
    return {"file_data": {"file_uri": uri, "mime_type": mime}}, uri


def watch(src, prompt, start=None, end=None, max_tokens=32768):
    key = _key()
    media, _ = build_part(src, key)
    if start or end:
        vm = {}
        if start: vm["start_offset"] = start
        if end: vm["end_offset"] = end
        media["video_metadata"] = vm

    payload = {
        "contents": [{"parts": [media, {"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }

    last = None
    for model in MODELS:
        for attempt in (1, 2, 3):
            try:
                t0 = time.time()
                r = _post(f"{API}/models/{model}:generateContent?key={key}", payload)
                cand = r["candidates"][0]
                txt = "".join(
                    p.get("text", "") for p in cand.get("content", {}).get("parts", [])
                )
                usage = r.get("usageMetadata", {})
                sys.stderr.write(
                    f"[{model}] {time.time()-t0:.0f}s | video={usage.get('promptTokensDetails')} "
                    f"total={usage.get('totalTokenCount')} | finish={cand.get('finishReason')}\n"
                )
                if cand.get("finishReason") == "MAX_TOKENS":
                    sys.stderr.write("AVISO: resposta truncada — aumente max_tokens.\n")
                return txt
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode()[:200]}"
                sys.stderr.write(f"[{model}] tentativa {attempt}: {last}\n")
                if e.code not in (429, 500, 503):
                    break          # erro definitivo: proximo modelo nao ajuda
                time.sleep(8 * attempt)
            except Exception as e:
                last = f"{type(e).__name__}: {e}"
                sys.stderr.write(f"[{model}] tentativa {attempt}: {last}\n")
                break
    sys.exit(f"Todos os modelos falharam. Ultimo erro: {last}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    a = sys.argv
    print(watch(a[1], a[2], a[3] if len(a) > 3 else None, a[4] if len(a) > 4 else None))
