"""Gera as peças da interface em pixel art (arte original do projeto).

Saída: assets/interface/*.png e icon.png na raiz (ícone do jogo).
Para gerar de novo: python tools/gerar_interface.py (requer Pillow e numpy).

Tudo é desenhado em "pixels de arte" e salvo com o dobro do tamanho, para casar com a fonte
(que no tamanho 16 também usa 2 pixels de tela por pixel de arte).
"""

import math
import os

import numpy as np
from PIL import Image

from gerar_personagens import CINZA, FOGO, MADEIRA, AMARELO, VIDRO, elipse, heroi, linha, px, retangulo
from pixel_base import contornar, tela

RAIZ = os.path.join(os.path.dirname(__file__), "..")
PASTA = os.path.join(RAIZ, "assets", "interface")
ESCALA = 2

# ------------------------------------------------------------------ paleta da interface

ESCURO = (18, 22, 16)
FUNDO_PAINEL = (22, 32, 26, 238)
MADEIRA_UI = [(52, 36, 24), (78, 54, 34), (108, 76, 46), (144, 104, 62), (180, 138, 84)]
OURO = [(150, 104, 30), (214, 166, 60), (250, 218, 120)]
CREME = (236, 226, 190)
VERDE_UI = [(30, 72, 40), (44, 104, 50), (66, 138, 60), (104, 172, 72), (150, 204, 96)]
CINZA_TECLA = [(70, 72, 80), (150, 154, 164), (206, 210, 218), (240, 242, 246)]


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


def salvar(img, nome, escala=ESCALA, pasta=PASTA):
    os.makedirs(pasta, exist_ok=True)
    imagem = Image.fromarray(img, "RGBA")
    if escala != 1:
        imagem = imagem.resize((imagem.width * escala, imagem.height * escala), Image.NEAREST)
    imagem.save(os.path.join(pasta, nome + ".png"))


def aparar_cantos(img, cor=(0, 0, 0, 0)):
    h, w = img.shape[:2]
    for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        img[y, x] = cor


# ------------------------------------------------------------------ painéis e botões (9 fatias)

def painel():
    """Moldura de madeira com fundo escuro translúcido. Margem de 5 pixels de arte."""
    img = tela(16, 16)
    camadas = [ESCURO, MADEIRA_UI[3], MADEIRA_UI[2], MADEIRA_UI[1], ESCURO]
    for i, cor in enumerate(camadas):
        retangulo(img, i, i, 15 - i, 15 - i, cor)
    retangulo(img, 5, 5, 10, 10, FUNDO_PAINEL)
    for i in range(1, 15):  # luz em cima e à esquerda, sombra embaixo e à direita
        px(img, i, 1, MADEIRA_UI[4])
        px(img, 1, i, MADEIRA_UI[4])
        px(img, i, 14, MADEIRA_UI[1])
        px(img, 14, i, MADEIRA_UI[1])
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):  # rebites dourados
        px(img, x, y, OURO[2])
    aparar_cantos(img)
    salvar(img, "painel")


def botao(nome, corpo, luz, sombra, borda=ESCURO, afundado=False):
    """Botão em relevo. Margem de 4 pixels de arte. O afundado desce 1 pixel e perde o degrau de baixo."""
    img = tela(12, 12)
    topo = 1 if afundado else 0
    retangulo(img, 0, topo, 11, 11, borda)
    retangulo(img, 1, topo + 1, 10, 10, corpo)
    retangulo(img, 1, topo + 1, 10, topo + 1, luz)
    if not afundado:
        retangulo(img, 1, 9, 10, 10, sombra)
    px(img, 0, topo, (0, 0, 0, 0))
    px(img, 11, topo, (0, 0, 0, 0))
    px(img, 0, 11, (0, 0, 0, 0))
    px(img, 11, 11, (0, 0, 0, 0))
    salvar(img, nome)


def foco():
    """Contorno dourado tracejado nos cantos, desenhado por cima do botão com foco."""
    img = tela(12, 12)
    for i in range(12):
        if i < 4 or i > 7:
            for x, y in ((i, 0), (i, 11), (0, i), (11, i)):
                px(img, x, y, OURO[2])
    aparar_cantos(img)
    salvar(img, "botao_foco")


def tecla():
    """Tecla de teclado clara, com degrau embaixo. Margem de 4 pixels de arte."""
    img = tela(12, 13)
    retangulo(img, 0, 0, 11, 12, ESCURO)
    retangulo(img, 1, 1, 10, 9, CINZA_TECLA[2])
    retangulo(img, 1, 1, 10, 1, CINZA_TECLA[3])
    retangulo(img, 1, 10, 10, 11, CINZA_TECLA[1])
    aparar_cantos(img)
    salvar(img, "tecla")


