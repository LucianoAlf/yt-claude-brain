---
name: assistir-video-youtube
description: Use when the user shares a YouTube URL or local video and wants its content analyzed, summarized, transcribed, or its on-screen material extracted — tutorials, aulas, palestras, screencasts, demos. Also use when a video analysis returned a transcript in the wrong language, timestamps that do not match the footage, or screen descriptions that cannot be trusted.
---

# Assistir vídeo do YouTube com precisão verificável

## Overview

Claude não aceita vídeo como entrada. Toda solução é percepção externa. O erro comum
não é falhar — é **falhar em silêncio**: devolver JSON bem-formado, com timestamps,
faltando 8 minutos de conteúdo, ou nomeando uma tela que não está lá.

**Princípio central: nenhuma camada pode depender do modelo acertar tempo.**

| Camada | Fonte da verdade | Responde |
|---|---|---|
| Gemini em blocos, direto da URL | — | o que aparece na tela, o que é dito |
| Legenda `pt-orig` do próprio vídeo | verificável | confirma citação, **corrige o timestamp** |
| Frame via `ffmpeg` | prova por construção | o que estava na tela naquele instante |

## Quick Reference

```bash
python scripts/assistir-youtube.py "https://youtu.be/ID" pasta-saida
```

Gera `pasta-saida/relatorio.md` (timeline + tabela de verificação), `frames/*.jpg`
e `transcricao.txt`. **Leia cada frame com a tool Read** e confira contra a coluna "tela".

Pré-requisitos: `yt-dlp`, `ffmpeg`, `ffprobe`, e `GEMINI_API_KEY` no **ambiente**
(chave gratuita em ai.google.dev — camada gratuita cobre uso normal).

```bash
pip install --user --upgrade yt-dlp
winget install --id Gyan.FFmpeg --exact --silent --accept-package-agreements
```

No Windows: use `python`, nunca `python3` (é o stub da Microsoft Store).
`pip install --user` instala fora do PATH — adicione `%APPDATA%\Roaming\Python\Python3XX\Scripts`.

## Como ler o relatório

- Coluna **conferida** `NAO` → paráfrase apresentada como verbatim. **Descarte a citação.**
- Coluna **tempo REAL** → use este timestamp. O início do intervalo erra ~15 s.
- Seção **Frames** → afirmação de tela é hipótese; o frame é a prova. Leia e confira.
- Se o relatório disser "sem prova visual", **nenhuma afirmação de tela foi verificada**.

## Precisão medida

Dois vídeos, 74 min no total, conferidos contra legenda e frames:

| | Citações | Visual |
|---|---|---|
| Vídeo denso de diagramas (55 min) | 87% | 93% |
| Vídeo com slides limpos (18 min) | **100%** | **100%** |

Custo: ~2 min e 2–6 chamadas por vídeo. Tela de alto contraste (slide, Finder, Slack)
acerta mais que diagrama escuro denso.

## Common Mistakes

**Aceitar a legenda que o yt-dlp escolhe sozinho.** Em vídeo em português ele costuma
pegar a **tradução automática para inglês**, que corrompe termos: "Claude" vira "cloud",
"/watch" vira "barrawat". O Whisper não salva — ele só entra quando não há legenda
nenhuma, então uma legenda ruim mas presente ganha calada. Force `--sub-langs pt-orig`.

**Pedir descrição "a cada 1 minuto".** Isso força uma tela por minuto, mas o vídeo troca
várias vezes no mesmo minuto — precisão visual cai para ~60%. **Peça INTERVALOS**
(`INÍCIO - FIM`). Foi a única mudança que levou 60% → 100%.

**Mandar o vídeo inteiro numa chamada.** Em 55 min são 3.300 frames; o modelo inventa
detalhe (afirmou um painel com "88%" que não existia) e as fronteiras derrapam minutos.
**Blocos de 10 minutos.**

**Fatiar o áudio e mandar sem o vídeo.** É o que o plugin `claude-video-vision` faz, e
num teste real ele perdeu **~85% do primeiro pedaço reportando sucesso**. Detecte pela
densidade de palavras **por faixa**, nunca pelo total: o total parece plausível e esconde
o buraco.

**Aceitar número que o modelo oferece.** Ele afirmou 150–165 palavras/minuto onde o
medido era 216 — erro de 30%. Aceite o que ele *observa*; **recalcule todo número.**

**Confiar no rótulo `t=MM:SS` do relatório de cena da skill `/watch`.** Conferido contra
ffmpeg, não corresponde ao conteúdo do frame. Para saber *quando*, use
`ffmpeg -ss <segundos> -i video.mp4 -frames:v 1 saida.jpg`.

**Desistir no primeiro erro de download.** `403 Forbidden` e `429` são intermitentes e
mudam de hora em hora na mesma máquina. Repita antes de complicar. Se persistir, tente
`yt-dlp --remote-components ejs:github` — destravou download que falhou 5 vezes seguidas.

## Quando o download falha de vez

Acontece: formatos acima de 144p ficam bloqueados, e às vezes todos. O script cai para
recheque por janela de 8 s — o modelo não tem para onde derrapar num intervalo tão curto.

**Isso é mais fraco que o frame**: mesmo modelo, logo não é prova independente. Serve
para pegar discordância, não para confirmar. Quando diverge, confie na janela curta.

Se o vídeo for de datacenter/VPS, o anti-bot é persistente — é **reputação de IP**, não
configuração. Trocar `player_client` não resolve. Priorize a rota de navegador logado, ou
baixe numa máquina residencial e passe o arquivo.

## Vídeo local

O script é para URL do YouTube. Para arquivo local, a skill `/watch` aceita caminho
direto e o Whisper transcreve automaticamente (~US$ 0,006/min). Vale mais nesse caso:
sem legenda para cruzar, a verificação de citação não existe — mas o áudio é limpo e a
transcrição sai fiel.

Para o Gemini assistir arquivo local, use `scripts/gemini-assistir.py`, que sobe pela
File API quando passa de 20 MB.

## O que nenhuma dessas ferramentas faz

**Análise de áudio propriamente dita.** Entonação, altura de voz, ritmo, ênfase e pausa
não são medidos por `/watch`. O Gemini *comenta* essas coisas, mas erra número. Se
alguém pedir análise de prosódia, diga que é observação qualitativa, não medida.
