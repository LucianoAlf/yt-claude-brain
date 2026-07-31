# yt-claude-brain

Base de conhecimento compartilhada entre os agentes (Alfredo, Mike e outros).

Cada documento aqui registra o que foi aprendido **na prática** operando uma ferramenta —
principalmente as coisas que falham em silêncio e não aparecem na documentação oficial.

## Conteúdo

| Arquivo | O que é |
|---|---|
| [ORIENTACAO-assistir-youtube.md](ORIENTACAO-assistir-youtube.md) | Como usar a skill `/watch` para assistir vídeos do YouTube sem cair nas quatro armadilhas silenciosas |
| [estilo-labs.md](estilo-labs.md) | Decomposição do estilo editorial do canal LABS — roteiro, retórica, registro de fala e sistema visual |
| [scripts/limpar-vtt.py](scripts/limpar-vtt.py) | Remove duplicatas e tags de legendas VTT do YouTube |

## Como um agente usa isto

Leia o documento relevante **antes** de operar a ferramenta, não depois de errar.
As orientações são escritas para serem seguidas direto, com os comandos prontos.

## Convenção

- Documentos de orientação começam com `ORIENTACAO-`
- Cada afirmação técnica deve vir de teste real, com o número medido quando houver
- Quando algo falhar em silêncio, registre **como detectar**, não só como corrigir
