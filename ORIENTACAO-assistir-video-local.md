# Assistir vídeo local — instalação para outros projetos e agentes

Para quando o vídeo **não** está no YouTube: arquivo baixado, gravação de tela, vídeo
de WhatsApp, gravação de reunião. Skill: [`skills/assistir-video-local/`](skills/assistir-video-local/).

## O que "assistir" quer dizer aqui — sem exagero

O Claude **não recebe vídeo**. Nenhuma versão recebe. Quem assiste de verdade — quadros
e áudio no mesmo passe, como um modelo multimodal — é o **Gemini**. Printar frames e
mandar para o Claude perde tudo que é dito; transcrever perde tudo que é mostrado.

O que a skill faz é juntar três fontes, cada uma com uma função:

| Quem | Faz | Por quê |
|---|---|---|
| **Gemini** | assiste o vídeo em blocos de 10 min, imagem e som juntos | é o único que vê e ouve ao mesmo tempo |
| **Whisper** | transcreve o áudio sozinho | fonte independente para conferir o que o Gemini disse que foi falado |
| **ffmpeg + Claude** | extrai um frame por intervalo, e o Claude lê cada um | prova do que o Gemini disse que estava em quadro |

O Gemini erra calado: chama paráfrase de citação e desliza o timestamp. A skill mostra
onde ele errou, em vez de deixar o erro passar como fato.

## Resultado medido

| Vídeo | Duração | Falas confirmadas | Visual conferido | Tempo total |
|---|---|---|---|---|
| Gravação de tela de celular (WhatsApp) | 0:56 | **4/4** | 4/4 | ~30 s |
| Tutorial com câmera e tela alternando (arquivo local, 360p) | 23:07 | **114/114** | **19/23 (83%)** | 11 min |

**O áudio é confiável; o visual é aproximado.** Os 4 erros visuais do vídeo longo
estão todos em trechos onde câmera e tela se alternam em poucos segundos: o Gemini
descreve o intervalo como um todo, e o frame do meio cai no outro lado. É exatamente
por isso que a skill manda o Claude **ler cada frame** — sem essa etapa, 1 em cada 6
afirmações de tela desse vídeo passaria como fato.

No YouTube, o mesmo método deu 87–100% nas falas e 93–100% no visual — ver
[ORIENTACAO-analise-de-audio-com-gemini.md](ORIENTACAO-analise-de-audio-com-gemini.md).

**Onde o tempo vai:** dos 11 min do vídeo longo, a maior parte é o Whisper local na
CPU. Com `--whisper base` ou com `OPENAI_API_KEY` definida, cai bastante.

**Onde o multimodal ganha:** nesse teste o Whisper ouviu "proimbrusa"; o Gemini escreveu
"pro Emusys", porque a palavra estava escrita no botão. Só o áudio erra o nome próprio;
imagem e som juntos acertam.

---

## Instalar

### Nesta máquina — vale para todos os projetos

Skills em `~/.claude/skills/` ficam disponíveis em **qualquer** projeto do Claude Code.
A skill já foi instalada lá. Para reinstalar ou atualizar:

```bash
cp -r /d/yt-claude-brain/skills/assistir-video-local ~/.claude/skills/
```

Os chats que já estavam abertos só enxergam a skill depois de reiniciar a sessão.

### Em outra máquina

```bash
git clone https://github.com/LucianoAlf/yt-claude-brain.git
cp -r yt-claude-brain/skills/assistir-video-local ~/.claude/skills/
```

### Dependências

```bash
winget install --id Gyan.FFmpeg --exact --silent --accept-package-agreements
python -m pip install --user faster-whisper
```

E `GEMINI_API_KEY` como **variável de ambiente** do Windows (chave grátis em
ai.google.dev). Opcional: `OPENAI_API_KEY`, que troca o Whisper local pelo da API —
mais rápido, ~US$ 0,006 por minuto.

No Windows use `python`, nunca `python3` (é o atalho da Microsoft Store).

### Conferir se está tudo certo

```bash
python -c "import os,faster_whisper;print('gemini:', 'ok' if os.environ.get('GEMINI_API_KEY') else 'FALTA'); print('faster-whisper:', faster_whisper.__version__)"
```

```bash
ffmpeg -version
```

---

## Prompt para colar em outro chat

```
Preciso que você assista um vídeo local com precisão — imagem e som juntos, não só
transcrição e não só prints.

Use a skill assistir-video-local. Se ela não estiver disponível nesta sessão, instale:
  cp -r /d/yt-claude-brain/skills/assistir-video-local ~/.claude/skills/
e leia o SKILL.md dessa pasta antes de começar.

Rode o script da skill no vídeo:
  python "<pasta da skill>/assistir-local.py" "<CAMINHO DO VIDEO>" analise-video

Depois:
1. Leia analise-video/relatorio.md.
2. Leia CADA frame listado na seção "Frames" com a tool Read e confira contra a coluna
   "quadro". O que o Gemini diz que viu é hipótese até você olhar o frame.
3. Só cite como fala literal o que estiver com "OK" na coluna "conferida". Use a coluna
   "tempo REAL" como timestamp.
4. Me diga o que foi confirmado e o que não foi.

Não me peça chave de API no chat. Se GEMINI_API_KEY faltar, me diga para configurar a
variável de ambiente.

Vídeo: <CAMINHO DO VIDEO>
O que eu quero saber: <SUA PERGUNTA>
```

---

## Antes de mandar um vídeo

O vídeo **sobe para a API do Google**. O script apaga o arquivo de lá ao terminar, mas
na camada gratuita da API o Google pode usar o conteúdo para melhorar produtos — confira
os termos do plano da chave. Gravação de reunião interna, conversa privada, dado de
aluno ou financeiro: decida conscientemente antes. Pela regra do cérebro da empresa,
conteúdo **restrito** não sai.

## Quanto custa

| Item | Custo |
|---|---|
| Gemini (flash) | ~5.500 tokens por minuto de vídeo; a camada gratuita cobre uso normal |
| Whisper local | grátis; na primeira execução baixa o modelo (~460 MB) |
| Whisper pela API | ~US$ 0,006 por minuto |
| Tempo | vídeo de 1 min: ~30 s. Vídeo de 23 min: ~11 min com Whisper local |

## Bugs encontrados no teste — e como perceber se voltarem

- **Upload grande falhava em silêncio.** O início do upload resumível tem que ir para
  `/upload/v1beta/files`; o endereço sem `/upload` responde 200 com corpo vazio. Sintoma:
  `ValueError: unknown url type: 'None'`. Afetava também `scripts/gemini-assistir.py`
  com qualquer arquivo acima de 20 MB.
- **Conferidor comparava texto de botão com o áudio.** Em gravação de tela, a primeira
  coisa entre aspas é o rótulo de um botão, não a fala. Sintoma: 0% de confirmação com
  falas visivelmente corretas no bruto. A citação agora vem só da linha `Fala:`.
- **Fala repetida recebia o timestamp da primeira vez.** Um trecho reprisado no fim do
  vídeo foi "corrigido" em 293 s para trás — o Gemini estava certo. Sintoma: um "pior
  erro de timestamp" de minutos quando a média é de segundos. Corrigido também nos
  scripts de YouTube.
