# Estilo LABS — decomposição

Fonte: "Agentes de IA em 18 minutos (O que 95% não entendem)" — canal LABS, 18:54, 2026-07-31.
Base: 100 frames (de 440 candidatos de cena) + transcrição original pt-BR via Whisper.

---

## 1. Arquitetura do roteiro

O motor do vídeo é uma **corrente problema→solução→novo problema**. Cada nível resolve
uma limitação e, ao resolver, cria a limitação seguinte. Nunca há transição neutra.

| Nível | Resolve | Limitação que ele mesmo cria |
|---|---|---|
| 1. O agente / loop | Age sozinho rumo a um objetivo | "não conhece você, seu projeto, nem o jeito que você trabalha" |
| 2. Contexto (AGENTS.md) | Ensina quem você é | "não faz o agente lembrar do que você explicou ontem" |
| 3. Memória (MEMORY.md) | Acumula aprendizado entre sessões | "até agora ele não tocou em nada do lado de fora" |
| 4. Ferramentas (MCP + skills) | Deixa ele agir no mundo | "só que aonde que ele roda?" |
| 5. Autonomia | Persistência 24h | — (fecha com o passo a passo) |

As frases-dobradiça são quase idênticas e sempre começam com **"Só que"**:

- "Só que tem um problema, pessoal. Um agente loop, ele ainda é limitado."
- "Só que o contexto ele resolve só uma parte do problema, porque ainda falta outra."
- "Só que tem um teto nisso tudo."
- "Só que aonde que ele roda?"

**Espinha numerada:** 30 conceitos contados em voz alta ao longo do vídeo — "Seis, agentes MD",
"Oito. Agentes contra o GPT personalizado", "13. O loop de auto melhora", "No 15", "21.",
"No ponto 26", "30." A contagem dá sensação de progresso mensurável e é o que sustenta
a promessa do título ("30 conceitos") sem exigir capítulos.

## 2. Padrões retóricos recorrentes

**Desarme de jargão.** Introduz o termo assustador, encena o pânico do espectador, desarma
na mesma respiração:
> "e aí que a gente entra no quatro, o Harness. Meu Deus, que que é isso? Relaxa, é a plataforma onde o agente roda."

**Objeção encenada.** Ele fala a dúvida do espectador em primeira pessoa e responde:
> "Ah, não entendi."
> "E aí você fala: 'Ah, então os modelos fechados do chat GPT, do Cloud, do Gemini, eles são melhores?' Não, porque..."

**Analogia concreta para cada abstração** — nunca deixa um conceito só na definição:
- plataformas = carros, e "aqui nesse vídeo você tá aprendendo a dirigir"
- AGENTS.md = manual do funcionário no primeiro dia
- MEMORY.md = "o caderno do agente"
- MCP = tradutor entre línguas; "o MCP dá mãos pro seu agente abraçar tudo"
- skill = "procedimento salvo", o SOP digital

**Número como âncora de autoridade.** Regras com valor específico grudam mais que
princípios vagos: "no máximo ali 200 linhas, porque eu vejo muita gente enchendo esse
arquivo de 500, 600 linhas."

**Reframe econômico no hook.** Abre com deslocamento de dinheiro, não com tecnologia:
> "Antigamente uma pessoa fazia uma venda e ganhava uma comissão, só que agora o agente faz a venda e a comissão fica com o dono do agente."

**Vantagem não-copiável como clímax.** O ponto emocional mais alto do vídeo (09:00) não é
uma ferramenta, é uma posse: "Isso vai virar uma camada de conhecimento que é só sua.
E essa aqui é a parte mais importante, porque ninguém vai copiar."

## 3. Registro de fala

Oral, segunda pessoa do singular, marcadores de conversa em altíssima densidade:
`tá bom?` `beleza?` `né?` `se liga só` `bora` `relaxa` `presta atenção` `pessoal` `meus amigos`
`ó` `enfim` `sei lá`.

Frases curtas. Quase nenhuma subordinada longa. Quando o assunto fica técnico, ele quebra
em orações de 5–8 palavras separadas por pausa.

Auto-interrupção como recurso: começa uma frase, corta, reformula mais simples
("Existe um jeito organizado de entregar isso para ele organizado. Seis, agentes MD.").

Fecha blocos com pergunta de confirmação — `Já entendeu, né?` / `Beleza?` — que funciona
como respiro e marca fim de conceito.

## 4. Sistema visual

**Plano principal:** meio-primeiro plano, centralizado, microfone condensador grande e
deliberadamente visível na base do quadro. Camiseta lisa marrom/oliva. Vinheta escura nas bordas.

