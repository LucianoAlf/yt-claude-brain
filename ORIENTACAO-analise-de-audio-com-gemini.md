# Orientação: fazer o Gemini ASSISTIR um vídeo

A solução definitiva para o que a `/watch` não faz — e para o que o
`claude-video-vision` faz errado.

Ferramenta: [`scripts/gemini-assistir.py`](scripts/gemini-assistir.py)

---

## A regra de ouro

> **Não fatie o vídeo. Mande inteiro, numa chamada só.**

Todo problema que encontramos veio de intermediários que picam o áudio antes de
entregar ao modelo. O Gemini aceita o vídeo inteiro e processa **frames e trilha
juntos** — é isso que faz ele *assistir* em vez de *transcrever*.

## Números medidos (2026-08-30)

Vídeo de **55:08** do YouTube, uma única chamada a `gemini-3.7-flash`:

| Métrica | Valor |
|---|---|
| Tokens de vídeo | **301.113** |
| Tempo | **127 s** |
| Truncamento | Nenhum (`finishReason: STOP`) |
| Custo por minuto de vídeo | ~5.500 tokens |
| Download necessário | **Nenhum** — URL do YouTube vai direta |

Um vídeo de 55 min consome ~300k tokens, bem dentro do contexto de 1M dos modelos
flash. **Vídeo de até ~3 horas cabe numa chamada só.**

## Uso

```bash
python scripts/gemini-assistir.py "<url-ou-arquivo>" "<pergunta>" [inicio] [fim]
```

```bash
python scripts/gemini-assistir.py "https://youtu.be/ID" "Estrutura em blocos com timestamps MM:SS, o que e dito e o que aparece na tela"
```

```bash
python scripts/gemini-assistir.py "https://youtu.be/ID" "O que aparece na tela?" 0s 600s
```

O script aceita URL do YouTube (sem download), arquivo local até 20 MB (inline) ou
maior (sobe pela File API). Faz retry em 429/500/503 e cai por uma lista de modelos.

Exige `GEMINI_API_KEY` no **ambiente** (`ai.google.dev`, camada gratuita).

## O que ele entrega que as outras ferramentas não

Numa passada só, com timestamps: estrutura em blocos, o que é dito, **o que aparece
na tela** (aplicativo, diagrama, aba do navegador, gráfico), transições, vinheta,
e leitura de conteúdo visual — texto de diagrama, nome de arquivo, item de menu.

Comparação real no mesmo vídeo, trecho 00:00–10:00:

| Ferramenta | Resultado |
|---|---|
| `claude-video-vision` | 215 palavras, um bloco sem timestamps internos, **~85% perdido em silêncio** |
| `gemini-assistir.py` | 16 itens com timestamps, fala + tela, em 25 s |

## Por que o chunking destrói o resultado

O `claude-video-vision` fatia o áudio em pedaços (padrão: acima de 20 min, pedaços de
10 min) e manda cada pedaço **como áudio isolado**. Sem o vídeo e sem o contexto do
todo, o modelo pode *resumir* em vez de *transcrever* — foi o que aconteceu com o
primeiro pedaço no teste.

Mandando o vídeo inteiro, isso não ocorre: o modelo vê a linha do tempo completa.

## Onde o Gemini ainda não é confiável

Isto continua valendo e **não** foi resolvido:

> Ele é boa **testemunha qualitativa** e mau **instrumento de medição**.

Num teste anterior ele afirmou ritmo de fala de 150–165 palavras por minuto; medido na
transcrição, eram **216**. Erro de ~30% na única alegação numérica verificável.

**Aceite:** onde ele pausa, o que enfatiza, se a voz varia, se há trilha, o que está na
tela, a estrutura do vídeo.
**Não aceite:** PPM, nível de energia em escala, frequência em Hz, decibéis.
Se um número importa, **meça você** — palavras da transcrição pela duração do `ffprobe`.

**Exija citação verbatim com timestamp** em cada afirmação. Sem isso, não há como
distinguir análise real de texto plausível. Com isso, dá para cruzar contra uma
transcrição independente e confirmar que ele processou o vídeo de fato — foi assim que
se verificou aqui (5 citações conferidas, 5 corretas).

## Armadilhas operacionais

**503 "high demand"** é comum nos modelos novos e é transitório. O script já faz retry
com espera crescente e cai para o modelo seguinte. Não conclua que a chave está errada.

**Só vídeo público** quando se usa URL do YouTube. Vídeo privado ou não listado exige
baixar e subir pela File API.

**Não confunda com a rota do navegador.** Usar a interface web do Gemini funciona mas é
frágil: `form_input` não dispara o evento de envio e `Enter` só quebra linha — é preciso
achar o botão no DOM. Para uso repetido, sempre a API.

## Validação externa

No próprio vídeo analisado (Bruno Okamoto, bloco 21:16–26:54), ele descreve que o agente
de conteúdo dele usa **Gemini Flash para assistir e resumir vídeos**. É a mesma
arquitetura descrita aqui, em produção, por um terceiro.

## Fontes

- https://ai.google.dev/gemini-api/docs/video-understanding
- https://github.com/jordanrendric/claude-video-vision
