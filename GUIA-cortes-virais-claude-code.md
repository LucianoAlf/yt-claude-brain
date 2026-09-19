# Cortes virais de podcast, editados no Claude Code

Guia operacional reconstruído do vídeo **"Como Editar um Reel Viral 100% no Claude Code"**
(canal LABS, 23:08, publicado em 03/09/2026 — `youtu.be/PE3cVKctDUI`).

Método de verificação: legenda `pt-orig` completa (711 falas, 4.987 palavras) + frames
extraídos por `ffmpeg` para conferir cada nome de ferramenta, skill e caminho de pasta.
Onde o texto abaixo cita um nome exato, ele foi **lido no frame**, não na legenda —
a legenda erra sistematicamente os nomes próprios (ver a última seção).

---

## O que o método é, em uma frase

Você não gera vídeo com IA. Você gera **imagens estáticas** com o Higgsfield e deixa o
**Claude montar e animar** o vídeo a partir delas. É isso que torna o processo barato:
gerar vídeo direto no Higgsfield é o que queima crédito.

---

## Ferramentas

| Ferramenta | Papel | Observação |
|---|---|---|
| **Claude app de desktop** | onde tudo acontece | precisa ser o app instalado — ele acessa arquivos locais |
| **Claude Code** (dentro do app) | o editor que corta e monta | a aba Chat não serve: não trabalha dentro de uma pasta |
| **Higgsfield** | gera os assets estáticos | pago; conecta por MCP |
| Transcritor de YouTube com timestamp | produz a decupagem | ele censura a tela — o link fica na descrição do vídeo |
| Baixador de vídeo do YouTube | pega o bruto | também censurado, mesma razão |

**Duas skills, feitas por ele, gratuitas (link na descrição):**

- **`corte-viral`** — decupagem com timing por palavra, identificação dos trechos que
  funcionam fora de contexto, corte com in/out preciso, enquadramento vertical com
  locutor ativo. **Não faz legenda nem motion.**
- **`motion-vox`** — recebe o vertical limpo da primeira e faz legenda + motion design.

As duas são encadeadas: quando a `corte-viral` termina, ela mesma chama a `motion-vox`.

> Resumo da descrição da `corte-viral`, lida no frame em 03:59: transforma vídeo longo
> (podcast, entrevista, live, aula) em clipes verticais 9:16 para Shorts, Reels e
> TikTok, e deixa legenda e motion explicitamente para a `motion-vox`.

---

## Bloco 1 — Preparação

1. **Escolha o podcast.** No YouTube: pesquise o canal → **Filtros → ordenar por
   popularidade** → mas procure um que também seja **recente**. Ele usou um episódio do
   Flow Podcast com o time do G4 (Tallis Gomes).

2. **Transcreva com timestamp ligado.** Cole o link do vídeo no transcritor e **ative a
   opção de timestamps**. Isso não é detalhe: o timestamp é o que permite ao Claude
   localizar o momento exato de cada fala no arquivo de vídeo.

3. **Salve a transcrição em arquivo.** Um `.txt`, `.vtt` ou `.rtf` — no vídeo aparecem
   `flow605.vtt` e `roteiro-podcast-fow.rtf`.

4. **Baixe o vídeo** e crie a pasta de trabalho. Ele chamou de `CLIPPER`. O vídeo bruto e
   a transcrição vão para dentro dela.

5. **Abra o Claude Code** e **selecione essa pasta** (ícone de pasta). Tudo que estiver
   lá dentro o Claude passa a enxergar.

---

## Bloco 2 — Cortar

6. **Instale a skill.** No app: **Personalizar → Habilidades → Adicionar → Fazer upload
   de habilidade**. Aceita um `.md` com nome e descrição em YAML, ou um `.zip`/`.skill`
   contendo um `SKILL.md`. Passa por uma verificação de segurança de 1–2 minutos.

7. **Confira que instalou:** digite `/` e as duas devem aparecer — `corte-viral` e
   `motion-vox`. Use só a primeira agora; a segunda é a fase final.

8. **Converta a transcrição em JSON.** Este é o passo de custo. Peça ao Claude para
   transformar a transcrição em um arquivo JSON — é um arquivo pequeno, e é sobre ele que
   o Claude trabalha para separar os melhores momentos.

   > **A versão melhor deste passo** ele só ensina no fim do vídeo, no bloco 4: em vez de
   > colar a transcrição no chat, **salve como arquivo dentro da pasta do projeto e
   > referencie com `@`**. Colar joga milhares de tokens para dentro do contexto; o
   > arquivo é lido como consulta. Use essa forma desde o começo.

9. **Resultado:** ele devolveu **16 cortes** de um podcast de mais de 3 horas, cada um com
   o timestamp de início e uma etiqueta de contexto — *história pessoal*, *sobre dinheiro*,
   *pergunta rápida*.

10. **Mande cortar.** Prompt literal: *"Tá bom, vamos cortar o vídeo"*. Ele cria a
    estrutura do projeto e começa a entregar os cortes um a um.

11. A skill instala **duas extensões** que ensinam o editor a identificar o rosto e
    seguí-lo, para o locutor não sair do enquadramento vertical.

12. **Faça a seleção humana.** Ele escolheu **3 dos 16**. Jogue os escolhidos numa pasta
    `preview` dentro do projeto.

13. **Prompt de refino** (o que ele mandou, em essência):
    *afine mais os hooks, porque alguns começam meio sem sentido; deixa os vídeos na
    vertical; dá uma leve decupada.*

