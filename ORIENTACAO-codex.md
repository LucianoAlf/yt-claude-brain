# Assistir vídeo no Codex (ou em qualquer agente fora do Claude Code)

Este repositório foi escrito para o Claude Code, mas **os scripts não dependem dele**.
São Python da biblioteca padrão mais três binários. Rodam em qualquer agente que
consiga executar comando no terminal e ler arquivo.

Duas coisas das skills **não** valem fora do Claude Code, e estão resolvidas abaixo:
o caminho `~/.claude/skills/`, e a instrução de ler os quadros "com a tool Read".

## O que é a habilidade, sem exagero

Nenhum desses agentes recebe vídeo como entrada. Quem assiste de verdade — quadros e
trilha de áudio no mesmo passe — é o **Gemini**. O que este repositório acrescenta é a
parte que o Gemini não faz sozinho: provar o que ele afirmou.

| Camada | Faz | Por que existe |
|---|---|---|
| **Gemini** | assiste em blocos de 10 min: o que está em quadro, texto na tela, fala | é quem vê e ouve junto |
| **Whisper** | transcreve o áudio por conta própria | fonte independente: confirma cada fala e corrige o horário |
| **ffmpeg** | extrai um quadro no meio de cada trecho | prova do que estava na tela |
| **Você** | **abre cada quadro e compara** | o Gemini erra calado; esta etapa é o que pega |

## Instalação

```bash
git clone https://github.com/LucianoAlf/yt-claude-brain.git
```

Pronto. Não existe passo de instalação: você chama o script pelo caminho do clone.

**Dependências:**

```bash
# Linux
sudo apt install -y ffmpeg
python -m pip install --user faster-whisper
python -m pip install --user --upgrade yt-dlp     # só se for usar YouTube

# Windows
winget install --id Gyan.FFmpeg --exact --silent --accept-package-agreements
python -m pip install --user faster-whisper
```

No Windows use `python`, nunca `python3` (é o atalho da Microsoft Store).

**Variáveis de ambiente:**

| Variável | Para quê | Obrigatória |
|---|---|---|
| `GEMINI_API_KEY` | é o Gemini que assiste o vídeo | **sim** (chave gratuita em ai.google.dev) |
| `OPENAI_API_KEY` | Whisper pela API, ~US$ 0,006/min, rápido | não — sem ela cai no `faster-whisper` local, grátis e mais lento |

Sem nenhum transcritor, o script roda mas **nenhuma fala é conferida**, e o relatório
diz isso. Nunca peça chave de API no chat e nunca grave chave em arquivo do projeto.

## Rodar

**Vídeo em arquivo** (baixado, WhatsApp, gravação de tela, reunião):

```bash
python yt-claude-brain/skills/assistir-video-local/assistir-local.py "video.mp4" analise
```

Opções: `--idioma en` (padrão `pt`), `--whisper base` (mais rápido que o padrão
`small`), `--sem-whisper`, `--manter-upload`.

**Vídeo do YouTube:**

```bash
python yt-claude-brain/skills/assistir-video-youtube/assistir-youtube.py "https://youtu.be/ID" analise
```

Saída em `analise/`: `relatorio.md`, `frames/*.jpg` e `transcricao.txt`.

## Depois de rodar — a parte que não pode ser pulada

1. Leia `analise/relatorio.md`.
2. **Abra cada imagem listada na seção "Frames"** e compare com a coluna que descreve a
   tela. Use o recurso do seu runtime para visualizar imagem. **Se você não conseguir
   ver imagem, diga isso ao usuário e trate toda afirmação de tela como não
   verificada** — não finja que conferiu.
3. Só cite como **fala literal** o que estiver `OK` na coluna "conferida". Linha `NAO`
   é paráfrase com aspas: serve de resumo, não de citação.
4. Use a coluna **tempo REAL** como horário. O início do intervalo erra alguns segundos.
5. Se aparecer **COBERTURA INCOMPLETA** no topo, há trecho sobre o qual o modelo não
   disse nada, mesmo depois da repetição automática. As taxas valem só para o resto.
6. Número que o modelo oferece (duração, contagem, palavras por minuto) não é medida.
   Recalcule ou não use.
7. Ao responder, diga o que foi confirmado e o que não foi.

## Precisão medida

| Vídeo | Falas confirmadas | Telas conferidas |
|---|---|---|
| Gravação de tela de celular, 0:56 | 4/4 | 4/4 |
| Câmera e tela alternando, 23:07 | 114/114 | 19/23 |
| Tutorial no YouTube, 26:56 | 68/73 | 16/18 |

**Áudio é confiável, tela é aproximada.** Os erros visuais se concentram onde câmera e
tela se alternam em poucos segundos: o Gemini descreve o trecho inteiro e o quadro do
meio cai do outro lado. É por isso que o passo 2 existe.

Onde o multimodal ganha do áudio sozinho: num teste o Whisper ouviu "proimbrusa" e o
Gemini escreveu "pro Emusys" — porque a palavra estava escrita na tela. Discordância em
nome próprio entre os dois não é erro do Gemini.

## Cuidados

- **O vídeo sobe para a API do Google.** O script apaga o arquivo de lá ao terminar, mas
  na camada gratuita o Google pode usar o conteúdo para melhorar produtos. Gravação de
  reunião interna, conversa privada, dado de aluno ou financeiro: pergunte ao usuário
  antes de enviar.
- **YouTube a partir de servidor ou VPS costuma ser bloqueado** por reputação de IP. Se
  o download falhar, tente outro `player_client` (`mweb` funcionou quando `web`,
  `web_safari`, `tv` e `ios` falharam) ou peça o arquivo ao usuário.
- **Se o relatório não bater com o que você vê nos quadros, reporte a divergência.** Não
  "corrija" o relatório por conta própria.

## Equivalências com o Claude Code

| No repositório | Fora do Claude Code |
|---|---|
| instalar em `~/.claude/skills/` | não instale: chame o script pelo caminho do clone |
| "leia o frame com a tool Read" | abra a imagem com o recurso do seu runtime |
| a skill dispara sozinha ao ver um vídeo | você decide rodar, ou o usuário pede |