**Fundo:** gradiente radial pintado, luz atrás do apresentador. A cor **deriva ao longo do
vídeo** — laranja-amarelado (03:29), vermelho-laranja saturado (dominante), vinho escuro
(07:59). Não é fundo fixo: é luz colorida controlada, provavelmente RGB com difusão.

**Variação de escala como corte.** O mesmo setup aparece em enquadramentos diferentes
(mais aberto em 00:48, mais fechado em 17:33). Ele corta entre escalas para dar ritmo sem
mudar de cena — é o que evita o vídeo parecer estático em 19 minutos.

**Cartelas — o sistema tipográfico:**
- Nível: `NÍVEL 5` em sans-serif bold caixa alta, dentro de **caixa preenchida azul-petróleo
  com borda tracejada** (referência visual a caixa de seleção de ferramenta de design; a
  caixa tem um corte diagonal na base), com `A AUTONOMIA` abaixo em **serifada itálica**.
  Glifos de brilho de 4 pontas soltos ao redor. Fundo azul-marinho escuro, nunca laranja.
- Conceito: `Conceito 18.` em serifada itálica + `Os skills: o SOP digital` em sans-serif,
  ancorado no canto superior esquerdo, sobreposto ao plano do apresentador.

O par tipográfico **sans-serif bold + serifada itálica** é a assinatura da marca.

**Paleta — dois mundos, e essa é a decisão central do canal.**

Não existe uma paleta com acentos. Existem **duas paletas que nunca se misturam**:

| Mundo | Cor | O que aparece nele |
|---|---|---|
| **Quente** | Gradiente radial laranja→vermelho, centro quente atrás da cabeça, queda a preto nos cantos | **Só o apresentador.** Nada de gráfico entra aqui |
| **Frio** | Azul-marinho quase preto, com arcos amplos de brilho ao fundo; linha e ícone em ciano/turquesa com glow | **Toda a informação:** cartelas de nível, cartelas de conceito, diagramas, esquemas |

Gravação de tela é um terceiro registro, sempre em quadro cheio, sem tratamento.

O efeito é que **calor = pessoa, frio = informação**. O espectador sabe, antes de ler
qualquer coisa, se está recebendo opinião ou estrutura. É barato de reproduzir e é o que
mais separa esse canal de um vídeo comum de talking head.

**Transições:** whip-pan desfocado, vazamento de luz (light leak) colorido, flash branco.
Rápidas, quase subliminares.

**B-roll:** três tipos, alternados — imagem de banco (pessoas), UI de produto em fundo
desfocado colorido, e **captura de tela cheia do terminal** rodando Claude Code de verdade
(AGENTS.md sendo escrito, prompt real sendo digitado). A captura real é o que dá credibilidade.

## 5. Estrutura de CTA

- **Meio do vídeo, contextual** (14:25, ao citar o Hermes): "se você quiser um vídeo sobre ele, comenta aqui e deixa o like também" — pedido amarrado ao interesse imediato, não genérico.
- **Fechamento acionável antes do CTA final:** passo 1 / passo 2 / passo 3, com um freio explícito ("não tenta automatizar tudo de uma vez... faz uma skill por vez").
- **CTA final curto:** "se inscreve no canal, hype esse vídeo, deixa o like, muito obrigado. E se você quer aprender uma ferramenta nova, comenta aqui."

---

## Como esta análise foi corrigida

A primeira versão deste documento afirmava que a paleta base era laranja e que ciano/azul
eram "só cartelas de contraste". **Estava invertido.**

O erro veio de confiar nos rótulos `t=MM:SS` do relatório de frames da skill `/watch`.
Conferidos contra o ffmpeg, **eles não batem com o conteúdo**: o relatório dizia que
03:29 e 07:59 eram planos do apresentador em fundo laranja; o ffmpeg mostra um README e um
diagrama ciano nos mesmos instantes. O modo `--timestamps` da skill concorda com o ffmpeg;
o modo scene-change não.

Toda afirmação visual aqui foi refeita sobre amostragem uniforme com ffmpeg
(`ffmpeg -ss <seg> -i video.mp4 -frames:v 1`), que é verificável. Timestamps individuais
de plano foram removidos por não serem confiáveis.

**Regra que fica:** para análise visual em que o *quando* importa, extraia com ffmpeg
direto. Ver `ORIENTACAO-assistir-youtube.md`.

## Limitação desta análise

Tudo acima vem de **frames + texto**. A skill `/watch` extrai imagem e transcrição —
não analisa o áudio em si. Portanto **entonação, altura de voz, ritmo de fala, onde ele
enfatiza e como usa pausa não foram medidos**, apenas inferidos da pontuação e do
comprimento das frases. Para capturar entonação de verdade seria preciso análise de
áudio (prosódia), que nenhuma ferramenta instalada aqui faz hoje.
