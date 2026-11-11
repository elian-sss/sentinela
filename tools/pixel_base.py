"""Funções de pixel art compartilhadas por gerar_personagens.py e gerar_interface.py."""

import math

import numpy as np

CONTORNO = (22, 32, 20, 255)
FOLHA = [(30, 72, 40), (44, 104, 50), (66, 138, 60), (104, 172, 72), (150, 204, 96)]
SOMBRA = (0, 0, 0, 90)


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
