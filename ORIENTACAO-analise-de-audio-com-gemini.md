# Orientação: analisar o áudio de um vídeo (o que a /watch não faz)

Pesquisa + teste feitos em 2026-07-31.

---

## O problema

A skill `/watch` entrega **frames + transcrição de texto**. Ela não analisa áudio. Logo,
qualquer pergunta sobre **entonação, ritmo de fala, pausa, ênfase, trilha ou efeito sonoro**
fica sem resposta — e essas são justamente as perguntas de quem quer copiar um estilo de
apresentação.

## O estado da arte (julho/2026)

**A API do Claude não aceita vídeo nativamente.** Confirmado por pesquisa: todas as soluções
existentes são camadas de percepção que quebram o vídeo em frames + transcrição antes de
entregar ao modelo. Não existe atalho — não adianta procurar uma flag escondida.

**O Gemini aceita URL do YouTube diretamente** e processa **frames e a trilha de áudio
sincronizada**, permitindo raciocínio entre as duas. Limites documentados: amostragem visual
de 1 quadro por segundo, 1 vídeo por requisição, 8 h de vídeo por dia, **somente vídeos
públicos**, e suporte a perguntas por timestamp MM:SS.

**Plugin alternativo que vale conhecer:** `jordanrendric/claude-video-vision` faz o mesmo que
o `bradautomates/claude-video` porém com backends de áudio plugáveis (Gemini, Whisper local,
OpenAI) e — o detalhe importante — **rotula a origem da transcrição** (`transcription_source:
youtube_subtitles` vs `youtube_auto_captions`). Isso ataca de frente o problema de legenda
contaminada descrito em `ORIENTACAO-assistir-youtube.md`.

## O teste

Vídeo `EzcXGtjNm5E` (LABS, 18:54) enviado ao Gemini pelo navegador isolado, com pedido de
análise de entrega vocal e timestamps.

**Funcionou.** Ele devolveu ritmo, pausas, ênfase, variação de altura, curva de energia e
descrição de trilha e efeitos — tudo com timestamp.

## A parte que importa: o que dá para confiar

Cruzei as citações dele contra uma transcrição `pt-orig` obtida de forma independente.

**Citações e timestamps: corretos.** Cinco verificados, cinco batendo — "cinco níveis e 30
conceitos" em [00:27], "não trava no nome da ferramenta" em [02:19], "terceiro nível: memória"
em [06:44], "uma das coisas mais importantes seria essa" em [09:30], "prompts mágicos" em
[06:00]. Ele **realmente processou** o vídeo; não alucinou o conteúdo.

**Alegação quantitativa: errada.** Ele afirmou ritmo de **150–165 palavras por minuto**.
Medido na transcrição: **216 PPM** (4077 palavras / 18,9 min). Erro de ~30%, e o erro real é
maior ainda: 216 é a média sobre o vídeo inteiro, incluindo trechos sem narração — o ritmo
durante a fala é mais alto que isso.

### Regra que fica

> O Gemini é bom **testemunha qualitativa** do áudio e ruim **instrumento de medição**.

Aceite dele: *onde* ele pausa, *o que* ele enfatiza, *se* a voz varia, *se* há trilha.
Não aceite: número de PPM, nível de energia em escala, frequência em Hz, decibéis. Se um
número importa, **meça você**: palavras da transcrição dividido pela duração do `ffprobe`.

## Como usar

1. Obtenha a transcrição `pt-orig` de forma independente (ver `ORIENTACAO-assistir-youtube.md`)
2. Peça a análise de áudio ao Gemini, exigindo **citação verbatim + timestamp** em cada afirmação
3. **Cruze as citações** contra sua transcrição — se elas batem, ele processou o vídeo de fato
4. **Recalcule sozinho** qualquer número que ele oferecer
5. Trate o que sobrou como observação, não como medida

O passo 2 é o que torna o resto possível: sem exigir citação verbatim, não há como
distinguir análise real de texto plausível.

## Caminho mais robusto que navegador

O teste acima foi feito pela interface web, que é frágil: `form_input` preenche o campo mas
não dispara o evento que habilita o envio, e `Enter` insere quebra de linha em vez de enviar
— é preciso localizar e clicar o botão "Enviar mensagem", que só existe no DOM depois que há
texto. Funciona, mas gasta várias idas e vindas.

Para uso repetido, a API do Gemini é o caminho: aceita a URL do YouTube direto e tem camada
gratuita. Exige criar uma chave em `ai.google.dev` — **decisão do usuário**, e a chave nunca
deve ir para arquivo versionado.

## Fontes

- https://ai.google.dev/gemini-api/docs/video-understanding
- https://developers.googleblog.com/en/gemini-2-5-video-understanding/
- https://github.com/jordanrendric/claude-video-vision
- https://explainx.ai/blog/can-llms-watch-video-claude-gemini-solutions-2026
