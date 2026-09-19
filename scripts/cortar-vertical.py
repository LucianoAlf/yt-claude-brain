# -*- coding: utf-8 -*-
"""Corta um trecho de video 16:9 e entrega um clipe 9:16 com locutor enquadrado
e legenda acesa palavra a palavra.

O problema que isto resolve:
    Recorte 9:16 fixo no centro corta o rosto quando a pessoa se move, e destroi
    qualquer trecho que seja gravacao de tela. Sao duas situacoes com solucoes
    opostas, e a maioria dos videos alterna entre as duas a cada poucos segundos.

Como resolve:
    1. detecta rosto a cada 0,5 s dentro do trecho
    2. quebra o trecho em faixas ROSTO e TELA
    3. ROSTO -> recorte 9:16 que segue o rosto suavizado
       TELA  -> quadro inteiro sobre fundo desfocado do proprio video
    4. concatena, devolve o audio original e queima a legenda

A legenda usa o timing por palavra da decupagem: cada palavra acende no instante
exato em que e dita. E isso, nao a fonte, que faz o clipe parecer editado a mao.

Uso:
    python cortar-vertical.py src.mp4 decup.json ini fim saida.mp4 [--sem-legenda]
"""
import json, io, os, subprocess, sys, tempfile

import cv2

W_OUT, H_OUT = 1080, 1920
FONTE = "Arial Black"
COR_ATIVA = "&H0022E1FF"     # ABGR: amarelo quente
PASSO = 0.5                  # amostragem de rosto
MIN_FAIXA = 1.5              # faixa menor que isso e absorvida pela vizinha
PALAVRAS_LINHA = 3

# Selo promocional que o video de origem queima por cima da imagem em rajadas
# curtas. Em fracao do quadro da FONTE (x, y, largura, altura).
SELO = (0.310, 0.655, 0.420, 0.330)
SELO_HSV = ((35, 120, 140), (75, 255, 255))   # borda verde-limao
SELO_LIMIAR = 0.010


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.stderr.write(p.stderr[-1800:] + "\n")
        raise SystemExit(f"ffmpeg falhou: {' '.join(cmd[:6])}...")


