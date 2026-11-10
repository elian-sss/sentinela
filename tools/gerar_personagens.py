"""Gera os sprites animados do herói, da árvore sagrada, dos inimigos e do chefe em pixel art.

Saída:
- assets/personagens/<nome>.png: uma folha por personagem, com os quadros lado a lado.
- cenas/<pasta>/<nome>_quadros.tres: o SpriteFrames do Godot com as animações.

Para gerar de novo: python tools/gerar_personagens.py (requer Pillow e numpy).
Os desenhos são feitos de frente, levemente de cima (visão 3/4), e viram para a esquerda com flip_h.
"""

import math
import os
import random

import numpy as np
from PIL import Image

from gerar_props import FOLHA, contornar, copa, sombra_eliptica, tela

RAIZ = os.path.join(os.path.dirname(__file__), "..")
PASTA_PNG = os.path.join(RAIZ, "assets", "personagens")

# ------------------------------------------------------------------ paleta

PELE = [(118, 72, 46), (150, 96, 62), (182, 124, 84)]
PELE_CLARA = [(170, 110, 80), (214, 156, 116), (236, 190, 150)]
FOGO = [(176, 44, 28), (232, 100, 34), (255, 170, 60), (255, 226, 130)]
URUCUM = (206, 52, 40)
OLHO = (24, 20, 26)
MADEIRA = [(70, 46, 30), (104, 70, 44), (140, 100, 62)]
XADREZ = [(110, 26, 30), (176, 44, 44), (214, 76, 66), (40, 26, 26)]
JEANS = [(40, 54, 90), (58, 78, 126)]
CALCA = [(44, 44, 50), (64, 64, 72)]
BOTA = [(46, 32, 24), (72, 50, 36)]
BARBA = [(78, 46, 24), (110, 68, 36)]
METAL = [(84, 88, 96), (140, 146, 156), (206, 212, 220)]
AMARELO = [(150, 104, 20), (210, 158, 36), (246, 200, 64), (255, 232, 140)]
LARANJA = [(170, 72, 20), (226, 116, 34), (252, 160, 60)]
CINZA = [(40, 42, 48), (62, 64, 72), (94, 98, 106), (130, 134, 142)]
VIDRO = [(44, 74, 92), (78, 122, 146), (150, 196, 214)]
CASCA = [(78, 70, 60), (110, 100, 86), (146, 136, 118), (180, 172, 150)]
BRILHO_SAGRADO = [(150, 255, 180), (255, 236, 140)]


# ------------------------------------------------------------------ primitivas

def px(img, x, y, cor):
    h, w = img.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        img[int(y), int(x)] = cor if len(cor) == 4 else (*cor, 255)


def retangulo(img, x0, y0, x1, y1, cor):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            px(img, x, y, cor)


def elipse(img, cx, cy, rx, ry, cor):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1:
                px(img, x, y, cor)


def linha(img, x0, y0, x1, y1, cor, espessura=1):
    passos = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(passos + 1):
        t = i / passos
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for dx in range(espessura):
            for dy in range(espessura):
                px(img, round(x) + dx, round(y) + dy, cor)


def pernas(img, x_esq, x_dir, topo, base, fase, cor, cor_pe, largura=3):
    """Duas pernas de frente. Na fase 1 a esquerda levanta, na fase 3 a direita."""
    for i, x in enumerate((x_esq, x_dir)):
        levantada = (fase == 1 and i == 0) or (fase == 3 and i == 1)
        fim = base - (2 if levantada else 0)
        retangulo(img, x, topo, x + largura - 1, fim - 2, cor[1] if i == 0 else cor[0])
        retangulo(img, x - (1 if i == 0 else 0), fim - 1, x + largura - (0 if i == 0 else -1), fim, cor_pe)


# ------------------------------------------------------------------ herói: guardião da floresta

MARGEM_HEROI = 8  # folga dos dois lados do quadro, para o cajado caber nas poses de ataque


