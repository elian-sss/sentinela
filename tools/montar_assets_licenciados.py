"""Monta os sprites de cenário, itens e da Samaúma a partir dos packs licenciados em assets/terceiros/.

Nada aqui é desenhado: cada sprite é um recorte dos originais, às vezes espelhado, recolorido
ou combinado com outro recorte (modificações permitidas pelas licenças, listadas em CREDITOS.md).

Originais (assets/terceiros/, ignorados pelo Godot por causa do .gdignore):
- sevarihk/: pixel art de Sevarihk, CC-BY 4.0 (OpenGameArt).
- db32_rpg_items/: "16x16 RPG Items (DB32)" de ARoachIFoundOnMyPillow, CC0 (OpenGameArt).

Saídas:
- assets/personagens/arvore_sagrada.png: a Samaúma em 3 quadros (saudável, ferida, quase seca).
- assets/interface/icone_samauma.png: retrato da Samaúma na moldura de madeira da interface.
- assets/personagens/item_*.png: ícones dos itens (20x20).
- assets/cenario/props/*.png: árvores, plantas, flores, cogumelos, vitórias-régias e o gramado.

Uso: python tools/montar_assets_licenciados.py (requer Pillow, numpy e scipy).
"""
import base64
import re
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

RAIZ = Path(__file__).resolve().parent.parent
TERCEIROS = RAIZ / "assets" / "terceiros"
PROPS = RAIZ / "assets" / "cenario" / "props"
PERSONAGENS = RAIZ / "assets" / "personagens"
INTERFACE = RAIZ / "assets" / "interface"

SELVA = TERCEIROS / "sevarihk" / "jungle-ruins_v3-2.png"
BAMBU = TERCEIROS / "sevarihk" / "bamboo-top_1.png"
FOLHAGEM = TERCEIROS / "sevarihk" / "jungle-foliage-ground1.png"
GRAMA = TERCEIROS / "sevarihk" / "dschungel-gras.png"
PALMEIRA = TERCEIROS / "sevarihk" / "palme-animation1.png"
ITENS = TERCEIROS / "db32_rpg_items" / "db32rpgitems_packed.png"

# Recortes (x0, y0, x1, y1) nos originais.
SAMAUMA = (17, 625, 180, 831)
ACACIA = (26, 1272, 151, 1401)
CHORAO = (161, 1317, 256, 1439)
ARVORE_PEQUENA = (169, 1739, 247, 1831)
REGIA_GRANDE = (100, 1866, 159, 1918)
REGIA_PEQUENA = (64, 1858, 96, 1888)
MONSTERA = (9, 1209, 60, 1248)
PALMEIRA_QUADRO = (45, 13, 206, 140)
TILE_AVULSO = (0, 0, 32, 32)  # o tile de amostra no canto dos autotiles
BASE_PALMEIRA = 46  # x da base do tronco no quadro da palmeira

# Ícones da folha DB32 (coluna, linha), quadros de 16x16.
ICONE = {
    "maca": (9, 2), "flor_rosa": (5, 6), "flor_branca": (6, 6), "flor_roxa": (7, 6),
    "erva": (8, 6), "pena": (3, 6), "escudo": (10, 11), "pocao_vermelha": (1, 11),
    "cogumelo": (8, 7),
}

QUADRO_SAMAUMA = (168, 212)
TAMANHO_ITEM = 20
TAMANHO_ARENA = (1152, 648)
TILE = 32
FOLGA_CLAREIRA = 22  # px que o buraco da grama avança além da terra da clareira
FOLGA_POCA = -4  # negativo: a grama cobre os cantos das poças, que ficam redondas


# ------------------------------------------------------------------ utilidades

def abrir(caminho):
    return Image.open(caminho).convert("RGBA")


def recortar(imagem, caixa):
    """Recorta e apara as bordas transparentes."""
    pedaco = imagem.crop(caixa)
    return pedaco.crop(pedaco.getbbox())


def icone(nome):
    coluna, linha = ICONE[nome]
    return abrir(ITENS).crop((coluna * 16, linha * 16, coluna * 16 + 16, linha * 16 + 16))