def detectar(video, ini, fim):
    """[(t, cx ou None)] a cada PASSO segundos."""
    casc = cv2.CascadeClassifier(cv2.data.haarcascades +
                                 "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(video)
    H = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    Wd = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    out, t = [], ini
    while t < fim:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        cx = None
        if ok:
            g = cv2.equalizeHist(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
            fa = casc.detectMultiScale(g, 1.12, 6, minSize=(int(H * .05),) * 2)
            if len(fa):
                x, y, w, h = max(fa, key=lambda z: z[2] * z[3])
                if h / H >= 0.20:                      # rosto grande = camera
                    cx = (x + w / 2) / Wd
        out.append((round(t - ini, 2), cx))
        t += PASSO
    cap.release()
    return out, int(Wd), int(H)


def janelas_selo(video, ini, fim, passo=0.25):
    """Quando o selo promocional da origem esta em quadro, em tempo relativo."""
    import numpy as np
    cap = cv2.VideoCapture(video)
    marc, t = [], ini
    while t < fim:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if ok:
            h, w = f.shape[:2]
            x, y, lw, lh = SELO
            r = f[int(y * h):int((y + lh) * h), int(x * w):int((x + lw) * w)]
            m = cv2.inRange(cv2.cvtColor(r, cv2.COLOR_BGR2HSV), *SELO_HSV)
            if m.mean() / 255 > SELO_LIMIAR:
                marc.append(t - ini)
        t += passo
    cap.release()
    jan = []
    for t in marc:                       # agrupa e alarga meio segundo de folga
        if jan and t - jan[-1][1] <= 1.0:
            jan[-1][1] = t
        else:
            jan.append([t, t])
    return [(max(0, a - 0.5), b + 0.7) for a, b in jan]


def limpar_selo(jan, a, b, Wd, Hd):
    """Grafo que desfoca so o retangulo do selo, so enquanto ele esta em quadro.

    boxblur atua no quadro inteiro, entao a regiao e recortada, desfocada e
    devolvida por cima — com recorte temporal no overlay.
    """
    loc = [(max(x, a) - a, min(y, b) - a) for x, y in jan if y > a and x < b]
    if not loc:
        return "", ""
    # Ligar e desligar o tratamento no meio do corte cria um piscar visivel: a
    # faixa tratada aparece e some. Se o selo entra em algum momento, o
    # tratamento vale o corte inteiro. Fica constante, e constante nao chama
    # atencao. O degrade de base cobre o resto.
    sx, sy, sw, sh = SELO
    X, Y = int(sx * Wd), int(sy * Hd)
    CW, CH = int(sw * Wd) // 2 * 2, int(sh * Hd) // 2 * 2
    grafo = (f"split=2[sb][sr];"
             f"[sr]crop={CW}:{CH}:{X}:{Y},boxblur=luma_radius=44:luma_power=3,"
             f"eq=brightness=-0.08:saturation=0.5[sx];"
             f"[sb][sx]overlay={X}:{Y}")
    return grafo, "sempre"


def faixas(amostras, dur):
    """Agrupa em ('rosto'|'tela', ini, fim) e absorve faixas curtas."""
    br = []
    for t, cx in amostras:
        m = "rosto" if cx is not None else "tela"
        if br and br[-1][0] == m:
            br[-1][2] = t + PASSO
        else:
            br.append([m, t, t + PASSO])
    # absorve faixas curtas na vizinha
    mudou = True
    while mudou and len(br) > 1:
        mudou = False
        for i, f in enumerate(br):
            if f[2] - f[1] < MIN_FAIXA:
                viz = br[i - 1] if i else br[1]
                viz[1] = min(viz[1], f[1]); viz[2] = max(viz[2], f[2])
                br.pop(i); mudou = True; break
    # a absorcao acima pode deixar duas faixas vizinhas do mesmo modo; funde
    j = 0
    while j + 1 < len(br):
        if br[j][0] == br[j + 1][0]:
            br[j][2] = br[j + 1][2]; br.pop(j + 1)
        else:
            j += 1
    br[0][1] = 0.0
    br[-1][2] = dur
    for i in range(len(br) - 1):
        br[i + 1][1] = br[i][2]
    return [(m, a, b) for m, a, b in br if b - a > 0.04]


def expr_crop(amostras, a, b, Wd, larg):
    """Expressao de x do crop: segue o rosto, suavizado, com pontos esparsos."""
    pts = [(t, cx) for t, cx in amostras if a - PASSO <= t <= b + PASSO and cx is not None]
    if not pts:
        return str(int((Wd - larg) / 2))
    # media movel de 5
    sua = []
    for i, (t, _) in enumerate(pts):
        jan = [c for _, c in pts[max(0, i - 2):i + 3]]
        sua.append((t - a, sum(jan) / len(jan)))
    # reduz pontos: so guarda mudanca > 1% da largura
    keep = [sua[0]]
    for t, c in sua[1:]:
        if abs(c - keep[-1][1]) > 0.01 and t - keep[-1][0] > 0.8:
            keep.append((t, c))
    keep.append((b - a, sua[-1][1]))
    def px(c):
        return max(0, min(Wd - larg, int(c * Wd - larg / 2)))
    if len(keep) == 1:
        return str(px(keep[0][1]))
    e = str(px(keep[-1][1]))
    for i in range(len(keep) - 2, -1, -1):
        t0, c0 = keep[i]; t1, c1 = keep[i + 1]
        x0, x1 = px(c0), px(c1)
        span = max(t1 - t0, 0.01)
        e = (f"if(lt(t,{t1:.2f}),{x0}+({x1 - x0})*(t-{t0:.2f})/{span:.2f},{e})")
    return e


# A legenda automatica do YouTube erra nome proprio com teimosia, e legenda
# queimada publica o erro. Corrigir aqui e obrigatorio, nao cosmetico.
CORRECOES = {
    "cloud": "Claude", "clould": "Claude", "claudio": "Claude", "cláudio": "Claude",
    "hixfield": "Higgsfield", "hickfield": "Higgsfield", "higsfield": "Higgsfield",
    "rigsfield": "Higgsfield", "heckfield": "Higgsfield", "hitsfield": "Higgsfield",
    "jzon": "JSON", "json": "JSON", "assete": "asset", "assetes": "assets",
    "esquora": "skill", "hul": "hook", "thales": "Tallis", "tales": "Tallis",
}
PONT = ".,!?;:—-\"'()“”…"


def corrigir(tok):
    """Troca o termo errado preservando pontuacao e caixa da vizinhanca."""
    nucleo = tok.strip(PONT)
    if not nucleo:
        return tok
    novo = CORRECOES.get(nucleo.lower())
    if not novo:
        return tok
    i = tok.find(nucleo)
    return tok[:i] + novo + tok[i + len(nucleo):]


def gerar_scrim(path):
    """Degrade escuro no rodape: da contraste para a legenda sem tapar a imagem."""
    from PIL import Image
    img = Image.new("RGBA", (W_OUT, H_OUT), (0, 0, 0, 0))
    px = img.load()
    topo, base = int(H_OUT * 0.58), H_OUT
    for y in range(topo, base):
        k = (y - topo) / (base - topo)
        a = int(200 * (k ** 1.6))
        for x in range(W_OUT):
            px[x, y] = (0, 0, 0, a)
    img.save(path)


def ass(palavras, ini, fim, path):
    """Legenda com o timing real de cada palavra."""
    ws = [w for w in palavras if ini - 0.05 <= w["t"] < fim]
    for w in ws:
        w["r"] = w["t"] - ini
    grupos = [ws[i:i + PALAVRAS_LINHA] for i in range(0, len(ws), PALAVRAS_LINHA)]

    def tc(s):
        s = max(s, 0)
        h = int(s // 3600); m = int(s % 3600 // 60)
        return f"{h}:{m:02d}:{s % 60:05.2f}"

    L = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W_OUT}", f"PlayResY: {H_OUT}",
         "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
         "[V4+ Styles]",
         "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
         "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
         "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
         f"Style: B,{FONTE},92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,"
         "-1,0,0,0,100,100,1,0,1,7,4,2,70,70,650,1", "",
         "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]

    # o fim de um grupo e o inicio do proximo: dois grupos no ar ao mesmo tempo
    # fazem o libass empilhar as linhas e a legenda sai fora de ordem.
    for gi, g in enumerate(grupos):
        if gi + 1 < len(grupos):
            gfim = grupos[gi + 1][0]["r"]
        else:
            gfim = g[-1]["r"] + g[-1]["d"] + 0.15
        for i, w in enumerate(g):
            ini_e = w["r"]
            fim_e = g[i + 1]["r"] if i + 1 < len(g) else gfim
            partes = []
            for j, x in enumerate(g):
                t = corrigir(x["w"]).upper().replace("{", "").replace("}", "")
                partes.append(f"{{\\c{COR_ATIVA}\\fscx112\\fscy112}}{t}{{\\r}}"
                              if j == i else t)
            txt = " ".join(partes)
            efeito = "{\\fad(60,0)}" if i == 0 else ""
            L.append(f"Dialogue: 0,{tc(ini_e)},{tc(fim_e)},B,,0,0,0,,{efeito}{txt}")
    io.open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return len(ws)


def main():
    if len(sys.argv) < 6:
        sys.exit(__doc__)
    src, decup, ini, fim, saida = (sys.argv[1], sys.argv[2], float(sys.argv[3]),
                                   float(sys.argv[4]), sys.argv[5])
    legenda = "--sem-legenda" not in sys.argv
    dur = fim - ini
    tmp = tempfile.mkdtemp(prefix="corte-")

    sys.stderr.write(f"[1/4] rastreando rosto em {dur:.1f}s...\n")
    amostras, Wd, Hd = detectar(src, ini, fim)
    larg = int(Hd * 9 / 16) // 2 * 2
    fx = faixas(amostras, dur)
    sys.stderr.write("      " + "  ".join(f"{m}:{a:.1f}-{b:.1f}" for m, a, b in fx) + "\n")
    selo = janelas_selo(src, ini, fim)
    if selo:
        sys.stderr.write("      selo da origem em " +
                         ", ".join(f"{a:.1f}-{b:.1f}s" for a, b in selo) + " (desfocado)\n")

    sys.stderr.write(f"[2/4] compondo {len(fx)} faixa(s) em {W_OUT}x{H_OUT}...\n")
    pedacos = []
    for i, (modo, a, b) in enumerate(fx):
        p = os.path.join(tmp, f"p{i:02d}.mp4")
        pre, _ = limpar_selo(selo, a, b, Wd, Hd)
        pre = pre + "," if pre else ""
        if modo == "rosto":
            vf = (pre + f"crop={larg}:{Hd}:'{expr_crop(amostras, a, b, Wd, larg)}':0,"
                  f"scale={W_OUT}:{H_OUT}:flags=lanczos,setsar=1")
        else:
            vf = (pre + f"split=2[bg][fg];"
                  f"[bg]scale=-2:{H_OUT},crop={W_OUT}:{H_OUT},"
                  f"boxblur=luma_radius=42:luma_power=2,eq=brightness=-0.14[b];"
                  f"[fg]scale={W_OUT}:-2,setsar=1[f];"
                  f"[b][f]overlay=(W-w)/2:(H-h)/2")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{ini + a:.3f}",
             "-t", f"{b - a:.3f}", "-i", src, "-an", "-filter_complex", vf,
             "-r", "24", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-pix_fmt", "yuv420p", p])
        pedacos.append(p)

    lista = os.path.join(tmp, "lista.txt")
    io.open(lista, "w", encoding="utf-8").write(
        "".join(f"file '{p.replace(os.sep, '/')}'\n" for p in pedacos))
    mudo = os.path.join(tmp, "mudo.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lista, "-c", "copy", mudo])

    sys.stderr.write("[3/4] degrade de base e legenda palavra a palavra...\n")
    scrim = os.path.join(tmp, "scrim.png")
    gerar_scrim(scrim)
    cadeia = "[0:v][2:v]overlay=0:0[v]"
    if legenda:
        pal = json.load(io.open(decup, encoding="utf-8"))["palavras"]
        assp = os.path.join(tmp, "leg.ass")
        n = ass(pal, ini, fim, assp)
        sys.stderr.write(f"      {n} palavras\n")
        esc = assp.replace("\\", "/").replace(":", "\\:")
        cadeia += f";[v]subtitles='{esc}'[v2]"
        alvo = "[v2]"
    else:
        alvo = "[v]"

    sys.stderr.write("[4/4] audio original e render final...\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", mudo,
         "-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", src, "-i", scrim,
         "-filter_complex", cadeia, "-map", alvo, "-map", "1:a:0",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", saida])
    sys.stderr.write(f"PRONTO: {saida}\n")


if __name__ == "__main__":
    main()
