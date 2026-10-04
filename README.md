# yt-claude-brain

Base de conhecimento compartilhada entre os agentes (Alfredo, Mike e outros).

Cada documento aqui registra o que foi aprendido **na prática** operando uma ferramenta —
principalmente as coisas que falham em silêncio e não aparecem na documentação oficial.

## Comece por aqui: dar a um agente a habilidade de assistir vídeo

```bash
git clone https://github.com/LucianoAlf/yt-claude-brain.git
cp -r yt-claude-brain/skills/assistir-video-local  ~/.claude/skills/
cp -r yt-claude-brain/skills/assistir-video-youtube ~/.claude/skills/
```

Skills em `~/.claude/skills/` valem para **todos** os projetos do Claude Code da máquina.
Passo a passo, dependências e prompt pronto para colar em outro chat:
[PROMPT-mestre-assistir-video.md](PROMPT-mestre-assistir-video.md).

**O que a habilidade é, sem exagero:** o Claude não recebe vídeo. Quem assiste imagem e
som juntos é o Gemini; o Whisper confere cada fala de forma independente e corrige o
horário; o `ffmpeg` extrai um quadro por trecho para o agente conferir a tela. Áudio é
confiável, tela é aproximada — por isso ler os quadros não é opcional.

| Vídeo testado | Falas confirmadas | Telas conferidas |
|---|---|---|
| Gravação de tela, 0:56 | 4/4 | 4/4 |
| Câmera e tela alternando, 23:07 | 114/114 | 19/23 |
| Tutorial no YouTube, 26:56 | 68/73 | 16/18 |

## Conteúdo

### Assistir vídeo

| Arquivo | O que é |
|---|---|
| [skills/assistir-video-local/](skills/assistir-video-local/SKILL.md) | **Skill** — vídeo em arquivo (baixado, WhatsApp, gravação de tela, reunião) |
| [skills/assistir-video-youtube/](skills/assistir-video-youtube/SKILL.md) | **Skill** — vídeo do YouTube, com a legenda original como verdade-base |
| [PROMPT-mestre-assistir-video.md](PROMPT-mestre-assistir-video.md) | Prompt para colar em outro agente: instala, confere o ambiente e ensina a usar |
| [ORIENTACAO-codex.md](ORIENTACAO-codex.md) | **Fora do Claude Code** (Codex e outros): os scripts rodam igual, sem instalar skill |
| [ORIENTACAO-assistir-video-local.md](ORIENTACAO-assistir-video-local.md) | Instalação, precisão medida, privacidade, custo e os bugs já encontrados |
| [ORIENTACAO-analise-de-audio-com-gemini.md](ORIENTACAO-analise-de-audio-com-gemini.md) | O método com o Gemini e o que dele dá para confiar |
| [ORIENTACAO-assistir-youtube.md](ORIENTACAO-assistir-youtube.md) | A skill `/watch` e as quatro armadilhas silenciosas dela |
| [ORIENTACAO-claude-video-vision.md](ORIENTACAO-claude-video-vision.md) | Teste do plugin alternativo: perde conteúdo em silêncio |
| [PROMPT-onboarding-watch.md](PROMPT-onboarding-watch.md) | Prompt de onboarding da `/watch` (anterior às skills acima) |

### Cortes verticais para Reels e Shorts

| Arquivo | O que é |
|---|---|
| [PIPELINE-cortes-virais.md](PIPELINE-cortes-virais.md) | Implementação própria, testada ponta a ponta: da decupagem ao motion |
| [GUIA-cortes-virais-claude-code.md](GUIA-cortes-virais-claude-code.md) | O método do vídeo do LABS, reconstruído e conferido quadro a quadro |
| [scripts/decupagem.py](scripts/decupagem.py) | Legenda do YouTube → JSON com timing **por palavra** |
| [scripts/cortar-vertical.py](scripts/cortar-vertical.py) | Recorte 9:16 seguindo o rosto + legenda acesa palavra a palavra |
| [scripts/asset-transparente.py](scripts/asset-transparente.py) | Devolve canal alfa a asset que veio com o xadrez desenhado |
| [scripts/motion.py](scripts/motion.py) | Anima os assets ancorados no instante em que a palavra é dita |

### Scripts de apoio e referência

| Arquivo | O que é |
|---|---|
| [scripts/assistir-youtube.py](scripts/assistir-youtube.py) | Pipeline do YouTube (mesma cópia que vai dentro da skill) |
| [scripts/gemini-assistir.py](scripts/gemini-assistir.py) | Pergunta livre sobre um vídeo (URL ou arquivo), com verificação de citação |
| [scripts/limpar-vtt.py](scripts/limpar-vtt.py) | Remove duplicatas e tags de legenda VTT |
| [scripts/mapa-visual.py](scripts/mapa-visual.py) | Mapa visual por detecção de cena (superado pelo método em blocos) |
| [estilo-labs.md](estilo-labs.md) | Decomposição do estilo editorial do canal LABS |
| [ORIENTACAO-google-navegador-isolado.md](ORIENTACAO-google-navegador-isolado.md) | Alcançar ferramentas Google com a conta de agentes, sem receber senha |

## Como um agente usa isto

Leia o documento relevante **antes** de operar a ferramenta, não depois de errar.
As orientações são escritas para serem seguidas direto, com os comandos prontos.

## Convenção

- Documentos de orientação começam com `ORIENTACAO-`
- Cada afirmação técnica deve vir de teste real, com o número medido quando houver
- Quando algo falhar em silêncio, registre **como detectar**, não só como corrigir
- O repositório é **público**: nada de chave, dado de aluno, financeiro ou pessoal aqui