14. **Corrigir defeito:** descreva em uma frase — *"evite deixar a tela dividida desse
    jeito"*. Quando o defeito é visual e difícil de descrever, **tire um print e cole no
    Claude** (foi assim que ele resolveu o rosto do segundo participante sendo cortado —
    a detecção tinha travado só no primeiro).

---

## Bloco 3 — Motion design

15. **Conecte o Higgsfield.** Em `higgsfield.ai/mcp`, aba **Claude Code**. Duas rotas:

    **Rota CLI** — copie e mande este prompt para o Claude Code (texto literal da página):
    ```
    Set up Higgsfield for me so I can generate images and videos from here.
    1. Install the CLI: run `npm i -g @higgsfield/cli`.
    2. Authenticate: run `higgsfield auth login` and complete the sign-in in the browser it opens.
    3. Install the companion skills: run `npx skills add higgsfield-ai/skills`.
    Once that's done, let me know when it's ready.
    ```

    **Rota conector (mais fácil)** — **Personalizar → Conectores → Adicionar → Adicionar
    conector personalizado**, cole a URL da aba "Claude" e dê o nome Higgsfield.

    Depois, faça um pedido simples de imagem: abre a tela de autorização, você clica em
    **Autorizar**. Para chamá-lo depois, basta citar o nome dele no prompt.

16. **Defina o estilo da legenda por referência visual.** Ele foi ao **Pinterest**,
    pesquisou **"Motion Design Captions"**, salvou vários prints dos estilos que gostou e
    mandou para o Claude dizendo que queria exatamente aquilo.

17. **Prompt de planejamento** (essência do que ele mandou):
    *agora vamos planejar um por um para criar o motion design; é importante criar os
    caracteres, a representação das pessoas e a representação das situações, para as
    pessoas conseguirem entender.*

18. **O que acontece:** o Higgsfield gera os assets (um caderno, um livro, um carro, um
    teclado, um relógio, uma imagem de fundo) e **o Claude monta a cena e anima**.

19. **Estrutura que ele cria** — conferida no Finder em 13:20, dentro de `CLIPPER`:
    ```
    CLIPPER/
      clipes-verticais/     ← os cortes aprovados
      motion/
      runs/
      flow605.vtt           ← a transcrição
      TALLIS + ALF...mp4    ← o vídeo bruto
    ```
    Dentro de `motion/` há **uma pasta por vídeo**, e dentro de cada uma: as fontes, o
    estilo, os `assets` e as `transições`.

20. **Loop de correção.** Quando um texto ficou ilegível (amarelo sobre fundo claro), ele
    disse ao Claude que *tudo precisa ter contraste* e sugeriu vermelho. A observação dele
    sobre isso é o ponto central do método:

    > A skill é um manual. Depois que a IA passa por ela, ela faz o que está na skill —
    > mas conforme você vai usando, ela se adapta e vai adicionando coisas. Não se
    > contente com os defeitos; vá corrigindo.

---

## Bloco 4 — Distribuição em massa

21. **Valide os 3 testes com o Claude.** A partir daí ele entende, com base nas suas
    escolhas, o que é bom e o que é ruim — **e adapta a própria skill**.

22. **Para cada novo podcast, o ciclo curto:**
    - copie o link → transcreva (com timestamp) → salve o arquivo **dentro da pasta do
      projeto**
    - baixe o vídeo para uma subpasta `bruto/`
    - no Claude Code: `/corte-viral` + `@` + selecione o arquivo da transcrição

23. **A segunda rodada é muito mais barata.** No segundo projeto ele mostra que o Claude
    criou um arquivo `.md` de regras e trabalhou muito mais rápido, gastando bem menos
    token. A explicação dele: **a primeira rodada é cara de propósito** — é onde a IA
    aprende os padrões. Depois disso, o processo fica leve.

**Custo que ele declara:** 30 créditos Higgsfield para os cortes, 50 créditos para montar
um vídeo com motion. (Números afirmados por ele; não verificáveis pelo vídeo.)

---

## O que ele não mostra

- **A ferramenta de transcrição** e **o baixador de vídeo** — ele censura as duas telas
  dizendo que o YouTube não permite. Os links ficam na descrição do vídeo.
- **O conteúdo das skills.** Elas são distribuídas prontas pelo link da descrição. O que
  dá para recuperar do vídeo é a descrição da `corte-viral` (citada acima) e o
  encadeamento entre as duas — suficiente para reescrever equivalentes do zero.

## Defeitos que apareceram no processo dele

Todos foram resolvidos conversando, mas vale saber que aparecem: tela dividida sem
sentido numa transição; rosto do segundo participante cortado no enquadramento; glitch na
transição entre duas cenas de motion; assets gerados sem fundo transparente (não-PNG).

---

## Erros da legenda automática (importante)

A legenda `pt-orig` deste vídeo tem erro de reconhecimento de fala, não de tradução — e
erra justamente os nomes próprios que você precisa acertar para reproduzir o método:

| Na legenda | É na verdade |
|---|---|
| cloud, Cláudio | **Claude** |
| Hixfield, Hickfield, Higsfield, Rigsfield, Heckfield, Hitsfield | **Higgsfield** |
| Thales, Tales | **Tallis** (Gomes) — confirmado pelo nome do arquivo no Finder |
| JZON | **JSON** |
| Hul | **hook** |
| El Musk, Elan Musk, Ilan Musk, Willam Musk | **Elon Musk** |
| Space Sex | **SpaceX** |
| Jet Vargas | **Getúlio Vargas** |
| assete | **asset** |
| piquezão | **PIX** |

Se você for pedir para um agente ler a transcrição bruta, avise disso — senão ele instala
"Hickfield".