def mouse():
    img = tela(12, 16)
    for y in range(16):
        for x in range(12):
            if ((x - 5.5) / 5.6) ** 2 + ((y - 7.5) / 7.8) ** 2 <= 1:
                px(img, x, y, CINZA_TECLA[2] if y > 6 else CINZA_TECLA[3])
    for y in range(0, 7):  # botão esquerdo em destaque
        for x in range(0, 6):
            if img[y, x, 3]:
                px(img, x, y, FOGO[1])
    retangulo(img, 5, 0, 6, 6, CINZA_TECLA[0])
    retangulo(img, 0, 7, 11, 7, CINZA_TECLA[0])
    contornar(img)
    salvar(img, "mouse")


# ------------------------------------------------------------------ ícones

def moldura_redonda(img, cor_fundo):
    h, w = img.shape[:2]
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - (w - 1) / 2, y - (h - 1) / 2)
            if d <= w / 2 - 0.4:
                borda = d > w / 2 - 2.6
                px(img, x, y, MADEIRA_UI[3] if borda and x + y < w else MADEIRA_UI[1] if borda else cor_fundo)


def retrato_sentinela():
    img = tela(24, 24)
    moldura_redonda(img, (40, 66, 44))
    rosto = heroi(0, 0)[0:19, 16:33]  # cabeça e cabelo do sprite do herói
    for y in range(rosto.shape[0]):
        for x in range(rosto.shape[1]):
            if rosto[y, x, 3] and img[y + 4, x + 3, 3]:
                img[y + 4, x + 3] = rosto[y, x]
    salvar(img, "retrato_sentinela")


def icone_escavadeira():
    img = tela(24, 24)
    moldura_redonda(img, (70, 50, 40))
    miolo = tela(24, 24)
    retangulo(miolo, 4, 16, 17, 19, CINZA[1])  # esteira
    for x in range(5, 18, 3):
        px(miolo, x, 17, CINZA[3])
    retangulo(miolo, 5, 12, 16, 15, AMARELO[1])  # base
    retangulo(miolo, 5, 7, 11, 12, AMARELO[2])  # cabine
    retangulo(miolo, 6, 8, 10, 10, VIDRO[1])
    linha(miolo, 11, 10, 16, 5, AMARELO[1], 2)  # braço
    linha(miolo, 17, 6, 19, 11, AMARELO[1], 2)
    retangulo(miolo, 17, 11, 20, 14, CINZA[2])  # caçamba
    contornar(miolo)
    for y in range(24):
        for x in range(24):
            if miolo[y, x, 3] and img[y, x, 3]:
                img[y, x] = miolo[y, x]
    salvar(img, "icone_escavadeira")


def icone_dash():
    img = tela(12, 12)
    azul = [(60, 120, 170), (120, 190, 230), (214, 240, 255)]
    for desloc, cor in ((0, azul[1]), (5, azul[2])):
        for i in range(5):
            px(img, 1 + desloc + min(i, 4 - i) * 1 + (i if i < 3 else 4 - i) * 0, 1 + i * 2, cor)
            px(img, 2 + desloc + (i if i < 3 else 4 - i), 1 + i * 2, cor)
            px(img, 2 + desloc + (i if i < 3 else 4 - i), 2 + i * 2, cor)
    contornar(img)
    salvar(img, "icone_dash")


def pip_onda(nome, cheia):
    """Folhinha que marca cada onda no topo da tela."""
    img = tela(10, 10)
    cores = (VERDE_UI[4], VERDE_UI[2], VERDE_UI[1]) if cheia else ((70, 76, 70), (52, 58, 54), (40, 46, 42))
    folha(img, 1, 8, -45, 10, 2.6, cores[0], cores[1], cores[2])
    contornar(img)
    salvar(img, nome)


def seta_continuar():
    img = tela(7, 9)
    for y in range(9):
        largura = 1 + min(y, 8 - y)
        retangulo(img, 1, y, largura, y, OURO[2] if y < 4 else OURO[1])
    contornar(img)
    salvar(img, "seta_continuar")


