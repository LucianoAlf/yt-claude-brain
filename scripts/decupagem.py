# -*- coding: utf-8 -*-
"""Legenda automatica do YouTube -> decupagem com timing por PALAVRA.

Por que isto existe:
    A legenda automatica do YouTube carrega timing por palavra em tags <c>, mas
    entrega tudo em cues rolantes que repetem cada linha duas ou tres vezes. Quem
    le o VTT cru acha que so tem timing por linha (~2 s) e perde a informacao mais
    valiosa que existe para cortar video: o instante exato de CADA palavra.

    Com timing por palavra da para (a) cortar no silencio entre duas palavras em
    vez de no meio de uma, e (b) acender a legenda palavra a palavra, que e o que
    faz um Reels parecer editado a mao.

Uso:
    python decupagem.py legenda.vtt saida.json

Saida: {"palavras": [{"t": 12.34, "d": 0.28, "w": "token"}, ...]}
"""
import io, json, re, sys

TAG = re.compile(r"<(\d\d):(\d\d):(\d\d[.,]\d\d\d)>")
CUE = re.compile(r"^(\d\d:\d\d:\d\d[.,]\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d[.,]\d\d\d)")


def seg(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))


def cue_seg(ts):
    h, m, s = ts.split(":")
    return seg(h, m, s)


def parse(path):
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    palavras = []          # (t, w)
    ini_cue = None
    for linha in txt.splitlines():
        m = CUE.match(linha.strip())
        if m:
            ini_cue = cue_seg(m.group(1))
            continue
        if not linha.strip() or "-->" in linha or linha.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if "<c>" not in linha and "<" not in linha:
            continue          # linha de eco, sem timing: ignorada
        # a primeira palavra da linha herda o inicio do cue
        cabeca = TAG.split(linha)[0]
        cabeca = re.sub(r"</?c[^>]*>", "", cabeca).strip()
        if cabeca and ini_cue is not None:
            for w in cabeca.split():
                palavras.append((ini_cue, w))
        # demais palavras trazem o proprio timestamp
        for m in re.finditer(r"<(\d\d):(\d\d):(\d\d[.,]\d\d\d)><c>(.*?)</c>", linha):
            t = seg(m.group(1), m.group(2), m.group(3))
            w = re.sub(r"<[^>]*>", "", m.group(4)).strip()
            if w:
                palavras.append((t, w))

    # o VTT rolante repete cada palavra; deduplica por (tempo arredondado, palavra)
    vistos, limpo = set(), []
    for t, w in sorted(palavras, key=lambda p: p[0]):
        chave = (round(t, 2), w)
        if chave in vistos:
            continue
        vistos.add(chave)
        limpo.append((t, w))

    # duracao = ate a proxima palavra, com teto para nao arrastar em pausa longa
    saida = []
    for i, (t, w) in enumerate(limpo):
        prox = limpo[i + 1][0] if i + 1 < len(limpo) else t + 0.4
        saida.append({"t": round(t, 3), "d": round(min(max(prox - t, 0.08), 1.2), 3), "w": w})
    return saida


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    palavras = parse(sys.argv[1])
    with io.open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump({"palavras": palavras}, f, ensure_ascii=False)
    dur = palavras[-1]["t"] if palavras else 0
    sys.stderr.write(f"{len(palavras)} palavras, ate {int(dur)//60:02d}:{int(dur)%60:02d}\n")
    sys.stderr.write(f"densidade: {len(palavras)/(dur/60):.0f} palavras/min\n")


if __name__ == "__main__":
    main()
