# Orientação: plugin claude-video-vision (teste real)

Testado em 2026-08-30 no vídeo `TSimMWwR6to` (Bruno Okamoto, 55:08), backend Gemini API.

---

## O que ele é

`jordanrendric/claude-video-vision` — plugin com **servidor MCP**, não skill de script.
Ferramentas: `video_info`, `video_analyze`, `video_watch`, `video_detail`, `video_configure`,
`video_setup`. MIT, duas dependências (`@modelcontextprotocol/sdk`, `zod`).

**Ressalva de cadeia de suprimentos:** o `.mcp.json` roda `npx -y claude-video-vision@latest`.
O que executa é o pacote npm no momento da execução, **não** o repositório que você auditou.
Auto-atualiza sem aviso.

Instalação exige **reiniciar** o Claude Code — servidor MCP de plugin só sobe no início da
sessão. E ele lê `GEMINI_API_KEY` / `OPENAI_API_KEY` da **variável de ambiente**, não de
arquivo `.env`. A chave que a `/watch` usa (em `~/.config/watch/.env`) **não serve** para ele.

## Onde ele é melhor que a /watch

**Não usa legenda do YouTube.** Transcreve o áudio direto com Gemini. Isso elimina por
construção a pior armadilha da `/watch` — a legenda auto-traduzida para inglês. Confirmado
no teste: transcrição voltou em português correto, sem contaminação.

**Arquitetura em dois estágios.** `video_analyze` planeja (cenas, silêncio, loudness,
movimento) **sem extrair frames**; só depois `video_watch` extrai. Gasta token melhor.

**Filtros ffmpeg reais**, que a `/watch` não tem: `scene_changes` com *score* por corte,
`silence`, `loudness` (ebur128), `motion` (siti), `blur`, `exposure`, `freeze`, `black_intervals`.

**Declara procedência.** Devolve `audio_warnings` descrevendo decisões de fronteira de
chunk. A `/watch` não conta nada disso.

Medições reais do teste: 160 cortes de cena com score; loudness média **-21,8 LUFS**,
faixa **6,1 LU**.

## O defeito grave: perda silenciosa de conteúdo

**O plugin perdeu ~85% dos primeiros 10 minutos e reportou sucesso.**

Ele fatia o áudio em chunks (config padrão: dispara acima de 1200 s, chunks de 600 s).
Densidade de palavras por faixa no teste:

| Faixa | Palavras | PPM |
|---|---|---|
| **0–10 min** | **215** | **22** |
| 10–20 min | 1482 | 148 |
| 20–30 min | 1823 | 182 |
| 30–40 min | 1695 | 170 |
| 40–50 min | 1732 | 173 |
| 50–55 min | 866 | 168 |

O chunk 0 devolveu **um único segmento rotulado `00:00:00 → 00:10:00`** contendo apenas a
introdução (termina em *"Partiu vídeo de hoje"*, ~90 s de fala). Os ~8,5 minutos seguintes
sumiram. Todos os outros chunks vieram com granularidade fina (mediana de 11 s por segmento).

**Os `audio_warnings` NÃO sinalizaram isso.** Eles reportaram `loose_threshold` para os
chunks 0 a 3 — mas os chunks 1, 2 e 3 saíram perfeitos. O aviso não correlaciona com a perda.

### Como detectar

Calcule palavras por minuto **por faixa**, não no total. O total do teste (7813 palavras /
55 min = 142 PPM) parece plausível e esconde o buraco. A anomalia só aparece por faixa.

Regra: se uma faixa destoa em ordem de grandeza das vizinhas, houve perda. Sinal auxiliar:
**um segmento cujo `end - start` é do tamanho do chunk** (600 s) em vez de dezenas de
segundos significa que aquele chunk não foi segmentado de verdade.

## O download dele falha igual

`video_info` e `video_analyze` com URL do YouTube deram `HTTP Error 403: Forbidden` — duas
vezes. Ele usa o **mesmo yt-dlp do sistema**, então herda a mesma exposição a anti-bot.
Não é solução para o problema de download.

### O que destravou (achado novo e útil)

Cinco tentativas de download direto falharam com 403. O que funcionou:

```bash
yt-dlp --remote-components ejs:github -f "worst[height<=480]/worst" -o "saida.%(ext)s" "<url>"
```

O `--remote-components ejs:github` habilita o solucionador de desafio JS que o yt-dlp pula
por padrão (ele avisa nos logs que pulou). Baixou em 530 fragmentos onde o método normal
dava 403 consistente. **Este é o passo de escalada a tentar antes de cookies ou PO token.**

Depois é só passar o **arquivo local** ao plugin — ele aceita caminho, e assim o download
deixa de ser problema dele.

## Cuidado ao baixar para análise visual

Se você baixar com `-f worst` para vencer o 403, pode acabar com **256×144**, como
aconteceu aqui. Serve para transcrição e para os filtros de áudio, mas **inutiliza a
análise de frames**. Para passe visual, force altura mínima: `-f "bv[height<=720]+ba/b"`.


## A correção definitiva

O problema **não é o Gemini, é a camada de chunking do plugin.** Chamando a API do
Gemini direto com o vídeo inteiro, os mesmos 10 minutos que o plugin perdeu voltaram
como 16 itens com timestamps, fala e tela, em 25 s. O vídeo completo de 55 min coube
numa única chamada: 301.113 tokens de vídeo, 127 s, sem truncar.

Use [`scripts/gemini-assistir.py`](scripts/gemini-assistir.py). Ver
`ORIENTACAO-analise-de-audio-com-gemini.md`.

Este plugin continua útil pelos filtros ffmpeg (`loudness`, `scene_changes` com score,
`silence`, `motion`) — mas **não** para transcrever vídeo longo.

## Veredito

Vale ter, **mas não substitui verificação**. Ele resolve a armadilha da legenda traduzida
por construção e traz filtros de áudio que a `/watch` não tem. Em troca introduz uma falha
pior: enquanto a `/watch` erra de forma *visível* (transcrição em inglês salta aos olhos),
este erra de forma *invisível* — devolve JSON bem-formado, com timestamps, faltando 8
minutos de conteúdo.

**Sempre confira densidade de palavras por faixa antes de confiar na transcrição.**
