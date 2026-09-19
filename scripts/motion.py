# -*- coding: utf-8 -*-
"""Entra com assets estaticos e sai com motion design animado sobre o clipe.

A ideia que faz isso valer a pena:
    Gerar VIDEO num modelo generativo e caro e imprevisivel. Gerar IMAGEM e barato
    e estavel. Entao o modelo so entrega a pecas paradas e a animacao — entrada,
    flutuacao, saida — e feita aqui, deterministicamente, ancorada no instante em
    que a PALAVRA correspondente e dita.

    E a ancoragem na fala, nao a animacao em si, que faz parecer editado a mao.

Plano (JSON):
    [{"asset": "moeda.png", "t": 26.9, "dur": 2.6, "x": 0.75, "y": 0.21, "w": 300}]
    t   = segundo do clipe em que o objeto entra
    x,y = centro do objeto em fracao do quadro
    w   = largura em pixels no quadro de saida

Uso:
    python motion.py clipe.mp4 plano_motion.json saida.mp4
"""
import io, json, subprocess, sys

ENTRADA = 0.18      # duracao do fade de entrada
SAIDA = 0.30        # duracao do fade de saida
FPS = 24


def construir(clip, itens, saida):
    ent = ["ffmpeg", "-y", "-loglevel", "error", "-i", clip]
    for it in itens:
        ent += ["-loop", "1", "-framerate", str(FPS), "-t", f"{it['dur']:.2f}",
                "-i", it["asset"]]

    cadeia, atual = [], "[0:v]"
    for i, it in enumerate(itens, start=1):
        t, dur, W = it["t"], it["dur"], it["w"]
        fim_fade = max(dur - SAIDA, ENTRADA)
        # bounce amortecido na entrada: cresce, passa um pouco e assenta
        larg = f"{W}*(1+0.16*exp(-5*t)*sin(13*t))"
        cadeia.append(
            f"[{i}:v]format=rgba,"
            f"scale=w='{larg}':h=-1:eval=frame,"
            f"rotate=a='0.05*sin(2*PI*t/2.6)':c=none:ow=rotw(0.06):oh=roth(0.06),"
            f"fade=t=in:st=0:d={ENTRADA}:alpha=1,"
            f"fade=t=out:st={fim_fade:.2f}:d={SAIDA}:alpha=1,"
            f"setpts=PTS-STARTPTS+{t:.3f}/TB[a{i}]")
        prox = f"[v{i}]"
        cadeia.append(
            f"{atual}[a{i}]overlay=eval=frame:eof_action=pass:"
            f"x='W*{it['x']}-w/2':"
            f"y='H*{it['y']}-h/2+14*sin(2*PI*(t-{t:.3f})/2.4)':"
            f"enable='between(t,{t:.3f},{t + dur:.3f})'{prox}")
        atual = prox

    ent += ["-filter_complex", ";".join(cadeia), "-map", atual, "-map", "0:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "copy",
            "-movflags", "+faststart", saida]
    p = subprocess.run(ent, capture_output=True, text=True)
    if p.returncode:
        sys.stderr.write(p.stderr[-2500:] + "\n")
        raise SystemExit("ffmpeg falhou")


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    itens = json.load(io.open(sys.argv[2], encoding="utf-8"))
    if not itens:
        sys.exit("plano vazio")
    construir(sys.argv[1], itens, sys.argv[3])
    sys.stderr.write(f"PRONTO: {sys.argv[3]} ({len(itens)} elemento(s))\n")


if __name__ == "__main__":
    main()