def heroi(fase, bob, pose="normal"):
    """Espírito guardião: cabelo de fogo, pintura de urucum, manto de folhas e um cajado com broto.
    pose: 'normal' (cajado em pé), 'ataque_alto' (cajado erguido) ou 'ataque_baixo' (cajado descendo à frente)."""
    img = tela(32, 44)
    o = bob
    pernas(img, 12, 17, 32 + o, 42, fase, [PELE[0], PELE[1]], PELE[0])
    # manto de folhas, alargando para baixo
    for r in range(16):
        y = 17 + o + r
        meia = 6 + r // 4
        for x in range(16 - meia, 16 + meia):
            base = FOLHA[2] if x < 14 else FOLHA[1]
            if (x + 2 * (y - o)) % 9 == 0:  # nervuras das folhas, espaçadas
                base = FOLHA[3]
            elif x == 16 + meia - 1:
                base = FOLHA[0]
            px(img, x, y, base)
    for x in range(8, 24, 2):  # barra recortada como folhas
        px(img, x, 33 + o, FOLHA[1])
    retangulo(img, 10, 26 + o, 21, 26 + o, MADEIRA[1])  # cinto de cipó
    px(img, 15, 26 + o, URUCUM)
    px(img, 16, 26 + o, (255, 120, 90))
    retangulo(img, 7, 19 + o, 8, 25 + o, PELE[1])  # braço esquerdo
    retangulo(img, 23, 20 + o, 24, 24 + o, PELE[1])  # braço direito segurando o cajado
    # cabeça
    retangulo(img, 12, 8 + o, 20, 16 + o, PELE[1])
    retangulo(img, 12, 8 + o, 12, 15 + o, PELE[2])
    retangulo(img, 20, 9 + o, 20, 16 + o, PELE[0])
    retangulo(img, 14, 11 + o, 14, 12 + o, OLHO)
    retangulo(img, 18, 11 + o, 18, 12 + o, OLHO)
    linha(img, 13, 14 + o, 15, 14 + o, URUCUM)  # pintura de urucum
    linha(img, 17, 14 + o, 19, 14 + o, URUCUM)
    # cabelo de fogo em labaredas
    for x in range(10, 23):
        altura_chama = 5 + int(3 * abs(math.sin(x * 1.3 + bob)))
        for k in range(altura_chama):
            y = 8 + o - k
            cor = FOGO[0] if k == 0 else FOGO[1] if k < altura_chama - 2 else FOGO[2]
            if k == altura_chama - 1 and x % 3 == 0:
                cor = FOGO[3]
            px(img, x, y, cor)
    retangulo(img, 10, 9 + o, 11, 14 + o, FOGO[1])  # mechas dos lados do rosto
    retangulo(img, 21, 9 + o, 22, 14 + o, FOGO[0])
    # passa para o quadro largo e desenha o cajado com broto na ponta, conforme a pose
    largo = tela(32 + MARGEM_HEROI * 2, 44)
    largo[:, MARGEM_HEROI:MARGEM_HEROI + 32] = img
    m = MARGEM_HEROI
    if pose == "normal":
        base, ponta = (25 + m, 42), (25 + m, 6 + o)
    elif pose == "ataque_alto":
        base, ponta = (22 + m, 30 + o), (33 + m, 3 + o)
    else:
        base, ponta = (22 + m, 20 + o), (39 + m, 30 + o)
    linha(largo, base[0], base[1], ponta[0], ponta[1], MADEIRA[1], 2)
    linha(largo, base[0], base[1], ponta[0], ponta[1], MADEIRA[2], 1)
    if pose != "normal":
        retangulo(largo, 23 + m, 21 + o, 25 + m, 23 + o, PELE[2])  # mão à frente
    for dx, dy, cor in ((-2, -2, FOLHA[3]), (-1, -3, FOLHA[2]), (2, -2, FOLHA[2]), (3, -3, FOLHA[3]), (0, -1, FOLHA[1]), (1, -1, FOLHA[1]), (0, -4, FOLHA[4])):
        px(largo, ponta[0] + dx, ponta[1] + dy, cor)
    contornar(largo)
    return largo


# ------------------------------------------------------------------ lenhador

