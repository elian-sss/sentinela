"""Gera a fonte pixel do Sentinela (arte original do projeto), com os acentos do português.

Saída: assets/fontes/sentinela_pixel.ttf
Para gerar de novo: python tools/gerar_fonte.py (requer fontTools; Pillow só para a prévia opcional).

Cada letra é desenhada numa grade: 7 linhas da altura das maiúsculas até a linha de base,
mais 2 linhas abaixo para as descendentes (g, j, p, q, y). Os acentos são montados por código
em cima das letras. 1 pixel da grade = 100 unidades, e o "em" tem 8 pixels: no Godot, use
tamanhos múltiplos de 8 (16, 24, 32, 48, 64) para a fonte ficar nítida.
"""

import os
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

RAIZ = os.path.join(os.path.dirname(__file__), "..")
DESTINO = os.path.join(RAIZ, "assets", "fontes", "sentinela_pixel.ttf")

PIXEL = 100
PIXELS_POR_EM = 8
LINHA_DE_BASE = 7  # quantas linhas ficam acima da linha de base
SUBIDA = 10  # linhas acima da base reservadas (7 da letra + 3 para acentos de maiúsculas)
DESCIDA = 2
LARGURA_ESPACO = 3

# ------------------------------------------------------------------ desenhos
# '#' é pixel aceso. As linhas extras (8ª e 9ª) são as descendentes.

