"""Gera os props coloridos do cenário em pixel art (arte original do projeto).

Saída: assets/cenario/props/*.png, na mesma escala do pack Dead Swamp (tiles de 32 px).
Para gerar de novo: python tools/gerar_props.py (requer Pillow e numpy).
A semente é fixa, então o resultado é sempre o mesmo.
"""

import math
import os
import random

import numpy as np
from PIL import Image

PASTA = os.path.join(os.path.dirname(__file__), "..", "assets", "cenario", "props")

# ------------------------------------------------------------------ paleta

CONTORNO = (22, 32, 20, 255)
FOLHA = [(30, 72, 40), (44, 104, 50), (66, 138, 60), (104, 172, 72), (150, 204, 96)]
FOLHA_ESCURA = [(24, 58, 44), (34, 84, 58), (50, 112, 66), (82, 146, 78), (124, 182, 96)]
TRONCO = [(52, 34, 24), (84, 56, 36), (116, 80, 50), (146, 106, 66)]
SOMBRA = (0, 0, 0, 90)
FLORES = {
    "vermelha": [(150, 30, 40), (220, 60, 60), (255, 130, 110)],
    "amarela": [(170, 110, 20), (240, 190, 50), (255, 236, 140)],
    "roxa": [(80, 40, 120), (150, 90, 200), (210, 160, 240)],
    "rosa": [(150, 60, 100), (236, 120, 170), (255, 196, 220)],
}
ACAI = [(40, 20, 50), (80, 40, 100), (130, 80, 150)]
COGUMELO = [(120, 40, 20), (220, 100, 40), (255, 170, 80)]


def tela(largura, altura):
    return np.zeros((altura, largura, 4), dtype=np.uint8)


def pintar(img, x, y, cor):
    h, w = img.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        img[y, x] = cor if len(cor) == 4 else (*cor, 255)


def contornar(img):
    """Contorno escuro de 1 px em volta de tudo que é opaco."""
    opaco = img[:, :, 3] > 200
    borda = np.zeros_like(opaco)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        borda |= np.roll(np.roll(opaco, dy, 0), dx, 1)
    borda &= ~opaco
    borda[0, :] = borda[-1, :] = False
    borda[:, 0] = borda[:, -1] = False
    img[borda & (img[:, :, 3] == 0)] = CONTORNO
    img[borda & (img[:, :, 3] > 0) & (img[:, :, 3] <= 200)] = CONTORNO


def sombra_eliptica(img, cx, cy, rx, ry):
    h, w = img.shape[:2]
    for y in range(h):
        for x in range(w):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 and img[y, x, 3] == 0:
                img[y, x] = SOMBRA


def salvar(img, nome):
    os.makedirs(PASTA, exist_ok=True)
    Image.fromarray(img, "RGBA").save(os.path.join(PASTA, nome + ".png"))


# ------------------------------------------------------------------ partes

def copa(img, blobs, paleta, rng):
    """Copa feita de vários círculos, iluminada de cima à esquerda, com tufos de folhas."""
    h, w = img.shape[:2]
    luz = np.array([-0.6, -0.8])
    for y in range(h):
        for x in range(w):
            melhor = None
            for cx, cy, r in blobs:
                d = math.hypot(x - cx, y - cy)
                ruido = rng.uniform(-1.2, 1.2)
                if d <= r + ruido:
                    nx, ny = (x - cx) / r, (y - cy) / r
                    luz_local = -(nx * luz[0] + ny * luz[1])
                    if melhor is None or luz_local > melhor:
                        melhor = luz_local
            if melhor is None:
                continue
            valor = melhor + rng.uniform(-0.25, 0.25)
            indice = int(np.clip((valor + 1) / 2 * len(paleta), 0, len(paleta) - 1))
            pintar(img, x, y, paleta[indice])
    # tufos claros espalhados
    for _ in range(len(blobs) * 6):
        cx, cy, r = rng.choice(blobs)
        a = rng.uniform(math.pi, 2 * math.pi)
        dist = rng.uniform(0, r * 0.8)
        x, y = int(cx + math.cos(a) * dist), int(cy + math.sin(a) * dist)
        if img[y % h, x % w, 3]:
            for dx, dy in ((0, 0), (1, 0), (0, -1)):
                if 0 <= y + dy < h and 0 <= x + dx < w and img[y + dy, x + dx, 3]:
                    pintar(img, x + dx, y + dy, paleta[-1])