def centralizar(img, largura, altura, base=True):
    """Põe a imagem numa tela maior, centralizada na horizontal e apoiada na base (ou no meio)."""
    tela = Image.new("RGBA", (largura, altura))
    y = altura - img.height if base else (altura - img.height) // 2
    tela.alpha_composite(img, ((largura - img.width) // 2, y))
    return tela


def salvar(img, caminho):
    img.save(caminho)
    print(f"{caminho.relative_to(RAIZ)}  {img.size[0]}x{img.size[1]}")


# ------------------------------------------------------------------ Samaúma

def mascara_folhas(px):
    r, g, b = (px[..., i].astype(int) for i in range(3))
    return (px[..., 3] > 0) & (g > r + 15) & (g >= b)


def ruido(altura, largura, escala, semente):
    rng = np.random.default_rng(semente)
    pequeno = rng.random((altura // escala + 2, largura // escala + 2))
    return ndimage.zoom(pequeno, escala, order=1)[:altura, :largura]


def samauma_estado(arvore, perda, cor_seca, mistura):
    """Copa mais rala (perda de 0 a 1) e folhas puxando para a cor seca."""
    px = np.array(arvore).astype(float)
    folhas = mascara_folhas(px.astype(np.uint8))
    caindo = folhas & (ruido(px.shape[0], px.shape[1], 6, 21) < perda)
    luz = (0.3 * px[..., 0] + 0.59 * px[..., 1] + 0.11 * px[..., 2]) / 160.0
    seca = luz[..., None] * np.array(cor_seca, float)
    px[folhas, :3] = px[folhas, :3] * (1 - mistura) + seca[folhas] * mistura
    px[caindo, 3] = 0
    return Image.fromarray(px.clip(0, 255).astype(np.uint8))


def samauma():
    arvore = recortar(abrir(SELVA), SAMAUMA)
    estados = [
        arvore,
        samauma_estado(arvore, 0.2, (150, 160, 60), 0.45),
        samauma_estado(arvore, 0.42, (150, 110, 50), 0.85),
    ]
    largura, altura = QUADRO_SAMAUMA
    folha = Image.new("RGBA", (largura * 3, altura))
    for i, estado in enumerate(estados):
        folha.alpha_composite(centralizar(estado, largura, altura), (i * largura, 0))
    salvar(folha, PERSONAGENS / "arvore_sagrada.png")
    icone_samauma(arvore)


def icone_samauma(arvore):
    """Troca só o miolo do retrato antigo pela Samaúma reduzida, mantendo a moldura da interface."""
    caminho = INTERFACE / "icone_samauma.png"
    retrato = np.array(abrir(caminho))
    lado = retrato.shape[0]
    ys, xs = np.mgrid[:lado, :lado]
    centro = (lado - 1) / 2
    miolo = (xs - centro) ** 2 + (ys - centro) ** 2 <= (lado / 2 - 5) ** 2
    reduzida = arvore.resize((int(arvore.width * 38 / arvore.height), 38), Image.LANCZOS)
    alfa = np.array(reduzida)[..., 3]
    reduzida.putalpha(Image.fromarray(np.where(alfa > 100, 255, 0).astype(np.uint8)))
    fundo = Image.new("RGBA", (lado, lado), (34, 74, 50, 255))
    fundo.alpha_composite(reduzida, ((lado - reduzida.width) // 2, lado - 4 - reduzida.height))
    novo = np.array(fundo)
    retrato[miolo] = novo[miolo]
    salvar(Image.fromarray(retrato), caminho)


# ------------------------------------------------------------------ itens

def itens():
    escolhas = {
        "fruta": icone("maca"),
        "erva": icone("erva"),
        "escudo": icone("escudo"),
        "velocidade": icone("pena"),
        "forca": icone("pocao_vermelha"),
    }
    for nome, img in escolhas.items():
        salvar(centralizar(img, TAMANHO_ITEM, TAMANHO_ITEM, base=False), PERSONAGENS / f"item_{nome}.png")


# ------------------------------------------------------------------ props

def palmeira():
    """Primeiro quadro da palmeira animada, com a sombra cinza do original virando sombra translúcida
    e a base do tronco no centro da imagem (o cenário apoia cada prop pelo centro da base)."""
    px = np.array(recortar(abrir(PALMEIRA), PALMEIRA_QUADRO))
    r, g, b = (px[..., i].astype(int) for i in range(3))
    sombra = (px[..., 3] > 0) & (abs(r - g) < 8) & (abs(g - b) < 8)
    px[sombra] = (0, 0, 0, 70)
    img = Image.fromarray(px)
    largura = 2 * max(BASE_PALMEIRA, img.width - BASE_PALMEIRA)
    tela = Image.new("RGBA", (largura, img.height))
    tela.alpha_composite(img, (largura // 2 - BASE_PALMEIRA, 0))
    return tela


def props():
    selva = abrir(SELVA)
    salvar(recortar(selva, ACACIA), PROPS / "arvore_frondosa.png")
    salvar(recortar(selva, ARVORE_PEQUENA), PROPS / "arvore_pequena.png")
    salvar(recortar(selva, CHORAO), PROPS / "arvore_chorona.png")
    salvar(palmeira(), PROPS / "palmeira.png")
    salvar(recortar(abrir(BAMBU), TILE_AVULSO), PROPS / "arbusto.png")
    salvar(recortar(abrir(FOLHAGEM), TILE_AVULSO), PROPS / "folhagem.png")
    salvar(recortar(abrir(GRAMA), TILE_AVULSO), PROPS / "touceira.png")
    salvar(recortar(selva, MONSTERA), PROPS / "folhas_largas.png")
    salvar(icone("flor_rosa"), PROPS / "flores_rosas.png")
    salvar(icone("flor_branca"), PROPS / "flores_brancas.png")
    salvar(icone("flor_roxa"), PROPS / "flores_roxas.png")
    salvar(icone("cogumelo"), PROPS / "cogumelos.png")
    salvar(recortar(selva, REGIA_GRANDE), PROPS / "vitoria_regia.png")
    salvar(recortar(selva, REGIA_PEQUENA), PROPS / "vitoria_regia_pequena.png")


# ------------------------------------------------------------------ gramado

def celulas_do_chao():
    """Lê o TileMap do Cenario.tscn: célula -> id da fonte (0 lama, 1 terra da clareira, 2 poça)."""
    texto = (RAIZ / "cenas" / "cenario" / "Cenario.tscn").read_text(encoding="utf8")
    dados = base64.b64decode(re.search(r'tile_map_data = PackedByteArray\("([^"]+)"', texto).group(1))
    celulas = {}
    for i in range(2, len(dados), 12):
        x, y, fonte = struct.unpack("<hhH", dados[i:i + 6])
        celulas[(x, y)] = fonte
    return celulas


def areas_sem_grama():
    """Retângulos (em pixels) de cada mancha de terra ou poça do TileMap, com a fonte dela."""
    celulas = celulas_do_chao()
    largura = max(x for x, _ in celulas) + 1
    altura = max(y for _, y in celulas) + 1
    fonte = np.zeros((altura, largura), int)
    for (x, y), id_fonte in celulas.items():
        fonte[y, x] = id_fonte
    rotulos, _ = ndimage.label(fonte > 0)
    areas = []
    for fatia in ndimage.find_objects(rotulos):
        ys, xs = fatia
        areas.append((fonte[fatia].max(), (xs.start * TILE, ys.start * TILE, xs.stop * TILE, ys.stop * TILE)))
    return areas


def gramado():
    """Cobre a arena com o tile de grama do meio do autotile (espelhado ao acaso para não repetir)
    e abre buracos redondos na clareira e nas poças, com uma sombra úmida na borda da grama."""
    rng = np.random.default_rng(16)
    tile = abrir(GRAMA).crop((TILE, 2 * TILE, 2 * TILE, 3 * TILE))
    variacoes = [tile, tile.transpose(Image.FLIP_LEFT_RIGHT), tile.transpose(Image.FLIP_TOP_BOTTOM),
                 tile.transpose(Image.ROTATE_180)]
    largura, altura = TAMANHO_ARENA
    imagem = Image.new("RGBA", (largura, altura))
    for y in range(0, altura, TILE):
        for x in range(0, largura, TILE):
            imagem.alpha_composite(variacoes[rng.integers(len(variacoes))], (x, y))

    ys, xs = np.mgrid[0:altura, 0:largura].astype(float)
    irregular = (ruido(altura, largura, 10, 7) - 0.5) * 0.25
    sem_grama = np.zeros((altura, largura), bool)
    for id_fonte, (x0, y0, x1, y1) in areas_sem_grama():
        folga = FOLGA_CLAREIRA if id_fonte == 1 else FOLGA_POCA
        rx, ry = (x1 - x0) / 2 + folga, (y1 - y0) / 2 + folga
        distancia = np.hypot((xs - (x0 + x1) / 2) / rx, (ys - (y0 + y1) / 2) / ry)
        sem_grama |= distancia < 1 + irregular

    px = np.array(imagem).astype(float)
    borda = ndimage.binary_dilation(sem_grama, iterations=3) & ~sem_grama
    px[borda, :3] *= 0.65
    px[sem_grama, 3] = 0
    salvar(Image.fromarray(px.astype(np.uint8)), PROPS / "gramado.png")


def main():
    samauma()
    itens()
    props()
    gramado()


if __name__ == "__main__":
    main()
