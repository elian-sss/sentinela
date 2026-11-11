# Créditos

## Arte original

Herói, inimigos (lenhador, motosserrista) e chefe (escavadeira) (`assets/personagens/heroi.png`,
`lenhador.png`, `motosserrista.png`, `escavadeira.png`, `golpe.png`): pixel art original, gerada por código
pelo próprio projeto. Para gerar de novo: `python tools/gerar_personagens.py` (requer Pillow e numpy).

Interface e fonte (`assets/interface/`, `assets/fontes/`): geradas por código pelo próprio projeto
(`tools/gerar_interface.py` e `tools/gerar_fonte.py`). O miolo do `icone_samauma.png` é a Samaúma do pack
de Sevarihk reduzida (veja abaixo).

## Áudio original

Todos os efeitos sonoros e músicas (`assets/audio/`) foram sintetizados por código pelo próprio projeto,
sem samples de terceiros. Para gerar de novo: `python tools/gerar_audio.py` (requer numpy, scipy e ffmpeg).

## Assets de terceiros (cenário, props e itens)

O regulamento (regra 1) permite assets licenciados para cenário, props e tilemaps. Os originais baixados
ficam em `assets/terceiros/` (com `.gdignore`, então o Godot não os importa nem exporta). Os sprites usados
no jogo são recortes desses originais, montados por `python tools/montar_assets_licenciados.py`
(requer Pillow, numpy e scipy).

### Dead Swamp (Sevarihk)

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

### Assets de selva (Sevarihk)

- **Autor:** Sevarihk ("Aurora")
- **Licença:** CC-BY 4.0 (https://creativecommons.org/licenses/by/4.0/), crédito obrigatório
- **Data de acesso:** 11/11/2026
- **Originais** (em `assets/terceiros/sevarihk/`, com o nome original):
  - `jungle-ruins_v3-2.png`, do "Aztec Tileset": https://opengameart.org/content/aztec-tileset
  - `dschungel-gras.png`, `jungle-foliage-ground1.png` e `bamboo-top_1.png`, do "Ground and foliage autotiles":
    https://opengameart.org/content/ground-and-foliage-autotiles
  - `palme-animation1.png`, do "Animated Palm Tree Sprite": https://opengameart.org/content/animated-palm-tree-sprite
- **Onde e com quais modificações:**
  - Samaúma (`assets/personagens/arvore_sagrada.png`): a árvore grande do `jungle-ruins_v3-2.png`. O quadro 1
    é o original. Nos quadros 2 e 3 (árvore ferida e quase seca), parte das folhas foi apagada e as folhas
    foram recoloridas para verde-oliva e marrom.
  - Retrato da Samaúma (`assets/interface/icone_samauma.png`): a mesma árvore, reduzida.
  - Props (`assets/cenario/props/`): `arvore_frondosa`, `arvore_pequena`, `arvore_chorona`, `folhas_largas`,
    `vitoria_regia` e `vitoria_regia_pequena` são recortes do `jungle-ruins_v3-2.png`. `arbusto`, `folhagem` e
    `touceira` são os tiles de amostra dos autotiles. `palmeira` é o primeiro quadro da palmeira animada, com
    a sombra cinza trocada por uma sombra translúcida.
  - Gramado (`assets/cenario/props/gramado.png`): o tile de grama do `dschungel-gras.png` repetido
    (espelhado ao acaso), com buracos redondos na clareira e nas poças e a borda escurecida.

### 16x16 RPG Items (DB32)

- **Autor:** ARoachIFoundOnMyPillow
- **URL:** https://opengameart.org/content/16x16-rpg-items-db32
- **Licença:** CC0 (domínio público; crédito não obrigatório, mas dado mesmo assim)
- **Data de acesso:** 11/11/2026
- **Original:** `assets/terceiros/db32_rpg_items/db32rpgitems_packed.png`
- **Onde:** ícones dos itens (`assets/personagens/item_*.png`: maçã, erva, escudo, pena e poção vermelha,
  centralizados num quadro de 20x20) e as flores e o cogumelo do cenário (`flores_rosas`, `flores_brancas`,
  `flores_roxas`, `cogumelos`)

**Crédito sugerido para a página do itch.io:**
"Cenário, plantas e Samaúma: Dead Swamp, Aztec Tileset, Ground and Foliage Autotiles e Animated Palm Tree,
por Sevarihk (CC-BY 4.0) — https://sevarihk.itch.io e https://opengameart.org/users/sevarihk.
Itens: 16x16 RPG Items (DB32), por ARoachIFoundOnMyPillow (CC0)."
