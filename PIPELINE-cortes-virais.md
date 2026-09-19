# Pipeline de cortes virais — implementação própria

Reprodução executável do método do vídeo "Como Editar um Reel Viral 100% no Claude Code"
(ver [GUIA-cortes-virais-claude-code.md](GUIA-cortes-virais-claude-code.md)), sem depender
das skills fechadas dele.

Testado ponta a ponta em 03/09/2026 sobre o próprio vídeo do LABS (23:08): três cortes
verticais 1080×1920 entregues.

## Etapas e scripts

| Etapa | Script | O que faz |
|---|---|---|
| 1. Decupagem | [`scripts/decupagem.py`](scripts/decupagem.py) | legenda `pt-orig` → JSON com timing **por palavra** |
| 2. Enquadramento | [`scripts/cortar-vertical.py`](scripts/cortar-vertical.py) | rastreia rosto, corta 9:16, queima legenda |
| 3. Asset | [`scripts/asset-transparente.py`](scripts/asset-transparente.py) | devolve canal alfa a asset gerado sem transparência |
| 4. Motion | [`scripts/motion.py`](scripts/motion.py) | anima os assets ancorados na palavra falada |

```bash
python scripts/decupagem.py legenda.pt-orig.vtt decup.json
python scripts/cortar-vertical.py src.mp4 decup.json 584.88 614.64 corte.mp4
python scripts/asset-transparente.py bruto.png asset.png
python scripts/motion.py corte.mp4 plano_motion.json final.mp4
```

Dependências: `ffmpeg`, `opencv-python-headless==4.11`, `numpy`, `Pillow`.

## As decisões que fizeram diferença

**A legenda automática do YouTube tem timing por palavra.** Fica escondido em tags `<c>`
dentro de cues rolantes que repetem cada linha duas ou três vezes. Quem lê o VTT cru acha
que só existe timing por linha. São 4.958 palavras cronometradas individualmente neste
vídeo — é isso que permite acender a legenda no instante exato e ancorar o motion na fala.

**Um vídeo alterna entre duas situações que pedem soluções opostas.** Câmera cheia pede
recorte 9:16 seguindo o rosto; gravação de tela pede o quadro inteiro sobre fundo
desfocado. Recorte fixo destrói uma das duas. O script detecta rosto a cada 0,5 s, quebra
o trecho em faixas e compõe cada uma do seu jeito.

**Gerar imagem é barato, gerar vídeo é caro.** Cinco assets no Higgsfield custaram
**10 créditos** (2 por imagem, `nano_banana_pro`). A animação — entrada com bounce
amortecido, flutuação, saída — é feita em ffmpeg, de graça e de forma determinística.
É a mesma inversão que ele ensina, e é o que mantém o custo no chão.

**Fechar as bordas no silêncio entre palavras.** O corte busca a maior pausa dentro de
±2,5 s do alvo. Sem isso o clipe começa no meio de uma sílaba.

## Três armadilhas que só aparecem quando você renderiza

**Legenda queimada publica o erro de transcrição.** O primeiro render saiu com
**"E O CLOUD"** em letra garrafal — a legenda automática troca "Claude" por "cloud" com
teimosia. Existe uma tabela de correção em `cortar-vertical.py` (`CORRECOES`); ela não é
cosmética, é obrigatória. Amplie a tabela para os termos do seu nicho antes de publicar.

**Dois grupos de legenda no ar ao mesmo tempo empilham as linhas.** Se o fim de um grupo
passar do começo do próximo, o libass empilha e o texto sai fora de ordem. O fim de cada
grupo tem que ser exatamente o início do seguinte.

**"Fundo transparente" costuma vir como xadrez pintado.** O modelo entrega um PNG sem
canal alfa em que o tabuleiro de transparência foi **desenhado como imagem**. É o defeito
que ele mostra no vídeo. Apagar "tudo que é claro" fura os brancos internos do ícone; a
decisão certa é por **conexão** — só vira transparente o claro que se liga à borda da
imagem. O branco de dentro está cercado pelo contorno preto e sobrevive.

## Limitação conhecida

O vídeo de origem queima um selo promocional próprio no rodapé, em rajadas curtas (2% da
duração). Uma delas cai dentro do corte `c02`. O script detecta e desfoca a região, mas
como o selo é escuro, o resultado é uma faixa escura constante na base desse clipe. Fica
consistente — não pisca —, porém é visível. Em material sem selo queimado (`c01` e `c03`)
o problema não existe.

## Custo medido

| Item | Custo |
|---|---|
| 5 assets no Higgsfield | 10 créditos |
| Legenda, corte, enquadramento, motion | R$ 0 (ffmpeg + OpenCV local) |
| Download e decupagem | R$ 0 (yt-dlp + legenda do próprio vídeo) |

Um asset falhou na primeira tentativa (moeda) e foi refeito com outro texto. Uma geração
foi feita por engano no conector Pixa/Pixelcut em vez do Higgsfield e custou 18 créditos
lá — voltou em JPG, sem alfa. Confira em qual conector está gerando antes de disparar.
