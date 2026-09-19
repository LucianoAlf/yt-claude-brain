# -*- coding: utf-8 -*-
"""Devolve alfa de verdade a um asset que veio com o xadrez DESENHADO.

O defeito:
    Pedir "fundo transparente" a um gerador de imagem costuma produzir um PNG sem
    canal alfa em que o proprio xadrez de transparencia foi pintado como imagem.
    Quem so olha a miniatura nao percebe, e o asset entra na composicao com um
    tabuleiro cinza em volta.

Por que nao basta tirar os pixels claros:
    O icone tambem tem branco. Apagar "tudo que e claro" fura o meio do desenho.
    Entao a decisao nao e por cor, e por CONEXAO: so vira transparente o claro
    que se liga a borda da imagem. O branco de dentro esta cercado pelo contorno
    preto e sobrevive.

Uso:
    python asset-transparente.py entrada.png saida.png [--margem 24]
"""
import sys

import cv2
import numpy as np

SAT_MAX = 42       # ate aqui e cinza/branco (0-255)
VAL_MIN = 168      # a partir daqui e claro
PENA = 2           # suavizacao da borda, em pixels


def recortar(caminho_in, caminho_out, margem=24):
    img = cv2.imread(caminho_in, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"nao abriu: {caminho_in}")
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    claro = ((hsv[:, :, 1] <= SAT_MAX) & (hsv[:, :, 2] >= VAL_MIN)).astype(np.uint8)

    # componentes conexos do "claro"; os que encostam na borda sao fundo
    n, lab = cv2.connectedComponents(claro, connectivity=8)
    borda = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    borda.discard(0)
    fundo = np.isin(lab, list(borda))

    alpha = np.where(fundo, 0, 255).astype(np.uint8)
    # fecha buracos de 1px do xadrez e suaviza a borda
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    if PENA:
        alpha = cv2.GaussianBlur(alpha, (PENA * 2 + 1,) * 2, 0)

    ys, xs = np.where(alpha > 12)
    if len(xs) == 0:
        raise SystemExit("recorte apagou tudo — revise SAT_MAX/VAL_MIN")
    x0, x1 = max(0, xs.min() - margem), min(w, xs.max() + margem)
    y0, y1 = max(0, ys.min() - margem), min(h, ys.max() + margem)

    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    cv2.imwrite(caminho_out, rgba[y0:y1, x0:x1])

    cob = (alpha > 12).mean()
    sys.stderr.write(f"{caminho_out}: {x1-x0}x{y1-y0}, objeto ocupa "
                     f"{cob*100:.0f}% do quadro original\n")
    return cob


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    m = int(sys.argv[sys.argv.index("--margem") + 1]) if "--margem" in sys.argv else 24
    recortar(sys.argv[1], sys.argv[2], m)