def lenhador(fase, bob, machado):
    """machado: 'ombro' (andando), 'alto' ou 'baixo' (golpeando a árvore)."""
    img = tela(28, 38)
    o = bob
    pernas(img, 10, 15, 27 + o, 37, fase, JEANS, BOTA[0])
    for y in range(15 + o, 28 + o):  # camisa xadrez
        for x in range(8, 20):
            cor = XADREZ[1] if x < 16 else XADREZ[0]
            if x % 4 == 0 or (y - o) % 4 == 0:
                cor = XADREZ[3] if (x % 4 == 0 and (y - o) % 4 == 0) else XADREZ[0] if x >= 16 else XADREZ[2]
            px(img, x, y, cor)
    retangulo(img, 6, 16 + o, 7, 24 + o, XADREZ[1])  # braço
    px(img, 6, 25 + o, PELE_CLARA[1])
    retangulo(img, 9, 5 + o, 18, 14 + o, PELE_CLARA[1])  # cabeça
    retangulo(img, 9, 5 + o, 9, 13 + o, PELE_CLARA[2])
    px(img, 11, 9 + o, OLHO)
    px(img, 16, 9 + o, OLHO)
    retangulo(img, 9, 11 + o, 18, 15 + o, BARBA[1])  # barba
    retangulo(img, 15, 12 + o, 18, 15 + o, BARBA[0])
    retangulo(img, 12, 12 + o, 15, 12 + o, (150, 70, 60))
    retangulo(img, 8, 2 + o, 19, 6 + o, XADREZ[1])  # gorro
    retangulo(img, 8, 6 + o, 19, 6 + o, XADREZ[0])
    retangulo(img, 13, 0 + o, 14, 1 + o, (230, 230, 230))
    # machado
    if machado == "ombro":
        cabo, lamina = ((20, 22 + o), (23, 4 + o)), (21, 1 + o, 26, 6 + o)
    elif machado == "alto":
        cabo, lamina = ((20, 20 + o), (17, 2 + o)), (13, 0 + o, 19, 4 + o)
    else:
        cabo, lamina = ((20, 20 + o), (26, 30 + o)), (23, 28 + o, 27, 34 + o)
    retangulo(img, 19, 19 + o, 21, 22 + o, PELE_CLARA[1])  # mão
    linha(img, *cabo[0], *cabo[1], MADEIRA[2], 2)
    retangulo(img, *lamina, METAL[1])
    retangulo(img, lamina[0], lamina[1], lamina[0], lamina[3], METAL[2])
    contornar(img)
    return img


# ------------------------------------------------------------------ motosserrista

def motosserrista(fase, bob, tremor, faiscas):
    img = tela(28, 38)
    o = bob
    pernas(img, 10, 15, 27 + o, 37, fase, CALCA, BOTA[0])
    retangulo(img, 8, 15 + o, 19, 27 + o, CINZA[2])  # camisa
    retangulo(img, 8, 15 + o, 10, 27 + o, LARANJA[1])  # colete
    retangulo(img, 17, 15 + o, 19, 27 + o, LARANJA[0])
    retangulo(img, 8, 22 + o, 19, 22 + o, AMARELO[3])  # faixa refletiva
    retangulo(img, 6, 16 + o, 7, 24 + o, CINZA[2])
    retangulo(img, 9, 5 + o, 18, 14 + o, PELE_CLARA[1])  # cabeça
    retangulo(img, 9, 5 + o, 9, 13 + o, PELE_CLARA[2])
    retangulo(img, 10, 8 + o, 17, 9 + o, CINZA[0])  # óculos de proteção
    px(img, 11, 8 + o, VIDRO[2])
    px(img, 16, 8 + o, VIDRO[2])
    retangulo(img, 12, 12 + o, 15, 12 + o, (150, 70, 60))
    retangulo(img, 8, 2 + o, 19, 6 + o, AMARELO[2])  # capacete
    retangulo(img, 7, 6 + o, 20, 6 + o, AMARELO[1])
    retangulo(img, 9, 2 + o, 11, 3 + o, AMARELO[3])
    # motosserra na cintura, apontando para a frente
    t = tremor
    retangulo(img, 15, 20 + o + t, 21, 26 + o + t, LARANJA[1])
    retangulo(img, 15, 20 + o + t, 21, 20 + o + t, LARANJA[2])
    retangulo(img, 16, 18 + o + t, 19, 19 + o + t, CINZA[0])  # alça
    retangulo(img, 22, 22 + o + t, 27, 24 + o + t, METAL[1])  # sabre
    for x in range(22, 28):
        if (x + fase + t) % 2 == 0:
            px(img, x, 21 + o + t, CINZA[0])
            px(img, x, 25 + o + t, CINZA[0])
    if faiscas:
        for dx, dy in ((1, -2), (2, 0), (0, 2), (2, -4)):
            px(img, 26 + dx - 1, 23 + o + t + dy, AMARELO[3])
    contornar(img)
    return img


