# Prompt de onboarding — skill /watch

Cole o bloco abaixo num chat que acabou de instalar o `watch@claude-video`.
É autossuficiente: não depende de clonar este repositório.

---

```text
Você acabou de instalar o plugin watch@claude-video. Antes de usar, leia isto:
a instalação funciona, mas erra em silêncio em quatro pontos.

PRIMEIRO: reinicie o Claude Code. O plugin só carrega em sessão nova, e o
processo atual ainda carrega o PATH antigo.

VERIFIQUE O SETUP:
  python "$env:USERPROFILE\.claude\plugins\cache\claude-video\watch\0.2.0\skills\watch\scripts\setup.py" --json
Você quer "status": "ready" e "missing_binaries": [].
No Windows use `python`, NUNCA `python3` (é o stub da Microsoft Store e não roda).
Se faltar yt-dlp mesmo depois do pip install, é PATH: o `pip install --user` joga o
exe em %APPDATA%\Roaming\Python\Python3XX\Scripts, que não está no PATH por padrão.

O QUE A SKILL FAZ: ela NÃO assiste vídeo. Extrai frames com ffmpeg + transcrição
(legenda ou Whisper) e entrega os dois; você faz a costura. Não há análise de áudio —
entonação, ritmo e ênfase ficam de fora.

AS QUATRO ARMADILHAS:

1) VÍDEO EM PORTUGUÊS VOLTA EM INGLÊS — a pior, porque parece sucesso.
   O yt-dlp pega a tradução automática e destrói os termos: "Claude" vira "cloud",
   "/watch" vira "barrawat". O Whisper NÃO salva: ele só entra quando não existe
   legenda nenhuma, então uma legenda ruim mas presente ganha calada.
   Confira antes:  yt-dlp --list-subs "<url>"
   Se houver pt-orig, baixe separado:
     yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "pt-orig" \
            --sub-format vtt -o "saida/v.%(ext)s" "<url>"

2) CADA LINHA VEM DUPLICADA — legenda rolante repete o cue anterior.
   Num vídeo de 19 min: 1708 cues viram ~570 linhas reais. Deduplique antes de ler.

3) OS TIMESTAMPS t=MM:SS DO RELATÓRIO NÃO SÃO CONFIÁVEIS.
   Verificado contra ffmpeg: o relatório dizia que 03:29 era o apresentador falando;
   era um README na tela. Erro sistemático. Use os frames como amostra do que EXISTE
   no vídeo, nunca para afirmar QUANDO algo aconteceu.
   Quando o "quando" importa:  ffmpeg -ss 209 -i video.mp4 -frames:v 1 saida.jpg

4) GRAVAÇÃO DE TELA MATA A SELEÇÃO DE FRAMES.
   Screencast de 10 min → 19 frames, com 4 minutos inteiros sem nenhum.
   Vídeo produzido de 19 min → 100 frames bem distribuídos.
   Aumentar --max-frames não resolve: o gargalo é a detecção, não o teto.
   Para screencast use --fps 0.2, ou leia a transcrição primeiro e peça frame nos
   momentos em que a pessoa aponta pra tela: --timestamps 4:32,7:10,9:55

429 / "Sign in to confirm you're not a bot": REPITA antes de complicar — costuma ser
transitório. Mas se o retry E um player_client alternativo falharem, é reputação de IP
(container/VPS levam bloqueio persistente; IP residencial não). Trocar de cliente não
resolve isso. Nesse caso priorize sessão de navegador real sobre o yt-dlp.

ARQUIVO LOCAL FUNCIONA DIRETO: passe o caminho no lugar da URL. Sem legenda, o Whisper
entra automático (~US$ 0,006/min; 19 min custou US$ 0,11).

NÃO TRUNQUE A SAÍDA: os caminhos dos frames ficam no cabeçalho e a transcrição no
rodapé. Se cortar com tail/Select-Object -Last, você perde os caminhos que precisa
para ler as imagens. Filtre com Select-String em vez de truncar.
```

---

## Se o repositório virar público

Dá para encurtar tudo isso para um link:

> Leia `ORIENTACAO-assistir-youtube.md` em https://github.com/LucianoAlf/yt-claude-brain
> antes de usar a skill `/watch`.

Comando para abrir: `gh repo edit LucianoAlf/yt-claude-brain --visibility public`

## Complemento

Se o agente for lidar com legenda com frequência, mande junto o
[`scripts/limpar-vtt.py`](scripts/limpar-vtt.py) — sem dependência externa, só stdlib.
