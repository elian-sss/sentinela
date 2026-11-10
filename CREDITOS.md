# Créditos

## Arte original

Herói, inimigos (lenhador, motosserrista, fogo), chefe (escavadeira), árvore sagrada e itens: arte original do autor do jogo.

## Áudio original

Todos os efeitos sonoros e músicas (`assets/audio/`) foram sintetizados por código pelo próprio projeto,
sem samples de terceiros. Para gerar de novo: `python tools/gerar_audio.py` (requer numpy, scipy e ffmpeg).

## Assets de terceiros (somente cenário)

### Tiny Town

- **Autor:** Kenney (www.kenney.nl)
- **URL:** https://kenney.nl/assets/tiny-town
- **Versão:** 1.1
- **Licença:** Creative Commons Zero (CC0 1.0), domínio público. Crédito não obrigatório.
  Arquivo original da licença: `assets/cenario/kenney_tiny_town/License.txt`
- **Data de acesso:** 10/11/2026
- **Arquivos usados:** `assets/cenario/kenney_tiny_town/tilemap_packed.png` (tilemap 16x16 com chão de grama e terra, arbustos, pinheiros, pedras, broto, tronco, cerca, barril e poço)
- **Onde:** `cenas/cenario/Cenario.tscn` (camadas `Chao` e `Decoracao`) e `cenas/cenario/cenario_tileset.tres`