# ------------------------------------------------------------------ chefe: escavadeira

def escavadeira(quadro):
    img = tela(124, 96)
    sombra_eliptica(img, 58, 88, 50, 8)
    # esteira
    retangulo(img, 12, 70, 100, 88, CINZA[0])
    retangulo(img, 14, 72, 98, 86, CINZA[1])
    for x in range(14 + quadro * 2, 99, 4):
        retangulo(img, x, 72, x, 86, CINZA[0])
    for cx in (22, 40, 58, 76, 92):
        elipse(img, cx, 79, 5, 5, CINZA[2])
        px(img, cx, 79, CINZA[0])
    # base
    retangulo(img, 16, 54, 96, 70, AMARELO[1])
    retangulo(img, 16, 54, 96, 56, AMARELO[2])
    retangulo(img, 16, 66, 96, 70, AMARELO[0])
    # contrapeso com faixas de alerta
    retangulo(img, 60, 36, 94, 56, AMARELO[1])
    for y in range(46, 55):
        for x in range(62, 93):
            if (x + y) // 3 % 2 == 0:
                px(img, x, y, CINZA[0])
    retangulo(img, 60, 36, 94, 38, AMARELO[3])
    # escapamento e fumaça
    retangulo(img, 84, 22, 86, 36, CINZA[1])
    for i, (dx, dy) in enumerate(((0, -4), (2, -8), (-1, -11))):
        if (i + quadro) % 2 == 0:
            elipse(img, 85 + dx, 22 + dy, 2, 2, CINZA[3])
    # cabine
    retangulo(img, 20, 20, 58, 56, AMARELO[2])
    retangulo(img, 20, 20, 58, 23, AMARELO[3])
    retangulo(img, 56, 22, 58, 56, AMARELO[1])
    retangulo(img, 26, 26, 52, 44, VIDRO[1])
    retangulo(img, 26, 26, 52, 27, VIDRO[0])
    linha(img, 30, 42, 40, 28, VIDRO[2], 2)
    # braço e caçamba
    linha(img, 56, 42, 88, 12, AMARELO[1], 6)
    linha(img, 57, 42, 88, 13, AMARELO[3], 2)
    linha(img, 90, 14, 110, 48, AMARELO[1], 5)
    elipse(img, 90, 15, 4, 4, CINZA[1])
    retangulo(img, 102, 46, 120, 62, CINZA[1])
    retangulo(img, 102, 46, 120, 48, CINZA[2])
    for x in range(103, 121, 4):
        retangulo(img, x, 63, x + 1, 65, METAL[2])
    contornar(img)
    return img


# ------------------------------------------------------------------ árvore sagrada: samaúma

# Círculos da copa (x, y, raio) em cada estado: 0 saudável, 1 ferida, 2 por um fio.
COPA_SAMAUMA = [
    [(84, 56, 40), (46, 66, 30), (122, 66, 30), (20, 78, 18), (148, 78, 18),
     (62, 38, 28), (106, 38, 28), (84, 24, 24), (84, 84, 30)],
    [(84, 56, 33), (46, 66, 23), (122, 66, 22), (62, 38, 23), (106, 40, 20), (84, 28, 19), (84, 82, 22)],
    [(84, 58, 22), (50, 64, 14), (118, 66, 13), (70, 40, 15), (102, 44, 12)],
]
FOLHA_SECA = [(60, 58, 30), (92, 88, 42), (126, 116, 54), (156, 140, 66), (184, 166, 88)]


