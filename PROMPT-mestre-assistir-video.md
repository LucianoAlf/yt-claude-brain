# Prompt mestre — assistir vídeo (local e YouTube)

Cole o bloco abaixo inteiro no chat do agente. Ele serve em qualquer máquina: se as
skills já estiverem instaladas, o agente só confere; se não, instala.

---

```
Vou te dar uma habilidade nova: assistir vídeo de verdade — imagem e som juntos —
com prova do que foi visto e ouvido. Instale, confira e passe a usar sempre que eu
mandar um vídeo. Leia tudo antes de agir.

## O que é, sem exagero

Você (Claude) não recebe vídeo como entrada. Printar frames perde o que é dito;
transcrever perde o que é mostrado. Quem assiste imagem e som juntos é o Gemini.
A habilidade junta três fontes:

1. Gemini assiste em blocos de 10 min e descreve quadro, texto na tela e fala.
2. Whisper transcreve o áudio de forma independente e confirma cada fala que o
   Gemini citou, corrigindo o timestamp.
3. ffmpeg tira um frame por trecho, e VOCÊ lê cada frame para conferir o que o
   Gemini disse que estava na tela.

Medido: fala 114/114 confirmada num vídeo de 23 min; tela 19/23 (83%). O áudio é
confiável, a tela é aproximada — os erros aparecem onde câmera e tela se alternam
rápido. Por isso ler os frames é obrigatório.

## Passo 1 — ver se já está instalado

Confira se existem as pastas:
  ~/.claude/skills/assistir-video-local/
  ~/.claude/skills/assistir-video-youtube/
Se existirem, pule para o Passo 3.

## Passo 2 — instalar

Mesma máquina do repositório (Windows, D:\yt-claude-brain existe):
  cp -r /d/yt-claude-brain/skills/assistir-video-local ~/.claude/skills/
  cp -r /d/yt-claude-brain/skills/assistir-video-youtube ~/.claude/skills/

Outra máquina:
  git clone https://github.com/LucianoAlf/yt-claude-brain.git
  cp -r yt-claude-brain/skills/assistir-video-local ~/.claude/skills/
  cp -r yt-claude-brain/skills/assistir-video-youtube ~/.claude/skills/

Dependências:
  - ffmpeg e ffprobe no PATH
      Windows: winget install --id Gyan.FFmpeg --exact --silent --accept-package-agreements
      Linux:   sudo apt install -y ffmpeg   (peça minha autorização antes de usar sudo)
  - python -m pip install --user faster-whisper
  - só para YouTube: python -m pip install --user --upgrade yt-dlp
No Windows use "python", nunca "python3" (é o atalho da Microsoft Store).

Chave: GEMINI_API_KEY precisa estar como variável de AMBIENTE. Opcional:
OPENAI_API_KEY troca o Whisper local pelo da API (mais rápido, ~US$0,006/min).
NUNCA me peça chave no chat e nunca a escreva em arquivo. Se faltar, me diga para
configurar a variável e reiniciar o terminal.

## Passo 3 — conferir o ambiente

Rode e me mostre o resultado:
  python -c "import os;print('GEMINI_API_KEY:', 'ok' if os.environ.get('GEMINI_API_KEY') else 'FALTA')"
  python -c "import faster_whisper;print('faster-whisper', faster_whisper.__version__)"
  ffmpeg -version

Depois leia os dois SKILL.md instalados. Eles têm as regras completas.

## Como usar

Vídeo em arquivo (baixado, WhatsApp, gravação de tela, reunião):
  python "<pasta da skill assistir-video-local>/assistir-local.py" "<VIDEO>" analise-video
  Opções: --idioma en | --whisper base (mais rápido) | --sem-whisper

Vídeo do YouTube:
  python "<pasta da skill assistir-video-youtube>/assistir-youtube.py" "<URL>" analise-video

Os dois geram analise-video/relatorio.md, analise-video/frames/*.jpg e a transcrição.

## Regras ao responder sobre o vídeo

1. Leia relatorio.md inteiro.
2. Leia CADA frame listado na seção "Frames" com a tool Read e compare com a coluna
   "quadro". O que o Gemini diz que viu é hipótese até você olhar o frame. Se não
   bater, diga que não bateu.
3. Só cite como fala literal o que estiver "OK" na coluna "conferida". Linha "NAO" é
   paráfrase — use como resumo, nunca entre aspas.
4. Use a coluna "tempo REAL" como timestamp.
5. Número que o modelo oferece (duração, contagem, palavras por minuto) não é
   medida. Recalcule ou não use.
6. Se o Whisper e o Gemini discordarem num nome próprio, o Gemini pode estar certo:
   ele lê a palavra na tela.
7. Ao terminar, diga o que foi confirmado e o que não foi, com os números do
   relatório.

## Cuidados

- O vídeo sobe para a API do Google (o script apaga ao terminar). Na camada gratuita
  o Google pode usar o conteúdo para melhorar produtos. Gravação de reunião interna,
  conversa privada, dado de aluno ou financeiro: me pergunte antes de mandar.
- YouTube a partir de servidor/VPS costuma ser bloqueado por reputação de IP. Se o
  download falhar, tente outro player_client (mweb funcionou quando os outros
  falharam) ou peça que eu baixe o vídeo e mande o arquivo.
- Se o relatório não bater com o que você vê nos frames, reporte a divergência.
  Não "corrija" o relatório por conta própria.

## Quando terminar a instalação

Me responda só com:
- skills instaladas: sim/não (caminho)
- ffmpeg / faster-whisper / GEMINI_API_KEY: ok ou o que falta
- pronto para receber um vídeo: sim/não
```

---

Referência completa: [ORIENTACAO-assistir-video-local.md](ORIENTACAO-assistir-video-local.md).
