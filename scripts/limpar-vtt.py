"""Limpa legendas VTT do YouTube.

Legenda rolante repete cada linha a cada cue e carrega tags inline de karaoke.
Este script remove as duas coisas e agrupa o resultado em blocos com timestamp.

Uso:
    python limpar-vtt.py entrada.vtt saida.txt
"""
import re, sys, io

src, dst = sys.argv[1], sys.argv[2]
raw = io.open(src, encoding="utf-8").read()

TS = re.compile(r"^(\d\d):(\d\d):(\d\d)\.\d+\s+-->")
cues = []
cur_t = None
for line in raw.splitlines():
    m = TS.match(line)
    if m:
        h, mi, s = (int(x) for x in m.groups())
        cur_t = h * 3600 + mi * 60 + s
        continue
    if not line.strip() or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
        continue
    if cur_t is None:
        continue
    txt = re.sub(r"<[^>]*>", "", line)          # tira tags inline de karaoke
    txt = re.sub(r"\s+", " ", txt).strip()
    if txt:
        cues.append((cur_t, txt))

# Legenda rolante repete a linha anterior. Mantém só a primeira ocorrencia.
seen, out = set(), []
for t, txt in cues:
    if txt in seen:
        continue
    seen.add(txt)
    out.append((t, txt))

# Descarta linha contida inteiramente na anterior (re-render parcial).
final = []
for t, txt in out:
    if final and txt in final[-1][1]:
        continue
    final.append((t, txt))

# Agrupa em blocos de ~25s.
blocks, buf, block_t = [], [], None
for t, txt in final:
    if block_t is None:
        block_t = t
    if t - block_t >= 25 and buf:
        blocks.append((block_t, " ".join(buf)))
        buf, block_t = [], t
    buf.append(txt)
if buf:
    blocks.append((block_t, " ".join(buf)))

with io.open(dst, "w", encoding="utf-8") as f:
    for t, txt in blocks:
        f.write("[%02d:%02d] %s\n\n" % (t // 60, t % 60, txt))

words = sum(len(b[1].split()) for b in blocks)
print("cues=%d kept=%d blocks=%d words=%d" % (len(cues), len(final), len(blocks), words))
