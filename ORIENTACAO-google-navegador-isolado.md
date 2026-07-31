# Orientação: acessar ferramentas do Google pelo navegador isolado

Como um agente alcança NotebookLM, YouTube, Gemini, AI Studio e afins usando uma conta
de serviço, **sem nunca receber a senha** e sem interferir no navegador pessoal do usuário.

Verificado em 2026-07-31 com a conta `LAHQ Agents`.

---

## O problema que isto resolve

O usuário não quer logar e deslogar da conta de agentes no navegador dele o tempo todo.
E o agente **não digita senha em tela de login** — é limite fixo, não negociável por
contexto, ambiente privado ou autorização explícita.

A saída não é o agente ter a credencial. É o agente ter **acesso**, que é outra coisa.

## A solução: painel Browser do Claude Code

O painel Browser (`mcp__Claude_Browser__*`) é **um navegador separado, com perfil próprio**,
sem relação com o Chrome pessoal do usuário. Não confundir com `mcp__claude-in-chrome__*`,
que opera o Chrome real com as sessões pessoais já logadas.

Fluxo de configuração, feito **uma vez**:

1. O agente abre o painel numa página de login do Google:
   ```
   mcp__Claude_Browser__preview_start(url: "https://notebook.google.com")
   ```
2. **O usuário digita e-mail e senha ele mesmo**, dentro do painel.
3. A sessão fica nesse perfil isolado. O navegador pessoal não é tocado.

A partir daí a sessão é **compartilhada entre todos os serviços Google** naquele perfil —
logar uma vez libera NotebookLM, YouTube, Gemini e AI Studio de uma vez só.

---

## Estado verificado das ferramentas

| Ferramenta | URL | Estado |
|---|---|---|
| NotebookLM / Gemini Notebook | `notebook.google.com` | Funciona. `notebooklm.google.com` redireciona para cá |
| YouTube | `youtube.com` | Funciona. Histórico, inscrições e identidade da conta legíveis |
| Gemini | `gemini.google.com/app` | Funciona. Conta gratuita (aparece "Fazer upgrade"), modelo Flash |
| AI Studio | `aistudio.google.com` | Funciona. Playground e catálogo de modelos/agentes |
| Stitch | `stitch.withgoogle.com` | **Inconclusivo** — ver abaixo |

---

## Armadilhas

### 1. A primeira navegação pode ser negada — repita

O YouTube retornou `navigation to https://youtube.com was denied or failed` na primeira
tentativa e carregou normalmente na segunda, sem nenhuma mudança.

**Primeira negativa não é bloqueio, é ruído.** Mesmo padrão do HTTP 429 do `yt-dlp`.
Repita antes de concluir que não tem acesso.

### 2. Screenshot exige o painel visível; leitura de texto não

Com o painel oculto, `computer(action: "screenshot")` falha com:

```
Screenshot timed out after 5s: the Browser pane is not displayed,
so the page is not compositing frames.
```

Mas `get_page_text` e `read_page` **funcionam com o painel oculto**. Prefira sempre os dois
últimos: são mais baratos, mais confiáveis e não dependem de o painel estar exibido.
Só peça o painel visível quando precisar genuinamente enxergar algo visual.

### 3. SPA em canvas/WebGL volta vazia com o painel oculto

O Stitch autentica (o título resolve, não redireciona para login), mas `read_page` devolve
só `main > generic`, zero elementos interativos, mesmo após recarregar.

Provavelmente ele renderiza em canvas e não constrói árvore de acessibilidade — ou não
compõe frames com o painel oculto. **Não foi possível distinguir as duas hipóteses sem o
painel visível.** Se for depender do Stitch, teste com o painel exibido antes de assumir.

Sintoma geral a reconhecer: **página autenticada, título correto, árvore vazia.**

### 4. Este painel não faz upload de arquivo local

`mcp__claude-in-chrome__file_upload` **não tem equivalente** no painel Browser.

Consequência prática no NotebookLM: adicionar fonte por **URL, link de YouTube e "Copied
text" funciona**; subir arquivo do disco **não**. Se upload local for essencial, tem que
ser pelo Chrome real, com a conta pessoal — o que reintroduz o problema de login que esta
orientação existe para evitar.

Contorno: gerar o conteúdo e colar como "Copied text" em vez de subir arquivo. Costuma dar
resultado melhor de qualquer forma, porque a fonte vai curada em vez de crua.

---

## Mapeamento de ferramentas

A skill do NotebookLM foi escrita para o Chrome real. Para rodar no painel isolado,
troque os nomes:

| Skill do NotebookLM diz | No painel Browser use |
|---|---|
| `tabs_context_mcp` | `mcp__Claude_Browser__tabs_context` |
| `tabs_create_mcp` | `mcp__Claude_Browser__tabs_create` |
| `navigate` | `mcp__Claude_Browser__navigate` |
| `computer` | `mcp__Claude_Browser__computer` |
| `read_page` | `mcp__Claude_Browser__read_page` |
| `find` | `mcp__Claude_Browser__find` |
| `form_input` | `mcp__Claude_Browser__form_input` |
| `get_page_text` | `mcp__Claude_Browser__get_page_text` |
| `file_upload` | **não existe** |

Abas são independentes: crie várias com `tabs_create` e navegue em paralelo, uma chamada
por aba na mesma mensagem. Foi assim que as quatro ferramentas acima foram testadas de uma vez.

---

## Não resolvido

**A sessão sobrevive a reiniciar o Claude Code?** Ainda não testado. Se não sobreviver,
o usuário teria que logar a cada reinício e todo o ganho desta abordagem cai por terra.
**Confirme isto antes de montar qualquer rotina em cima deste caminho.**

## Fora de escopo para o agente

- Digitar senha em tela de login — sempre o usuário, sempre
- Criar conta
- Aceitar termos, consentimentos ou permissões OAuth sem pedido explícito do usuário

Gerar chave de API nessas ferramentas é possível e o usuário pode autorizar, mas trate
como decisão dele: chave criada é credencial nova no mundo, com custo e superfície de
risco próprios. Peça confirmação, e nunca escreva a chave em arquivo versionado.
