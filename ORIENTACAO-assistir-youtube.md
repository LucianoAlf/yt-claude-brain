# Orientação: assistir vídeos do YouTube

Para agentes (Alfredo, Mike e outros) que vão usar a skill `/watch` do plugin
[`bradautomates/claude-video`](https://github.com/bradautomates/claude-video).

Este documento existe porque a instalação padrão **funciona, mas erra em silêncio** em
quatro pontos que só aparecem depois que você já confiou no resultado. Cada item abaixo
foi encontrado na prática, não copiado da documentação.

---

## O que a skill realmente faz

Ela **não** dá visão de vídeo. Ela quebra o vídeo em duas coisas que o modelo já
consegue processar:

1. **Frames** — JPEGs extraídos com ffmpeg, entregues como imagens para você ler com `Read`
2. **Transcrição** — legenda nativa do YouTube, ou Whisper API quando não há legenda

Você recebe as duas e faz a síntese. Não existe análise de áudio: **entonação, altura de
voz, ritmo e ênfase não são medidos.** Se te pedirem análise de prosódia, diga que não dá.

---

## Instalação

```bash
claude plugin marketplace add bradautomates/claude-video
claude plugin install watch@claude-video
```

Depois instale as duas dependências externas. No Windows:

```bash
winget install --id Gyan.FFmpeg --exact --silent --accept-source-agreements --accept-package-agreements
```

```bash
pip install --user --upgrade yt-dlp
```

Rode o setup uma vez para criar o arquivo de configuração:

```bash
python "$env:USERPROFILE\.claude\plugins\cache\claude-video\watch\0.2.0\skills\watch\scripts\setup.py"
```

Confirme com `setup.py --json`. Você quer ver `"status": "ready"` e `"missing_binaries": []`.

### Chave da OpenAI (para vídeos sem legenda)

Edite `~/.config/watch/.env` e preencha:

```
OPENAI_API_KEY=<a chave>
WATCH_DETAIL=balanced
SETUP_COMPLETE=true
```

**Whisper API não é Wispr Flow.** Wispr Flow é aplicativo de ditado (fala → texto ao vivo).
O que a skill chama é `api.openai.com/v1/audio/transcriptions`. Ter um não te dá o outro.

Custo real medido: **US$ 0,11 para transcrever 19 minutos** (whisper-1, ~US$ 0,006/min).

---

## As quatro armadilhas

### 1. Vídeo em português volta transcrito em inglês

**A pior delas, porque não dá erro.** O yt-dlp escolhe a faixa de legenda automaticamente
e frequentemente pega a **tradução automática para inglês**. O estrago é literal:
"Claude" vira "cloud", "/watch" vira "barrawat", "Ciência Todo Dia" vira "Science every day".

Whisper **não** te salva disso: ele só entra quando não existe legenda nenhuma. Uma legenda
ruim mas presente ganha em silêncio.

Antes de confiar em qualquer transcrição de vídeo em português, liste as faixas:

```bash
yt-dlp --list-subs "<url>"
```

Se aparecer `pt-orig` (Português Original), é essa que você quer. Baixe separado:

```bash
yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "pt-orig" --sub-format vtt -o "saida/video.%(ext)s" "<url>"
```

Depois confira qual arquivo caiu em `download/`. Se for `video.en.vtt` num vídeo em
português, a transcrição da skill está contaminada — descarte e use a que você baixou.

### 2. A legenda vem com cada linha duplicada

Legenda rolante do YouTube repete a linha anterior a cada cue. Um vídeo de 19 minutos
gera 204 KB de VTT com 1708 cues, dos quais só ~570 são conteúdo real.

Use `scripts/limpar-vtt.py` deste repositório:

```bash
python scripts/limpar-vtt.py entrada.vtt saida.txt
```

Ele remove as tags inline de karaokê, elimina repetições e agrupa em blocos de ~25s com
timestamp. No teste: 1708 cues → 570 linhas → 45 blocos → 4077 palavras.

### 3. Gravação de tela mata a seleção de frames

O modo `balanced` seleciona frames por mudança de cena. Screencast tem pouquíssima
variação entre quadros, então o detector passa fome. Números reais dos dois casos:

| Tipo de vídeo | Duração | Candidatos de cena | Frames obtidos |
|---|---|---|---|
| Tutorial gravação de tela | 10:42 | **19** | 19 |
| Vídeo produzido com b-roll | 18:54 | **440** | 100 |

No screencast a distribuição foi péssima: **4 minutos inteiros sem nenhum frame**, e
7 frames espremidos em 3 segundos. Aumentar `--max-frames` não resolve — o gargalo é a
detecção, não o teto.

Para screencast, force amostragem uniforme ou aponte os momentos:

```bash
python .../watch.py "<url>" --fps 0.2
```

```bash
python .../watch.py "<arquivo-local>" --timestamps 4:32,7:10,9:55
```

A segunda forma é a melhor: leia a transcrição primeiro, ache onde a pessoa diz
"olha aqui", "repara nisso", "como vocês podem ver", e peça frame naqueles instantes.
Aponta-se para a tela justamente quando a mudança visual é *baixa* — que é o caso que
o detector de cena perde.

### 3b. Os timestamps do relatório de scene-change não são confiáveis

**Descoberto em 2026-07-31, e já contaminou uma análise.**

O relatório do `watch.py` lista cada frame como `frame_0107.jpg (t=03:29, reason=scene-change)`.
**Esse `t=` pode não corresponder ao conteúdo do frame.** Conferido contra o ffmpeg no
vídeo `EzcXGtjNm5E`: o relatório dizia que 03:29 e 07:59 eram planos do apresentador; o
ffmpeg mostra um README e um diagrama nesses instantes. Erro sistemático, não pontual.

O modo `--timestamps` **é** confiável — bate com o ffmpeg. O modo scene-change não.

Consequência: dá para confiar nos frames como *amostra do que existe no vídeo*, mas **não
para afirmar quando cada coisa acontece**. Uma análise que cite momento fica errada.

Quando o *quando* importar, extraia direto:

```bash
ffmpeg -ss 209 -i video.mp4 -frames:v 1 -vf scale=768:-1 saida.jpg
```

Amostragem uniforme com ffmpeg também dá retrato mais honesto da mistura visual do vídeo
do que a seleção por cena, que enviesa para os trechos de mais movimento.

### 4. HTTP 429 do YouTube é normal — só repita

Você vai ver isto e vai parecer bloqueio definitivo:

```
ERROR: Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies
WARNING: HTTP Error 429: Too Many Requests
```

**Não vá atrás de cookies na primeira ocorrência.** Na prática é transitório: a mesma URL
funcionou na tentativa seguinte, sem nenhuma mudança. Repita antes de complicar.

**Mas repetir só resolve em máquina de IP residencial.** Veja a seção seguinte.

---

## O anti-bot depende do seu ambiente, não do vídeo

Esta é a diferença que mais confunde: **o mesmo vídeo pode funcionar num agente e falhar
noutro**, com a mesma versão do yt-dlp e a mesma configuração.

Caso medido em 2026-07-31, vídeo `2rdMEq3kr34`, yt-dlp 2026.07.04 nos dois lados:

| Ambiente | Resultado |
|---|---|
| Desktop Windows, IP residencial | Baixou. 429 transitório na primeira, sucesso na segunda |
| Container Linux como `root` (VPS) | Bloqueado. Retry falhou, `player_client=mweb` falhou |

**O YouTube pontua reputação de IP.** Faixa de datacenter recebe anti-bot persistente;
faixa residencial recebe no máximo um 429 passageiro. Trocar de `player_client` não
resolve isso, porque o problema não é o cliente — é de onde a requisição sai.

### Como saber em qual caso você está

Se o retry simples resolve, você está em IP residencial e a seção anterior basta.
Se o retry **e** um cliente alternativo falham, é reputação de IP. Pare de trocar cliente.

### O que fazer em ambiente bloqueado

Em ordem de custo crescente:

1. **Priorize sessão de navegador real, não o yt-dlp.** Um navegador logado costuma passar
   onde o yt-dlp não passa, porque ele *é* um navegador. Se o agente tem CDP ou painel de
   browser, buscar legenda por ali deve ser o **caminho primário** nesse ambiente, com o
   yt-dlp como reserva — o inverso do que faz sentido em máquina residencial.
2. **Habilite o solucionador de desafio JS.** O yt-dlp avisa que pulou os componentes
   remotos: `--remote-components ejs:github`. Em IP de datacenter os desafios JS aparecem
   muito mais, então isso pesa mais lá do que aqui.
3. **Cookies de uma conta dedicada de agentes** (`--cookies cookies.txt`). Nunca da conta
   pessoal: a conta usada pode ser sinalizada.
4. **Separe download de processamento.** Baixe onde funciona e passe os artefatos adiante.
   O `watch.py` aceita caminho de arquivo local, então frames e transcrição rodam em
   qualquer máquina depois.

### Regra de diagnóstico

**Chave de API resolvida não significa transcrição resolvida.** São dois gargalos distintos
em sequência: primeiro obter a mídia, depois transcrever. O Whisper só entra se houver
áudio baixado. Se o yt-dlp não baixa, a chave estar perfeita não muda nada — e é fácil
perder tempo depurando o lado errado.

---

## Detalhes de plataforma (Windows)

- **Use `python`, nunca `python3`.** No Windows `python3` é o stub da Microsoft Store e não executa o script. Toda a documentação da skill usa `python3` porque foi escrita para macOS/Linux.
- **`pip install --user` instala fora do PATH.** O `yt-dlp.exe` cai em `%APPDATA%\Roaming\Python\Python3XX\Scripts`, que normalmente não está no PATH. Adicione ao PATH do usuário ou o setup vai continuar reportando dependência faltando.
- **Reinicie o Claude Code depois de instalar.** O plugin só carrega em sessão nova, e o processo em execução ainda carrega o PATH antigo.
- **O aviso de permissão do `.env` é cosmético.** O hook roda `stat` pelo Git Bash, que não enxerga ACL do NTFS, então reclama `644` para sempre. Restrinja a ACL de verdade e ignore o aviso:
  ```bash
  icacls "%USERPROFILE%\.config\watch\.env" /inheritance:r /grant:r "%USERNAME%:(F)"
  ```

---

## Erro de operação: não trunque a saída

O `watch.py` imprime os **caminhos dos frames com timestamp** no cabeçalho do relatório,
e a transcrição inteira no rodapé. Se você cortar a saída com `tail`/`Select-Object -Last`,
perde exatamente os caminhos que precisa para ler as imagens.

Filtre em vez de truncar:

```bash
python .../watch.py "<url>" 2>&1 | Select-String -Pattern 't=|Frames:|Source:'
```

Em vídeo longo, rode em background e grave o relatório em arquivo.

---

## Receita completa para vídeo em português

1. `yt-dlp --list-subs "<url>"` — veja se existe `pt-orig`
2. Baixe `pt-orig` separado e limpe com `scripts/limpar-vtt.py`
3. Rode o `watch.py` para os frames (`--fps` baixo se for screencast)
4. Leia os frames com `Read`, em paralelo
5. Cruze frames × transcrição limpa e responda citando timestamps
6. Apague o diretório de trabalho — um vídeo de 19 min ocupa ~70 MB

## Escolha do modo

| Modo | Frames | Quando usar |
|---|---|---|
| `transcript` | 0 | Só o que foi dito. Nem baixa o vídeo se houver legenda. |
| `efficient` | até 50 | Extração quase instantânea. Em vídeo parado pode render *mais* frames que `balanced`. |
| `balanced` | até 100 | Padrão. Boa relação custo/fidelidade em vídeo produzido. |
| `token-burner` | ilimitado | Corte rápido, muita informação visual. Caro. |

Ordem de grandeza: 100 frames a 512px ≈ 20k tokens de imagem. Num vídeo de 19 minutos a
transcrição sozinha dá ~4 mil palavras — em vídeo longo **o texto costuma custar mais que
as imagens**.