def arvore_sagrada(semente, estado=0):
    """Samaúma: tronco cinza com sapopemas e copa em guarda-chuva. O estado mostra o quanto ela já sofreu."""
    rng = random.Random(semente)
    img = tela(168, 184)
    sombra_eliptica(img, 84, 172, 70, 10)
    # sapopemas (raízes em tábua) e tronco cinza
    for y in range(96, 176):
        t = (y - 96) / 80
        meia = 14 + 6 * t + (max(0, t - 0.55) ** 2) * 160
        for x in range(int(84 - meia), int(84 + meia) + 1):
            rel = (x - (84 - meia)) / (2 * meia)
            indice = 3 if rel < 0.2 else 2 if rel < 0.55 else 1 if rel < 0.85 else 0
            if rng.random() < 0.08:
                indice = max(indice - 1, 0)
            px(img, x, y, CASCA[indice])
    for x in (60, 108, 72, 96):  # vincos das raízes
        linha(img, 84 + (x - 84) * 0.3, 140, x, 175, CASCA[0])
    # símbolo sagrado no tronco: brilha enquanto ela está bem e apaga quando está por um fio
    cor_simbolo = [BRILHO_SAGRADO[0], (110, 170, 130), CASCA[0]][estado]
    for dx, dy in ((0, 0), (-1, 1), (1, 1), (0, 2), (-2, 3), (2, 3), (0, 4)):
        px(img, 84 + dx, 118 + dy, cor_simbolo)
    # galhos: ficam escondidos pela copa cheia e aparecem conforme ela perde folhas
    for cx, cy, r in COPA_SAMAUMA[0]:
        linha(img, 84, 100, cx, cy + r * 0.3, CASCA[1], 3)
        linha(img, 84, 100, cx, cy + r * 0.3, CASCA[2], 1)
        for lado in (-1, 1):
            linha(img, cx, cy + r * 0.3, cx + lado * r * 0.5, cy - r * 0.2, CASCA[1], 2)
    # copa larga em guarda-chuva, mais rala e mais seca a cada estado
    blobs = COPA_SAMAUMA[estado]
    copa(img, blobs, FOLHA if estado < 2 else FOLHA_SECA, rng)
    for _ in range([14, 8, 3][estado]):  # cipós pendurados
        x = rng.randint(24, 144)
        inicio = next((y for y in range(110, 0, -1) if img[y, x, 3] and tuple(img[y, x][:3]) not in CASCA), None)
        if inicio:
            for y in range(inicio, inicio + rng.randint(6, 16)):
                px(img, x, y, FOLHA[1])
    for _ in range([26, 10, 0][estado]):  # brilhos sagrados na copa
        cx, cy, r = rng.choice(blobs)
        x, y = cx + rng.randint(-r // 2, r // 2), cy + rng.randint(-r // 2, r // 2)
        if img[y, x, 3]:
            px(img, x, y, BRILHO_SAGRADO[1])
    contornar(img)
    return img


# ------------------------------------------------------------------ itens (20 x 20, cada um com a cor que o identifica)

def item_fruta():
    img = tela(20, 20)
    elipse(img, 10, 12, 6, 6, (176, 30, 44))
    elipse(img, 9, 11, 5, 5, (220, 52, 60))
    elipse(img, 7, 9, 2, 2, (255, 140, 130))
    linha(img, 10, 6, 11, 3, MADEIRA[1])
    for dx, dy in ((1, 0), (2, -1), (3, -1), (2, 0), (4, -2)):
        px(img, 11 + dx, 4 + dy, FOLHA[3] if dy < -1 else FOLHA[2])
    contornar(img)
    return img


def folha(img, x0, y0, angulo, comprimento, largura, clara, escura, nervura, entalhes=False):
    """Folha (ou pena) em forma de fuso, com nervura no meio. O lado de cima fica mais claro."""
    a = math.radians(angulo)
    direcao = (math.cos(a), math.sin(a))
    normal = (-direcao[1], direcao[0])
    for i in range(comprimento * 2):
        t = i / (comprimento * 2)
        meia = math.sin(math.pi * min(t * 1.15, 1)) * largura
        if entalhes and int(t * 10) % 3 == 2:
            meia *= 0.5
        cx, cy = x0 + direcao[0] * t * comprimento, y0 + direcao[1] * t * comprimento
        for k in range(-int(meia * 2), int(meia * 2) + 1):
            d = k / 2
            px(img, round(cx + normal[0] * d), round(cy + normal[1] * d), clara if d < 0 else escura)
        px(img, round(cx), round(cy), nervura)


def item_erva():
    img = tela(20, 20)
    for angulo in (-130, -90, -50):
        folha(img, 10, 17, angulo, 11 if angulo == -90 else 9, 2.4, FOLHA[3], FOLHA[2], FOLHA[1])
    retangulo(img, 8, 15, 12, 17, MADEIRA[2])  # amarrado de cipó
    retangulo(img, 8, 16, 12, 16, MADEIRA[1])
    contornar(img)
    return img


def item_escudo():
    """Casco de jabuti azulado."""
    img = tela(20, 20)
    azul = [(50, 104, 150), (90, 150, 200), (150, 200, 236), (214, 240, 255)]
    elipse(img, 10, 11, 8, 7, azul[0])
    elipse(img, 10, 10, 7, 6, azul[1])
    for cx, cy in ((10, 10), (6, 9), (14, 9), (8, 13), (12, 13)):  # placas do casco
        elipse(img, cx, cy, 1.6, 1.4, azul[2])
    px(img, 7, 6, azul[3])
    px(img, 8, 6, azul[3])
    contornar(img)
    return img


def item_velocidade():
    """Pena de gavião amarela, com a ponta laranja."""
    img = tela(20, 20)
    folha(img, 4, 17, -55, 17, 2.6, (255, 230, 120), (226, 176, 44), (150, 100, 30), entalhes=True)
    for i in range(4):  # ponta laranja
        px(img, 13 + i // 2, 4 - i // 2 + 1, (236, 120, 40))
    linha(img, 3, 18, 5, 15, (150, 100, 30))  # cálamo
    contornar(img)
    return img


def item_forca():
    """Cacho de sementes roxas de açaí."""
    img = tela(20, 20)
    roxo = [(60, 26, 80), (110, 58, 150), (164, 110, 210), (226, 190, 250)]
    linha(img, 10, 3, 10, 8, MADEIRA[1])
    for cx, cy in ((7, 10), (13, 10), (10, 9), (8, 14), (12, 14), (10, 12), (10, 16)):
        elipse(img, cx, cy, 2.2, 2.2, roxo[1])
        px(img, cx - 1, cy - 1, roxo[3])
        px(img, cx + 1, cy + 1, roxo[0])
    contornar(img)
    return img


# ------------------------------------------------------------------ golpe do herói

def golpe(inicio, fim, forca):
    """Arco de energia verde-dourada do cajado, virado para a direita (+x).
    O centro do arco fica no herói, 34 px atrás do centro do quadro (como em heroi.gd).
    inicio e fim são os ângulos do arco em graus; forca (0 a 1) afina e apaga o rastro."""
    img = tela(64, 84)
    cx, cy = 32 - 34, 42
    cores = [(90, 200, 90, 150), (190, 255, 140, 210), (255, 255, 225, 255)]
    for y in range(84):
        for x in range(64):
            d = math.hypot(x - cx, y - cy)
            a = math.degrees(math.atan2(y - cy, x - cx))
            if not inicio <= a <= fim:
                continue
            t = (a - inicio) / max(fim - inicio, 1)  # 0 no rastro, 1 na ponta do golpe
            espessura = (3 + 9 * t) * forca
            meio = 36
            distancia = abs(d - meio)
            if distancia > espessura:
                continue
            nivel = 2 if distancia < espessura * 0.35 else 1 if distancia < espessura * 0.7 else 0
            px(img, x, y, cores[nivel])
    return img


# ------------------------------------------------------------------ saída

def salvar_folha(nome, quadros):
    os.makedirs(PASTA_PNG, exist_ok=True)
    largura, altura = quadros[0].shape[1], quadros[0].shape[0]
    folha = np.concatenate(quadros, axis=1)
    Image.fromarray(folha, "RGBA").save(os.path.join(PASTA_PNG, nome + ".png"))
    return largura, altura


def salvar_quadros(caminho_tres, nome_png, tamanho, animacoes):
    """animacoes: lista de (nome, [índices dos quadros], fps, repete)."""
    largura, altura = tamanho
    usados = sorted({i for _, indices, _, _ in animacoes for i in indices})
    linhas = [f'[gd_resource type="SpriteFrames" load_steps={len(usados) + 2} format=3]', "",
              f'[ext_resource type="Texture2D" path="res://assets/personagens/{nome_png}.png" id="1_folha"]', ""]
    for i in usados:
        linhas += [f'[sub_resource type="AtlasTexture" id="quadro_{i}"]', 'atlas = ExtResource("1_folha")',
                   f"region = Rect2({i * largura}, 0, {largura}, {altura})", ""]
    blocos = []
    for nome, indices, fps, repete in animacoes:
        quadros = ", ".join(f'{{"duration": 1.0, "texture": SubResource("quadro_{i}")}}' for i in indices)
        blocos.append(f'{{\n"frames": [{quadros}],\n"loop": {"true" if repete else "false"},\n'
                      f'"name": &"{nome}",\n"speed": {fps:.1f}\n}}')
    linhas += ["[resource]", "animations = [" + ", ".join(blocos) + "]", ""]
    with open(os.path.join(RAIZ, caminho_tres), "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("\n".join(linhas))


# Andar: perna esquerda, meio (abaixado), perna direita, meio (abaixado).
PASSOS = ((1, 0), (0, 1), (3, 0), (0, 1))


def main():
    quadros = [heroi(0, 0), heroi(0, 1)] + [heroi(f, b) for f, b in PASSOS]
    quadros += [heroi(0, 0, "ataque_alto"), heroi(1, 1, "ataque_baixo")]
    tamanho = salvar_folha("heroi", quadros)
    salvar_quadros("cenas/heroi/heroi_quadros.tres", "heroi", tamanho,
                   [("parado", [0, 1], 3, True), ("andando", [2, 3, 4, 5], 8, True),
                    ("atacando", [6, 7, 7], 16, False)])

    quadros = [lenhador(f, b, "ombro") for f, b in PASSOS] + [lenhador(0, 0, "alto"), lenhador(0, 1, "baixo")]
    tamanho = salvar_folha("lenhador", quadros)
    salvar_quadros("cenas/inimigo/lenhador_quadros.tres", "lenhador", tamanho,
                   [("andando", [0, 1, 2, 3], 7, True), ("atacando", [4, 5], 2, True)])

    quadros = [motosserrista(f, b, 0, False) for f, b in PASSOS] + [motosserrista(0, 0, -1, True), motosserrista(1, 0, 1, False)]
    tamanho = salvar_folha("motosserrista", quadros)
    salvar_quadros("cenas/inimigo/motosserrista_quadros.tres", "motosserrista", tamanho,
                   [("andando", [0, 1, 2, 3], 10, True), ("atacando", [4, 5], 14, True)])

    tamanho = salvar_folha("escavadeira", [escavadeira(0), escavadeira(1)])
    salvar_quadros("cenas/chefe/escavadeira_quadros.tres", "escavadeira", tamanho,
                   [("andando", [0, 1], 6, True)])

    salvar_folha("arvore_sagrada", [arvore_sagrada(21, estado) for estado in range(3)])

    quadros = [golpe(-75, -25, 1.0), golpe(-75, 25, 1.0), golpe(-60, 70, 1.0), golpe(-20, 75, 0.6)]
    tamanho = salvar_folha("golpe", quadros)
    salvar_quadros("cenas/heroi/golpe_quadros.tres", "golpe", tamanho, [("golpe", [0, 1, 2, 3], 20, False)])

    for nome, funcao in (("fruta", item_fruta), ("erva", item_erva), ("escudo", item_escudo),
                         ("velocidade", item_velocidade), ("forca", item_forca)):
        salvar_folha("item_" + nome, [funcao()])


if __name__ == "__main__":
    main()