def icone_som(nome, tipo, ligado):
    img = tela(14, 14)
    cor = CREME if ligado else (120, 116, 104)
    if tipo == "musica":
        retangulo(img, 5, 2, 6, 10, cor)
        retangulo(img, 5, 2, 11, 3, cor)
        retangulo(img, 10, 2, 11, 8, cor)
        elipse(img, 4, 10, 2, 1.6, cor)
        elipse(img, 9, 8, 2, 1.6, cor)
    else:
        retangulo(img, 2, 5, 4, 8, cor)
        for i in range(4):
            retangulo(img, 5 + i, 4 - i + 1, 5 + i, 9 + i - 1, cor)
        if ligado:
            for y in range(4, 10):
                px(img, 10 + (0 if y in (4, 9) else 1), y, cor)
    if not ligado:
        linha(img, 2, 12, 12, 2, FOGO[1], 2)
    contornar(img)
    salvar(img, nome)


# ------------------------------------------------------------------ logo

LETRAS_LOGO = {
    "S": [".#####.", "#######", "##...##", "###....", ".#####.", "....###", "##...##", "#######", ".#####."],
    "E": ["#######", "#######", "##.....", "#####..", "#####..", "##.....", "##.....", "#######", "#######"],
    "N": ["##...##", "###..##", "###..##", "####.##", "##.####", "##..###", "##..###", "##...##", "##...##"],
    "T": ["#######", "#######", "..###..", "..###..", "..###..", "..###..", "..###..", "..###..", "..###.."],
    "I": ["#####", "#####", ".###.", ".###.", ".###.", ".###.", ".###.", "#####", "#####"],
    "L": ["##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "#######", "#######"],
    "A": ["..###..", ".#####.", "###.###", "##...##", "##...##", "#######", "#######", "##...##", "##...##"],
}
FAIXAS_LOGO = [(246, 244, 176), (206, 232, 124), (158, 208, 98), (112, 178, 76), (72, 144, 62), (46, 108, 52)]


def logo():
    """SENTINELA em letras de bloco com degradê de folha, contorno, sombra, cipó e a chama do Curupira no I."""
    celula, vao, margem = 4, 3, 12
    palavra = "SENTINELA"
    largura = sum(len(LETRAS_LOGO[c][0]) * celula for c in palavra) + vao * (len(palavra) - 1) + margem * 2
    altura = 9 * celula + margem * 2 + 6
    mascara = np.zeros((altura, largura), dtype=bool)
    x = margem
    inicios = {}
    for i, c in enumerate(palavra):
        inicios[i] = x
        for linha_i, texto in enumerate(LETRAS_LOGO[c]):
            for col, ch in enumerate(texto):
                if ch == "#":
                    mascara[margem + linha_i * celula:margem + (linha_i + 1) * celula,
                            x + col * celula:x + (col + 1) * celula] = True
        x += len(LETRAS_LOGO[c][0]) * celula + vao
    # arredonda as quinas vivas
    cheio = np.pad(mascara, 1)
    cima, baixo, esq, dir_ = cheio[:-2, 1:-1], cheio[2:, 1:-1], cheio[1:-1, :-2], cheio[1:-1, 2:]
    quina = mascara & ((~cima & ~esq) | (~cima & ~dir_) | (~baixo & ~esq) | (~baixo & ~dir_))
    mascara &= ~quina

    img = tela(largura, altura)
    # sombra deslocada
    for y, xx in zip(*np.nonzero(mascara)):
        for dy, dx in ((2, 2), (3, 2), (2, 3), (3, 3)):
            px(img, xx + dx, y + dy, (6, 10, 6, 170))
    # preenchimento em faixas com transição pontilhada
    altura_letra = 9 * celula
    for y, xx in zip(*np.nonzero(mascara)):
        t = (y - margem) / altura_letra * len(FAIXAS_LOGO)
        faixa = int(t)
        if t - faixa > 0.7 and (xx + y) % 2 == 0:
            faixa += 1
        px(img, xx, y, FAIXAS_LOGO[min(faixa, len(FAIXAS_LOGO) - 1)])
    # relevo: luz na borda de cima, sombra na de baixo
    cheio = np.pad(mascara, 1)
    cima, baixo = cheio[:-2, 1:-1], cheio[2:, 1:-1]
    for y, xx in zip(*np.nonzero(mascara & ~cima)):
        px(img, xx, y, (255, 255, 224))
    for y, xx in zip(*np.nonzero(mascara & ~baixo)):
        px(img, xx, y, (28, 70, 40))
    # contorno escuro de 1 pixel (com diagonais, para ficar encorpado)
    borda = np.zeros_like(mascara)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            borda |= np.roll(np.roll(mascara, dy, 0), dx, 1)
    for y, xx in zip(*np.nonzero(borda & ~mascara)):
        px(img, xx, y, (14, 22, 12))

    # cipó com folhas por baixo das letras
    y_cipo = margem + altura_letra + 5
    for xx in range(margem - 4, largura - margem + 4):
        y = y_cipo + round(math.sin(xx * 0.09) * 2)
        px(img, xx, y, VERDE_UI[1])
        px(img, xx, y + 1, VERDE_UI[0])
    for i, xx in enumerate(range(margem + 6, largura - margem, 22)):
        y = y_cipo + round(math.sin(xx * 0.09) * 2)
        folha(img, xx, y, -50 if i % 2 == 0 else 40, 7, 2.2, VERDE_UI[4], VERDE_UI[2], VERDE_UI[1])
    # brotos saindo do S e do A
    folha(img, inicios[0] + 3, margem + 1, -120, 8, 2.4, VERDE_UI[4], VERDE_UI[2], VERDE_UI[1])
    folha(img, inicios[8] + 24, margem + 2, -40, 8, 2.4, VERDE_UI[4], VERDE_UI[2], VERDE_UI[1])
    # chama do Curupira em cima do I
    cx = inicios[4] + 10
    for dy in range(9):
        meia = [1, 2, 3, 3, 3, 2, 2, 1, 0][dy]
        for dx in range(-meia, meia + 1):
            cor = FOGO[3] if abs(dx) <= meia - 2 and dy < 5 else FOGO[2] if abs(dx) < meia else FOGO[1]
            px(img, cx + dx + (1 if dy > 6 else 0), margem - 3 - dy, cor)
    for dy in range(9):  # contorno escuro só em volta da chama
        for dx in range(-5, 6):
            xx, y = cx + dx, margem - 3 - dy
            if img[y, xx, 3] == 0 and any(tuple(img[y + ay, xx + ax][:3]) in (FOGO[1], FOGO[2], FOGO[3])
                                         for ay, ax in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px(img, xx, y, (60, 20, 14))
    salvar(img, "logo")
    return img


def icone_do_jogo():
    """Ícone 128 x 128: o rosto do Sentinela sobre um fundo de mata."""
    img = tela(32, 32)
    retangulo(img, 0, 0, 31, 31, (30, 56, 36))
    for y in range(32):
        for x in range(32):
            if (x * 7 + y * 13) % 11 == 0:
                px(img, x, y, (40, 72, 44))
    retangulo(img, 0, 0, 31, 0, ESCURO)
    retangulo(img, 0, 31, 31, 31, ESCURO)
    retangulo(img, 0, 0, 0, 31, ESCURO)
    retangulo(img, 31, 0, 31, 31, ESCURO)
    aparar_cantos(img)
    rosto = heroi(0, 0)[0:26, 13:37]
    for y in range(rosto.shape[0]):
        for x in range(rosto.shape[1]):
            if rosto[y, x, 3]:
                img[y + 4, x + 4] = rosto[y, x]
    salvar(img, "icon", escala=4, pasta=RAIZ)


def main():
    painel()
    botao("botao_normal", MADEIRA_UI[2], MADEIRA_UI[4], MADEIRA_UI[0])
    botao("botao_hover", MADEIRA_UI[3], OURO[2], MADEIRA_UI[1], borda=OURO[1])
    botao("botao_pressionado", MADEIRA_UI[1], MADEIRA_UI[0], MADEIRA_UI[0], afundado=True)
    botao("botao_desativado", (70, 66, 60), (96, 92, 84), (48, 46, 42))
    botao("botao_verde_normal", VERDE_UI[2], VERDE_UI[4], VERDE_UI[0])
    botao("botao_verde_hover", VERDE_UI[3], (220, 244, 150), VERDE_UI[1], borda=OURO[1])
    botao("botao_verde_pressionado", VERDE_UI[1], VERDE_UI[0], VERDE_UI[0], afundado=True)
    foco()
    tecla()
    mouse()
    retrato_sentinela()
    icone_escavadeira()
    icone_dash()
    pip_onda("pip_onda_cheia", True)
    pip_onda("pip_onda_vazia", False)
    seta_continuar()
    for tipo in ("musica", "efeitos"):
        icone_som(f"icone_{tipo}_ligado", tipo, True)
        icone_som(f"icone_{tipo}_desligado", tipo, False)
    logo()
    icone_do_jogo()


if __name__ == "__main__":
    main()
