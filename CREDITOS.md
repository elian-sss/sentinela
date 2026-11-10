# Créditos

## Arte original

Herói, inimigos (lenhador, motosserrista), chefe (escavadeira), árvore sagrada e itens (`assets/personagens/`):
pixel art original, gerada por código pelo próprio projeto. Para gerar de novo: `python tools/gerar_personagens.py`
(requer Pillow e numpy).

Props coloridos do cenário (`assets/cenario/props/`: árvores com copa, açaizeiro, arbustos, samambaias,
flores, cogumelos e vitórias-régias): pixel art original, gerada por código pelo próprio projeto.
Para gerar de novo: `python tools/gerar_props.py` (requer Pillow e numpy).

## Áudio original

Todos os efeitos sonoros e músicas (`assets/audio/`) foram sintetizados por código pelo próprio projeto,
sem samples de terceiros. Para gerar de novo: `python tools/gerar_audio.py` (requer numpy, scipy e ffmpeg).

## Assets de terceiros (somente cenário)

### Dead Swamp

- **Autor:** Sevarihk (também assina como "Aurora")
- **URL:** https://sevarihk.itch.io/dead-swamp-tileset
- **Licença:** Creative Commons Attribution 4.0 International (CC-BY 4.0), conforme a página do pack,
  e os termos do `README.txt` do autor: uso comercial permitido, edição permitida, **crédito obrigatório**
  ("Sevarihk" ou "Aurora"), não apresentar os assets como próprios.
  Arquivo original dos termos: `assets/cenario/dead_swamp/README.txt`
- **Data de acesso:** 10/11/2026
- **Arquivos usados** (renomeados para nomes sem espaço; conteúdo original):
  - `dead_swamp_v4.png` ← `dead-swamp-v4.png` (chão de lama, árvores mortas, tronco quebrado, juncos, galhos)
  - `tree_trunk_swamp.png` ← `tree-trunk-swamp.png` (toco gigante, montes de raiz, folhinhas)
  - `dreck_auf_dreck.png` ← `dreck auf dreck.png` (terra da clareira)
  - `agua_pantano.png`: primeiro quadro recortado de `swamp-brühe animated-v5.png` (poças)
- **Onde:** `cenas/cenario/Cenario.tscn` (camadas `Chao` e `Decoracao`) e `cenas/cenario/cenario_tileset.tres`

**Crédito sugerido para a página do itch.io e para o jogo:**
"Cenário: Dead Swamp por Sevarihk (CC-BY 4.0) — https://sevarihk.itch.io/dead-swamp-tileset"
