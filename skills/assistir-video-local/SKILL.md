---
name: assistir-video-local
description: Use when the user shares or points to a video FILE on disk (.mp4, .mov, .mkv, .webm, .avi — WhatsApp videos, screen recordings, downloaded clips, meeting recordings) and wants it watched, described, transcribed, summarized, or its on-screen content extracted. Also use when frame screenshots alone missed what was said, or a transcript alone missed what was shown.
---

# Assistir vídeo local — imagem e som juntos, com prova

## Overview

Claude não recebe vídeo como entrada. Printar frames perde tudo que é dito;
transcrever perde tudo que é mostrado. Quem **assiste** — quadros e áudio no mesmo
passe — é o Gemini. Esta skill põe o Gemini para assistir e depois **prova** o que
ele afirmou, porque ele erra calado: parafraseia e chama de citação, desliza o
timestamp, às vezes inventa um detalhe de tela.

**Princípio: o modelo descreve; fontes independentes confirmam.**

| Camada | Faz | Fonte de verdade |
|---|---|---|
| Gemini, blocos de 10 min | vê e ouve junto: o que está em quadro, texto na tela, fala | — |
| Whisper | transcreve o áudio sozinho | confirma cada fala e **corrige o timestamp** |
| ffmpeg | extrai o frame do meio de cada intervalo | prova do que estava em quadro |
| Você (Claude) | **lê os frames com a tool Read** | confere o que o Gemini disse que viu |

## Quick Reference

```bash
python "<diretório desta skill>/assistir-local.py" "caminho/do/video.mp4" pasta-saida
```

Saída em `pasta-saida/`: `relatorio.md` (timeline + verificação), `frames/*.jpg`,
`transcricao.txt`. Depois de rodar:

1. Leia `relatorio.md`.
2. **Leia cada frame listado com a tool Read** e confira contra a coluna "quadro".
3. Responda ao usuário usando só o que foi confirmado.

Opções: `--idioma en` (padrão `pt`), `--whisper base` (mais rápido que o padrão
`small`), `--sem-whisper`, `--manter-upload`.

## Precisão medida

| Vídeo | Falas confirmadas | Visual conferido |
|---|---|---|
| Gravação de tela, 0:56 | 4/4 | 4/4 |
| Câmera e tela alternando, 23:07 | 114/114 | 19/23 (83%) |

Áudio confiável; visual aproximado. Os erros visuais caem onde câmera e tela se
alternam em poucos segundos. **Por isso ler os frames não é opcional.**

## Como ler o relatório

- **conferida `NAO`** → paráfrase apresentada como verbatim. Não cite como fala literal.
- **tempo REAL** → use este timestamp; o início do intervalo erra alguns segundos.
- **Frames** → a descrição de quadro é hipótese até você ler o frame.
- Discordância em **nome próprio** entre Gemini e Whisper não é erro do Gemini: ele lê
  a palavra na tela. Num teste, o Whisper ouviu "proimbrusa" e o Gemini escreveu
  "pro Emusys" — que estava escrito no botão.

## Pré-requisitos

- `ffmpeg` e `ffprobe` no PATH
- Python 3.9+
- `GEMINI_API_KEY` no **ambiente** (chave em ai.google.dev)
- Transcrição, um dos dois:
  - `pip install --user faster-whisper` — local, grátis, privado. Na primeira execução
    baixa o modelo (~460 MB no `small`).
  - `OPENAI_API_KEY` no ambiente — Whisper pela API, ~US$ 0,006/min, mais rápido.

Nunca peça chave de API no chat. Se faltar, diga ao usuário para definir a variável
de ambiente e reiniciar o terminal.

## Common Mistakes

**Mandar o vídeo inteiro numa chamada.** Acima de ~10 min o modelo derrapa no tempo e
inventa detalhe de tela. O script já fatia em blocos de 10 min sobre um único upload.

**Pedir "descreva a cada minuto".** Força uma tela por minuto quando o vídeo troca
várias vezes no mesmo minuto; a precisão visual cai para ~60%. O prompt pede
**intervalos** (`INÍCIO - FIM`) — foi o que levou a 100%, ao mesmo custo.

**Confiar na fala sem conferir.** O Gemini confirma cerca de 87% das citações em vídeo
denso. O resto é paráfrase com aspas.

**Aceitar número que o modelo oferece.** Palavras por minuto, contagens, durações:
recalcule. Num teste ele disse 150–165 ppm onde o medido era 216.

**Olhar o total de palavras em vez da densidade por minuto.** Transcrição que perdeu um
trecho parece plausível no total. O script avisa minutos com menos de 20 palavras.

## Privacidade

O vídeo sobe para a API do Google. O script apaga o arquivo de lá ao terminar, mas na
camada gratuita da API o Google pode usar o conteúdo para melhorar produtos — confira
os termos do seu plano. Não envie gravação com dado pessoal sensível, conversa privada
ou material confidencial sem o usuário decidir isso explicitamente.

## O que isto não faz

Não mede prosódia. Entonação, ritmo e ênfase aparecem como observação qualitativa do
Gemini (linha "Som:"), não como medida.