LETRAS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    "b": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "####."],
    "c": ["....", "....", ".###", "#...", "#...", "#...", ".###"],
    "d": ["....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    "f": ["..##", ".#..", "###.", ".#..", ".#..", ".#..", ".#.."],
    "g": [".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", ".###."],
    "h": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "i": ["#", ".", "#", "#", "#", "#", "#"],
    "j": ["..#", "...", "..#", "..#", "..#", "..#", "..#", "#.#", ".#."],
    "k": ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"],
    "l": ["#.", "#.", "#.", "#.", "#.", "#.", ".#"],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    "n": [".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "o": [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."],
    "p": [".....", ".....", "####.", "#...#", "#...#", "#...#", "####.", "#....", "#...."],
    "q": [".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", "....#"],
    "r": ["....", "....", "#.##", "##..", "#...", "#...", "#..."],
    "s": ["....", "....", ".###", "#...", ".##.", "...#", "###."],
    "t": [".#..", ".#..", "###.", ".#..", ".#..", ".#..", "..##"],
    "u": [".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####"],
    "v": [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "w": [".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "x": [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "y": [".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####", "....#", ".###."],
    "z": [".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    ",": ["..", "..", "..", "..", "..", "..", ".#", "#."],
    ":": [".", ".", ".", "#", ".", ".", "#"],
    ";": ["..", "..", "..", ".#", "..", "..", ".#", "#."],
    "!": ["#", "#", "#", "#", "#", ".", "#"],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "-": ["...", "...", "...", "...", "###", "...", "..."],
    "–": ["....", "....", "....", "....", "####", "....", "...."],
    "—": [".....", ".....", ".....", ".....", "#####", ".....", "....."],
    "'": ["#", "#", ".", ".", ".", ".", "."],
    '"': ["#.#", "#.#", "...", "...", "...", "...", "..."],
    "(": [".#", "#.", "#.", "#.", "#.", "#.", ".#"],
    ")": ["#.", ".#", ".#", ".#", ".#", ".#", "#."],
    "[": ["##", "#.", "#.", "#.", "#.", "#.", "##"],
    "]": ["##", ".#", ".#", ".#", ".#", ".#", "##"],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    "%": ["##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"],
    "+": [".....", ".....", "..#..", "..#..", "#####", "..#..", "..#.."],
    "×": ["...", "...", "...", "#.#", ".#.", "#.#", "..."],
    "*": ["...", "#.#", ".#.", "#.#", "...", "...", "..."],
    "=": ["....", "....", "....", "####", "....", "####", "...."],
    "<": ["...", "...", "..#", ".#.", "#..", ".#.", "..#"],
    ">": ["...", "...", "#..", ".#.", "..#", ".#.", "#.."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    "…": [".....", ".....", ".....", ".....", ".....", ".....", "#.#.#"],
    "•": ["..", "..", "..", "##", "##", "..", ".."],
    "→": [".....", ".....", "..#..", "...#.", "#####", "...#.", "..#.."],
    "♥": [".....", ".#.#.", "#####", "#####", ".###.", "..#..", "....."],
    "º": ["##.", "#.#", ".##", "...", "###", "...", "..."],
    "ª": [".##", "#.#", ".##", "...", "###", "...", "..."],
    # sem pingo, só para montar í e ì
    "ı": [".", ".", "#", "#", "#", "#", "#"],
}

ACENTOS = {
    "agudo": [".#", "#."],
    "grave": ["#.", ".#"],
    "circunflexo": [".#.", "#.#"],
    "til": [".##.#", "#.##."],
    "trema": ["#.#"],
}
CEDILHA = ["..#.", ".#.."]

# letra acentuada -> (letra base, acento)
COMPOSTAS = {
    "Á": ("A", "agudo"), "À": ("A", "grave"), "Â": ("A", "circunflexo"), "Ã": ("A", "til"),
    "É": ("E", "agudo"), "Ê": ("E", "circunflexo"), "Í": ("I", "agudo"),
    "Ó": ("O", "agudo"), "Ô": ("O", "circunflexo"), "Õ": ("O", "til"),
    "Ú": ("U", "agudo"), "Ü": ("U", "trema"),
    "á": ("a", "agudo"), "à": ("a", "grave"), "â": ("a", "circunflexo"), "ã": ("a", "til"),
    "é": ("e", "agudo"), "ê": ("e", "circunflexo"), "í": ("ı", "agudo"),
    "ó": ("o", "agudo"), "ô": ("o", "circunflexo"), "õ": ("o", "til"),
    "ú": ("u", "agudo"), "ü": ("u", "trema"),
}


# ------------------------------------------------------------------ montagem

def pixels_de(linhas):
    """Lista de (coluna, linha) acesos. A linha 0 é o topo das maiúsculas; a 6 fica sobre a linha de base."""
    largura = len(linhas[0])
    assert all(len(l) == largura for l in linhas), linhas
    assert len(linhas) in (LINHA_DE_BASE, LINHA_DE_BASE + 1, LINHA_DE_BASE + DESCIDA), linhas
    return {(x, y) for y, l in enumerate(linhas) for x, c in enumerate(l) if c == "#"}, largura


def com_acento(base, nome_acento):
    pixels, largura = pixels_de(LETRAS[base])
    acento, largura_acento = pixels_de_acento(ACENTOS[nome_acento])
    topo = min(y for _, y in pixels)
    linha_do_acento = topo - 1 - len(ACENTOS[nome_acento])  # uma linha de folga acima da letra
    nova_largura = max(largura, largura_acento)
    desloc_base = (nova_largura - largura) // 2
    desloc_acento = (nova_largura - largura_acento + 1) // 2
    resultado = {(x + desloc_base, y) for x, y in pixels}
    resultado |= {(x + desloc_acento, y + linha_do_acento) for x, y in acento}
    return resultado, nova_largura


def pixels_de_acento(linhas):
    return {(x, y) for y, l in enumerate(linhas) for x, c in enumerate(l) if c == "#"}, len(linhas[0])


def com_cedilha(base):
    pixels, largura = pixels_de(LETRAS[base])
    cedilha, _ = pixels_de_acento(CEDILHA)
    desloc = (largura - 4) // 2 + (1 if base == "C" else 0)
    return pixels | {(x + desloc, y + LINHA_DE_BASE) for x, y in cedilha}, largura


def todos_os_glifos():
    glifos = {c: pixels_de(linhas) for c, linhas in LETRAS.items()}
    for c, (base, acento) in COMPOSTAS.items():
        glifos[c] = com_acento(base, acento)
    glifos["Ç"] = com_cedilha("C")
    glifos["ç"] = com_cedilha("c")
    return glifos


def desenhar(pixels):
    """Um retângulo por sequência horizontal de pixels (contorno horário, como o TrueType pede)."""
    caneta = TTGlyphPen(None)
    for y in sorted({y for _, y in pixels}):
        colunas = sorted(x for x, yy in pixels if yy == y)
        inicio = anterior = colunas[0]
        for x in colunas[1:] + [None]:
            if x is not None and x == anterior + 1:
                anterior = x
                continue
            x0, x1 = inicio * PIXEL, (anterior + 1) * PIXEL
            y1 = (LINHA_DE_BASE - y) * PIXEL
            y0 = y1 - PIXEL
            caneta.moveTo((x0, y0))
            caneta.lineTo((x0, y1))
            caneta.lineTo((x1, y1))
            caneta.lineTo((x1, y0))
            caneta.closePath()
            if x is not None:
                inicio = anterior = x
    return caneta.glyph()


def gerar():
    glifos = todos_os_glifos()
    nomes = {c: "uni%04X" % ord(c) for c in glifos}
    ordem = [".notdef", "space"] + [nomes[c] for c in sorted(glifos)]
    desenhos = {".notdef": TTGlyphPen(None).glyph(), "space": TTGlyphPen(None).glyph()}
    metricas = {".notdef": (LARGURA_ESPACO * PIXEL, 0), "space": (LARGURA_ESPACO * PIXEL, 0)}
    for c, (pixels, largura) in glifos.items():
        desenhos[nomes[c]] = desenhar(pixels)
        metricas[nomes[c]] = ((largura + 1) * PIXEL, min(x for x, _ in pixels) * PIXEL)
    mapa = {ord(c): nomes[c] for c in glifos if c != "ı"}
    mapa[ord(" ")] = "space"
    mapa[0xA0] = "space"

    fonte = FontBuilder(unitsPerEm=PIXELS_POR_EM * PIXEL, isTTF=True)
    fonte.setupGlyphOrder(ordem)
    fonte.setupCharacterMap(mapa)
    fonte.setupGlyf(desenhos)
    fonte.setupHorizontalMetrics(metricas)
    fonte.setupHorizontalHeader(ascent=SUBIDA * PIXEL, descent=-DESCIDA * PIXEL)
    fonte.setupNameTable({"familyName": "Sentinela Pixel", "styleName": "Regular"})
    fonte.setupOS2(sTypoAscender=SUBIDA * PIXEL, sTypoDescender=-DESCIDA * PIXEL, sTypoLineGap=0,
                   usWinAscent=SUBIDA * PIXEL, usWinDescent=DESCIDA * PIXEL)
    fonte.setupPost()
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    fonte.save(DESTINO)
    print(f"{len(glifos)} glifos em {DESTINO}")


def previa(destino):
    """Imagem de conferência com um texto de exemplo em três tamanhos."""
    from PIL import Image, ImageDraw, ImageFont
    texto = ["SENTINELA  Guardião da Samaúma  0123456789",
             "A máquina avança. Não é ação à toa: é coração, pão, véu, vôo, lá, ênfase!",
             "ÁÀÂÃ ÉÊ Í ÓÔÕ Ú Ç  áàâã éê í óôõ ú ç  ? ! . , ; : - – — ' \" ( ) [ ] / % + × = → ♥ • … 1º",
             "The quick brown fox jumps over the lazy dog  WASD J Espaço Esc  Onda 3/5  ×3"]
    imagem = Image.new("RGB", (1150, 330), (24, 34, 28))
    desenho = ImageDraw.Draw(imagem)
    y = 8
    for tamanho in (16, 24, 32):
        fonte = ImageFont.truetype(DESTINO, tamanho)
        for linha in texto:
            desenho.text((8, y), linha, font=fonte, fill=(236, 230, 200))
            y += int(tamanho * 1.5)
        y += 6
    imagem.save(destino)


if __name__ == "__main__":
    gerar()
    if len(sys.argv) > 1:
        previa(sys.argv[1])
