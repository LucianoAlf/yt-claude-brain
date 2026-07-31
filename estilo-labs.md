# Estilo LABS — padrão extraído de 3 vídeos

| Vídeo | Duração | Tipo |
|---|---|---|
| Agentes de IA em 18 minutos (O que 95% não entendem) | 18:54 | aula |
| Aprenda tudo de Claude Code em 22 minutos | 22:02 | aula |
| O "Novo Funcionário" que me faz R$ 46K LUCRO por mês | 12:18 | caso/pitch |

**Método:** transcrição original `pt-orig` (nunca a tradução automática) limpa de duplicatas;
frames por amostragem uniforme com `ffmpeg -ss`, não por detecção de cena — os timestamps
do relatório scene-change da skill `/watch` não são confiáveis (ver
`ORIENTACAO-assistir-youtube.md`).

---

## 1. O que é invariável — e é aqui que mora a marca

**Só uma coisa se repete idêntica nos três vídeos: o plano do apresentador.**

- Gradiente radial laranja→vermelho, ponto quente atrás da cabeça, queda a quase preto nos cantos
- Camiseta lisa marrom/oliva, gola careca
- Microfone condensador grande, preto, centralizado na base do quadro — deliberadamente visível
- Meio-primeiro plano, centralizado, vinheta escura nas bordas
- Corte entre escalas (mais aberto / mais fechado) do mesmo setup, para dar ritmo sem trocar de cena

O gradiente laranja é o identificador dele. **Ele viaja junto:** no vídeo de Claude Code, quando
a tela vira screencast, o apresentador aparece num **PiP circular** — e dentro do círculo o
fundo laranja continua lá.

A saturação varia entre os vídeos (o de Claude Code puxa mais para o vermelho que o de
Agentes), mas o setup é o mesmo.

## 2. O que varia — a linguagem gráfica NÃO é fixa

Esta seção corrige a primeira versão deste documento, que a partir de **um único vídeo**
concluiu "quente = pessoa, frio = informação". **Com três vídeos essa regra cai.**

| Vídeo | Linguagem dos gráficos |
|---|---|
| Agentes | Azul-marinho quase preto, arcos de brilho, linha e ícone ciano com glow |
| R$ 46K | Marrom-escuro quente, caixas e setas coral/salmão, orbes suaves ao fundo |
| Claude Code | Ilustração isométrica 3D (PC lilás, bicho pixel-art coral) sobre grade turquesa |

Três vídeos, três mundos gráficos diferentes. A hipótese mais provável é que a paleta
**segue o assunto** — coral quando o tema é Claude (cor da marca Anthropic), ciano para
agentes em geral. Não dá para confirmar isso com três amostras, mas dá para afirmar o
essencial: **não existe um sistema gráfico fixo a copiar.** O que se copia é o plano dele.

## 3. Os três modos de tela

1. **Apresentador em quadro cheio** — no fundo laranja
2. **Gráfico/cartela em quadro cheio** — paleta livre por vídeo
3. **Gravação de tela** — sempre em quadro cheio ou com **PiP circular** do apresentador
   no canto inferior direito. Nunca dentro de moldura de navegador ou janela falsa.

O modo 3 domina o vídeo mais longo e mais didático (Claude Code, 22 min) — é o mais barato
de produzir e o que melhor sustenta duração.

## 4. Arquitetura de roteiro

**A dobradiça é "Só que".** Ele abre uma limitação e emenda na solução seguinte. Frequência
medida:

| Vídeo | Ocorrências | Por minuto |
|---|---|---|
| Claude Code (aula) | 41 | 1,9 |
| Agentes (aula) | 29 | 1,5 |
| R$ 46K (caso) | 6 | 0,5 |

**Nos vídeos de ensino a densidade é 3× a do vídeo de pitch.** Ou seja, "só que" não é vício
de fala — é o motor didático dele. Cada uso cria a próxima pergunta e impede o espectador
de sair.

Outros marcadores presentes nos **três**:

| Recurso | Agentes | R$46K | Claude Code |
|---|---|---|---|
| Objeção encenada ("Ah, não entendi") | 8 | 7 | 4 |
| Desarme ("relaxa", "calma", "meu Deus") | 5 | 1 | 6 |
| Analogia explícita ("é como se", "imagina") | 5 | 2 | 5 |
| Marcador oral ("tá bom?", "beleza?", "se liga", "bora") | 12 | 5 | 10 |

Espinha numerada (nível / etapa / passo) aparece forte nas duas aulas (13 e 11) e some no
vídeo de caso (2). É recurso de aula, não do canal.

## 5. A abertura tem sempre três tempos, em ~25 segundos

1. **Afirmação contraintuitiva** que contraria o senso comum
2. **Por que isso te afeta** — ou o obstáculo que faz as pessoas desistirem
3. **Promessa + desarme**

Verbatim dos três:

> "Todo mundo tá falando de agente, mas ninguém consegue explicar de um jeito simples. E isso
> é um problema, porque a próxima grande mudança da internet não vai ser um software que você
> assina, vai ser um agente que faz todo o trabalho por você. Como assim? **Se liga só.**"

> "As pessoas que mais estão fazendo dinheiro em 2026 não estão montando equipe gigante, elas
> estão criando sistemas com o Claude."

> "É uma das ferramentas mais poderosas que a humanidade já construiu. **Só que** ela assusta
> muita gente porque parece programação e muita gente desiste de entender. **Mas relaxa**, vou
> explicar."

## 6. O fechamento é fixo

Nos três: `se inscreve no canal` + `deixa o like` + `hype/hypa esse vídeo`. Dois de três
acrescentam `me segue no Instagram`. Um detalhe bom: *"Se você tá assistindo pela televisão,
pega o seu celular, se inscreve"* — remove o atrito de um contexto específico em vez de
pedir genericamente.

Nas aulas, antes do CTA vem um **fechamento acionável** (passo 1 / passo 2 / passo 3) com um
freio explícito: *"não tenta automatizar tudo de uma vez... faz uma skill por vez."*

---

## 7. O que dá para reproduzir, e com quê

**O plano do apresentador é físico, não é pós.** Luz RGB atrás e abaixo, apontada para
parede lisa, com a pessoa bem à frente para não projetar sombra. A queda a preto nos cantos
é só lei do inverso do quadrado. Câmera em meio-primeiro plano, mic condensador no quadro.

Nada disso se resolve em software — é luz, parede e enquadramento.

**Todo o resto é reproduzível em Remotion:** cartelas com borda tracejada, diagramas de
caixa e seta, ícones de linha com glow, brilhos de 4 pontas, PiP circular sobre screencast,
contadores numerados. É CSS e SVG animados por `useCurrentFrame`. Não exige After Effects.

**Não é possível determinar a ferramenta dele olhando o resultado** — render é render. O que
se afirma com segurança é que nenhum elemento observado exige AE.

**Do formato dele, o mais aproveitável para vídeo-aula é o modo 3** (screencast + PiP
circular): mais barato, aguenta duração longa e é o que ele usa justamente no vídeo mais
didático dos três.

## Limitação

Tudo aqui vem de **imagem e texto**. Entonação, altura de voz, ritmo de fala, ênfase e uso
de pausa **não foram medidos** — a skill `/watch` não analisa áudio. O registro escrito
(gírias, densidade de marcadores orais, comprimento de frase) esse sim está medido.