def tronco(img, base_x, topo_y, base_y, largura, rng):
    for y in range(topo_y, base_y + 1):
        t = (y - topo_y) / max(base_y - topo_y, 1)
        meia = largura / 2 + t * t * 3  # alarga embaixo (raízes)
        for x in range(int(base_x - meia), int(base_x + meia) + 1):
            rel = (x - (base_x - meia)) / (2 * meia)
            indice = 1 if rel > 0.6 else (2 if rel > 0.25 else 3)
            if rng.random() < 0.12:
                indice = 0
            pintar(img, x, y, TRONCO[indice])


def frutinhas(img, cx, cy, paleta, rng, quantidade=7):
    for _ in range(quantidade):
        x = cx + rng.randint(-3, 3)
        y = cy + rng.randint(-2, 3)
        pintar(img, x, y, paleta[1])
        pintar(img, x, y - 1, paleta[2])


# ------------------------------------------------------------------ props

def arvore_frondosa(nome, semente, paleta=FOLHA, flores=None):
    rng = random.Random(semente)
    img = tela(112, 128)
    sombra_eliptica(img, 56, 118, 34, 8)
    tronco(img, 56, 70, 118, 10, rng)
    blobs = [(56, 46, 30), (32, 58, 20), (80, 58, 20), (42, 30, 20), (72, 30, 20), (56, 20, 18)]
    copa(img, blobs, paleta, rng)
    if flores:
        for _ in range(9):
            cx, cy, r = rng.choice(blobs)
            frutinhas(img, cx + rng.randint(-r // 2, r // 2), cy + rng.randint(-r // 2, r // 3), flores, rng, 3)
    contornar(img)
    salvar(img, nome)


def arvore_alta(nome, semente, paleta=FOLHA_ESCURA):
    rng = random.Random(semente)
    img = tela(80, 144)
    sombra_eliptica(img, 40, 134, 24, 7)
    tronco(img, 40, 60, 134, 8, rng)
    blobs = [(40, 88, 22), (40, 62, 22), (40, 38, 18), (40, 18, 13), (26, 76, 14), (54, 74, 14)]
    copa(img, blobs, paleta, rng)
    contornar(img)
    salvar(img, nome)


def palmeira_acai(nome, semente):
    """Açaizeiro: tronco fino e curvo, folhas longas em leque e cachos roxos de açaí."""
    rng = random.Random(semente)
    img = tela(96, 136)
    sombra_eliptica(img, 50, 128, 20, 5)
    # tronco curvo
    topo = (44, 34)
    for y in range(topo[1], 128):
        t = (y - topo[1]) / (128 - topo[1])
        x = int(topo[0] + math.sin(t * math.pi * 0.8) * 6)
        for dx in range(-2, 3):
            indice = 3 if dx < 0 else (2 if dx == 0 else 1)
            if (y % 6) == 0:
                indice = 0
            pintar(img, x + dx, y, TRONCO[indice])
    # folhas em leque
    for i in range(9):
        angulo = math.radians(-170 + i * 20 + rng.uniform(-6, 6))
        comprimento = rng.uniform(30, 40)
        for passo in range(int(comprimento)):
            t = passo / comprimento
            queda = t * t * 14  # as folhas pendem nas pontas
            x = topo[0] + math.cos(angulo) * passo
            y = topo[1] + math.sin(angulo) * passo + queda
            cor = FOLHA[3] if t < 0.4 else FOLHA[2]
            pintar(img, int(x), int(y), cor)
            # folíolos dos dois lados
            if passo % 2 == 0 and passo > 3:
                perp = angulo + math.pi / 2
                tam = 4 * (1 - t) + 1
                for lado in (-1, 1):
                    for k in range(1, int(tam) + 1):
                        fx = x + math.cos(perp) * lado * k * 0.6
                        fy = y + math.sin(perp) * lado * k * 0.6 + k * 0.7
                        pintar(img, int(fx), int(fy), FOLHA[1] if lado > 0 else FOLHA[2])
    # cachos de açaí logo abaixo das folhas
    for dx in (-6, 6):
        for _ in range(14):
            x = topo[0] + dx + rng.randint(-3, 3)
            y = topo[1] + 6 + rng.randint(0, 7)
            pintar(img, x, y, ACAI[rng.randint(0, 2)])
    contornar(img)
    salvar(img, nome)


def arbusto(nome, semente, flores=None):
    rng = random.Random(semente)
    img = tela(48, 36)
    sombra_eliptica(img, 24, 31, 20, 4)
    copa(img, [(24, 20, 12), (13, 24, 9), (35, 24, 9), (24, 12, 8)], FOLHA, rng)
    if flores:
        for _ in range(7):
            x, y = rng.randint(10, 38), rng.randint(9, 28)
            if img[y, x, 3]:
                pintar(img, x, y, flores[1])
                pintar(img, x + 1, y, flores[2])
                pintar(img, x, y + 1, flores[0])
    contornar(img)
    salvar(img, nome)


def samambaia(nome, semente):
    rng = random.Random(semente)
    img = tela(44, 32)
    base = (22, 29)
    for i in range(7):
        angulo = math.radians(-160 + i * 23 + rng.uniform(-5, 5))
        comprimento = rng.uniform(13, 18)
        for passo in range(int(comprimento)):
            t = passo / comprimento
            x = base[0] + math.cos(angulo) * passo
            y = base[1] + math.sin(angulo) * passo + t * t * 6
            pintar(img, int(x), int(y), FOLHA[2])
            if passo % 2 == 0 and passo > 1:
                for lado in (-1, 1):
                    perp = angulo + math.pi / 2
                    tam = 3 * (1 - t) + 1
                    for k in range(1, int(tam) + 1):
                        pintar(img, int(x + math.cos(perp) * lado * k), int(y + math.sin(perp) * lado * k),
                               FOLHA[3] if lado < 0 else FOLHA[1])
    contornar(img)
    salvar(img, nome)


def flores(nome, paleta, semente):
    rng = random.Random(semente)
    img = tela(24, 20)
    for _ in range(4):
        cx, cy = rng.randint(5, 18), rng.randint(5, 14)
        for y in range(cy + 1, min(cy + 5, 20)):  # caule
            pintar(img, cx, y, FOLHA[1])
        pintar(img, cx + 1, cy + 3, FOLHA[3])
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):  # pétalas
            pintar(img, cx + dx, cy + dy, paleta[1])
        pintar(img, cx - 1, cy - 1, paleta[2])
        pintar(img, cx, cy, FLORES["amarela"][2] if paleta is not FLORES["amarela"] else (255, 255, 255))
    contornar(img)
    salvar(img, nome)


def cogumelos(nome, semente):
    rng = random.Random(semente)
    img = tela(28, 24)
    for cx, cy, r in ((9, 13, 6), (19, 16, 4), (14, 19, 3)):
        for y in range(cy, cy + r + 2):  # pé
            pintar(img, cx, y, (230, 214, 190))
            pintar(img, cx - 1, y, (196, 176, 150))
        for y in range(cy - r, cy + 1):  # chapéu
            for x in range(cx - r, cx + r + 1):
                if ((x - cx) / r) ** 2 + ((y - cy) / (r * 0.8)) ** 2 <= 1:
                    indice = 2 if (x < cx and y < cy - r / 2) else (1 if y < cy else 0)
                    pintar(img, x, y, COGUMELO[indice])
        for _ in range(r // 2 + 1):  # pintinhas
            pintar(img, cx + rng.randint(-r + 2, r - 2), cy - rng.randint(1, max(r - 2, 1)), (255, 236, 200))
    contornar(img)
    salvar(img, nome)


def vitoria_regia(nome, semente, com_flor):
    rng = random.Random(semente)
    img = tela(40, 28)
    for cx, cy, r in ((14, 15, 10), (29, 18, 7), (26, 8, 5)):
        corte = rng.uniform(0, 2 * math.pi)
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = math.hypot(x - cx, (y - cy) * 1.3)
                if d > r:
                    continue
                a = math.atan2(y - cy, x - cx)
                if abs((a - corte + math.pi) % (2 * math.pi) - math.pi) < 0.25:
                    continue  # o corte em "V" da folha
                borda = d > r - 1.5
                pintar(img, x, y, FOLHA[1] if borda else FOLHA[3] if (x + y) % 5 else FOLHA[4])
    if com_flor:
        cx, cy = 14, 12
        for dx, dy in ((0, -2), (-2, 0), (2, 0), (-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)):
            pintar(img, cx + dx, cy + dy, FLORES["rosa"][1])
        pintar(img, cx, cy - 1, FLORES["rosa"][2])
        pintar(img, cx, cy, FLORES["amarela"][1])
    contornar(img)
    salvar(img, nome)


# ------------------------------------------------------------------ gramado

# Verde-oliva apagado e úmido, puxando para a terra, para combinar com o pântano.
GRAMA = [(34, 40, 30), (42, 49, 35), (51, 58, 40), (61, 68, 45), (74, 80, 52)]
GRAMA_FOLHA_CLARA = (90, 96, 60)
GRAMA_SOMBRA = (26, 30, 24)
# Matriz de Bayer 4x4: faz a transição entre tons com padrão de pixel art, sem chiado.
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

# Áreas que ficam sem grama, em pixels da arena (1152 x 648), tiradas do TileMap do Cenario:
# a clareira da árvore sagrada e as quatro poças.
CLAREIRA = (480, 256, 672, 416)
POCAS = [(32, 384, 128, 480), (288, 32, 416, 96), (672, 512, 800, 608), (960, 160, 1088, 256)]


def ruido_suave(largura, altura, escala, rng):
    """Ruído de valor interpolado, entre 0 e 1."""
    grade = np.array([[rng.random() for _ in range(largura // escala + 2)] for _ in range(altura // escala + 2)])
    ys, xs = np.mgrid[0:altura, 0:largura] / escala
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = grade[y0, x0] * (1 - fx) + grade[y0, x0 + 1] * fx
    b = grade[y0 + 1, x0] * (1 - fx) + grade[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def dentro_da_elipse(xs, ys, retangulo, folga, irregular):
    """Elipse inscrita no retângulo, com borda irregular. Folga negativa encolhe a elipse."""
    x0, y0, x1, y1 = retangulo
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2 + folga, (y1 - y0) / 2 + folga
    return np.hypot((xs - cx) / rx, (ys - cy) / ry) < 1 + irregular


def tufo(img, x, y, rng):
    """Tufo de grama em pixel art: 3 a 5 folhas finas, claras em cima e com sombra embaixo."""
    h, w = img.shape[:2]
    folhas = rng.choice(((-1, 0, 1), (-2, 0, 2), (-1, 1), (-2, -1, 1, 2), (-2, 0, 1, 2)))
    for dx in folhas:
        altura_folha = 3 if dx == 0 else 2
        for k in range(altura_folha):
            px, py = x + dx + (dx > 0 and k == altura_folha - 1) - (dx < 0 and k == altura_folha - 1), y - k
            if 0 <= px < w and 0 <= py < h and img[py, px, 3]:
                img[py, px] = (*(GRAMA_FOLHA_CLARA if k == altura_folha - 1 else GRAMA[4]), 255)
    for dx in range(-2, 3):
        if 0 <= x + dx < w and y + 1 < h and img[y + 1, x + dx, 3]:
            img[y + 1, x + dx] = (*GRAMA_SOMBRA, 255)


def gramado(nome, semente):
    """Camada de grama para cobrir a terra da arena, deixando a clareira e as poças à mostra."""
    rng = random.Random(semente)
    largura, altura = 1152, 648
    ys, xs = np.mgrid[0:altura, 0:largura].astype(float)
    irregular = (ruido_suave(largura, altura, 10, rng) - 0.5) * 0.25

    # A grama cobre os cantos das poças, que ficam redondas. A clareira fica um pouco maior que o TileMap.
    sem_grama = dentro_da_elipse(xs, ys, CLAREIRA, 22, irregular)
    for poca in POCAS:
        sem_grama |= dentro_da_elipse(xs, ys, poca, -4, irregular * 0.6)

    # Manchas grandes e suaves de cor, quantizadas com dithering ordenado.
    tom = ruido_suave(largura, altura, 64, rng) * 0.55 + ruido_suave(largura, altura, 20, rng) * 0.45
    tom = (tom - tom.min()) / (tom.max() - tom.min())
    limiar = BAYER[ys.astype(int) % 4, xs.astype(int) % 4]
    indice = np.clip((tom * 3.2 + limiar - 0.5).astype(int) + 0, 0, 3)
    paleta = np.array([(*c, 255) for c in GRAMA[:4]], dtype=np.uint8)
    img = paleta[indice]

    # Sombra úmida em volta da terra e das poças, mais escura perto da borda.
    perto = np.zeros_like(sem_grama)
    for raio in (1, 2, 3):
        for dy, dx in ((raio, 0), (-raio, 0), (0, raio), (0, -raio), (raio, raio), (-raio, -raio)):
            perto |= np.roll(np.roll(sem_grama, dy, 0), dx, 1)
    img[perto & ~sem_grama & (limiar < 0.7)] = (*GRAMA_SOMBRA, 255)

    # Tufos espalhados, mais concentrados onde a grama é mais clara.
    for _ in range(2600):
        x, y = rng.randrange(3, largura - 3), rng.randrange(3, altura - 2)
        if rng.random() < 0.3 + tom[y, x] * 0.7:
            tufo(img, x, y, rng)

    img[sem_grama] = (0, 0, 0, 0)
    # Folhinhas avançando sobre a terra, para a borda não ficar reta.
    perto_da_grama = np.zeros_like(sem_grama)
    for dy, dx in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        perto_da_grama |= np.roll(np.roll(~sem_grama, dy, 0), dx, 1)
    for _ in range(4000):
        x, y = rng.randrange(2, largura - 2), rng.randrange(3, altura - 1)
        if sem_grama[y, x] and perto_da_grama[y, x]:
            img[y, x] = (*GRAMA[2], 255)
            img[y - 1, x] = (*GRAMA[3], 255)
    salvar(img, nome)


def main():
    gramado("gramado", 16)
    arvore_frondosa("arvore_frondosa", 1)
    arvore_frondosa("arvore_frondosa_flores", 2, flores=FLORES["amarela"])
    arvore_alta("arvore_alta", 4)
    palmeira_acai("palmeira_acai", 5)
    arbusto("arbusto", 6)
    arbusto("arbusto_flores_vermelhas", 7, flores=FLORES["vermelha"])
    arbusto("arbusto_flores_amarelas", 8, flores=FLORES["amarela"])
    samambaia("samambaia", 9)
    flores("flores_vermelhas", FLORES["vermelha"], 10)
    flores("flores_amarelas", FLORES["amarela"], 11)
    flores("flores_roxas", FLORES["roxa"], 12)
    cogumelos("cogumelos", 13)
    vitoria_regia("vitoria_regia", 14, com_flor=True)
    vitoria_regia("vitoria_regia_sem_flor", 15, com_flor=False)


if __name__ == "__main__":
    main()
