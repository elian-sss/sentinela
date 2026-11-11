"""Gera os sprites animados do herói, dos inimigos e do chefe em pixel art.
A Samaúma e os itens vêm de packs licenciados: veja tools/montar_assets_licenciados.py.

Saída:
- assets/personagens/<nome>.png: uma folha por personagem, com os quadros lado a lado.
- cenas/<pasta>/<nome>_quadros.tres: o SpriteFrames do Godot com as animações.

Para gerar de novo: python tools/gerar_personagens.py (requer Pillow e numpy).
Os desenhos são feitos de frente, levemente de cima (visão 3/4), e viram para a esquerda com flip_h.
"""

import math
import os

import numpy as np
from PIL import Image

from pixel_base import FOLHA, contornar, copa, sombra_eliptica, tela

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

    quadros = [golpe(-75, -25, 1.0), golpe(-75, 25, 1.0), golpe(-60, 70, 1.0), golpe(-20, 75, 0.6)]
    tamanho = salvar_folha("golpe", quadros)
    salvar_quadros("cenas/heroi/golpe_quadros.tres", "golpe", tamanho, [("golpe", [0, 1, 2, 3], 20, False)])


if __name__ == "__main__":
    main()
