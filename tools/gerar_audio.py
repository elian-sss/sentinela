#!/usr/bin/env python3
"""Gera todo o áudio do Sentinela por síntese, sem nenhum sample de terceiros.

Uso:  python tools/gerar_audio.py
Requer numpy e scipy. Usa o ffmpeg (libvorbis) para salvar .ogg; sem ffmpeg, salva .wav.
Saída (mono, 44,1 kHz):
  assets/audio/efeitos/*.ogg   efeitos normalizados em pico de -6 dBFS
  assets/audio/musica/*.ogg    loops perfeitos normalizados em RMS de -14 dBFS (pico <= -1 dBFS)

Músicas (todas giram em torno do mesmo motivo, o "tema da Samaúma": sol, dó, ré, mi | sol, mi, ré):
  musica_menu      tema completo, calmo, em Fá maior
  musica_calmaria  respiro entre as ondas: floresta na frente e pedaços do tema
  musica_combate   carimbó em Ré menor: curimbós, maracas, banjo, marimba e o tema em menor
  musica_chefe     a máquina: pulso de motor, batidas de metal e o tema escurecido
  musica_vitoria   tema em Ré maior, em clima de festa mansa
Instrumentos: flauta, marimba, calimba, corda dedilhada (banjo), coro (pad), baixo, curimbós,
maracas, bumbo, bigorna e motor.

É reproduzível: cada som tem a sua própria semente fixa, e o ffmpeg roda em modo bitexact.
Para que as músicas fechem o loop sem estalo, todo som é colocado num buffer circular:
o que passa do fim volta no começo, e o vento e o reverb são filtrados no domínio da frequência.
"""
import os
import shutil
import subprocess
import tempfile
import zlib

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
SEMENTE = 2026
PICO_EFEITOS_DB = -6.0
RMS_MUSICA_DB = -14.0
TETO_MUSICA_DB = -1.0
QUALIDADE_OGG_EFEITOS = 4
QUALIDADE_OGG_MUSICA = 3

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_EFEITOS = os.path.join(RAIZ, "assets", "audio", "efeitos")
PASTA_MUSICA = os.path.join(RAIZ, "assets", "audio", "musica")
FFMPEG = shutil.which("ffmpeg")

rng = np.random.default_rng(SEMENTE)


# ---------------------------------------------------------------- utilidades

def semear(nome):
    """Cada som tem a sua própria semente: mexer em um não muda os outros."""
    global rng
    rng = np.random.default_rng([SEMENTE, zlib.crc32(nome.encode())])


def db(valor):
    return 10 ** (valor / 20)


def amostras(segundos):
    return int(round(segundos * SR))


def tempo(segundos):
    return np.arange(amostras(segundos)) / SR


def ruido(n):
    return rng.standard_normal(n)


def filtrar(x, tipo, freq, ordem=2):
    sos = signal.butter(ordem, freq, btype=tipo, fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def unitario(x):
    pico = np.max(np.abs(x))
    return x / pico if pico > 0 else x


def fase(freqs):
    """Fase acumulada para uma frequência que varia amostra a amostra."""
    return 2 * np.pi * np.cumsum(freqs) / SR


def bordas(x, entrada=0.004, saida=0.02):
    """Rampa curta no começo e no fim para não estalar."""
    x = x.copy()
    a, r = min(len(x), amostras(entrada)), min(len(x), amostras(saida))
    if a > 0:
        x[:a] *= np.linspace(0, 1, a)
    if r > 0:
        x[-r:] *= np.linspace(1, 0, r)
    return x


def a_partir_de(t, inicio):
    """Tempo relativo a partir de `inicio` (negativo antes) e a máscara de onde já começou."""
    rel = t - inicio
    return rel, rel >= 0


def encaixar(x, som, inicio, ganho=1.0):
    """Soma `som` em `x` a partir de `inicio` segundos, cortando o que passar do fim."""
    i = amostras(inicio)
    parte = som[:max(len(x) - i, 0)]
    x[i:i + len(parte)] += ganho * parte


def varredura_filtrada(x, f_ini, f_fim, q=1.5):
    """Passa-faixa de estado variável com o centro indo de f_ini a f_fim (exponencial)."""
    n = len(x)
    fc = f_ini * (f_fim / f_ini) ** (np.arange(n) / max(n - 1, 1))
    f = 2 * np.sin(np.pi * fc / SR)
    amortecimento = 1 / q
    baixa = faixa = 0.0
    saida = np.empty(n)
    for i in range(n):
        alta = x[i] - baixa - amortecimento * faixa
        faixa += f[i] * alta
        baixa += f[i] * faixa
        saida[i] = faixa
    return saida


def tom_harmonico(freqs, harmonicos):
    """Soma de harmônicos [(multiplicador, amplitude), ...] sobre uma frequência variável."""
    ph = fase(freqs)
    return sum(a * np.sin(k * ph) for k, a in harmonicos)


def serra(freqs):
    return 2 * ((fase(freqs) / (2 * np.pi)) % 1) - 1


SEMITONS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(nome):
    """'A4' -> 440.0. Aceita sustenido e bemol: 'F#5', 'Bb2'."""
    semitom = SEMITONS[nome[0]] + nome.count("#") - nome[1:-1].count("b")
    return 440.0 * 2 ** ((semitom - 9) / 12 + int(nome[-1]) - 4)


def nota(base_hz, escala, grau):
    oitava, i = divmod(grau, len(escala))
    return base_hz * 2 ** ((escala[i] + 12 * oitava) / 12)


# ruídos já filtrados, fatiados por cada nota (mais rápido que filtrar nota a nota)
SOPRO = unitario(filtrar(ruido(amostras(4)), "bandpass", [1200, 6000]))
AREIA = unitario(filtrar(ruido(amostras(3)), "highpass", 5000, 4))
PELE = unitario(filtrar(ruido(amostras(3)), "bandpass", [500, 2500]))


def fatia(buffer, n):
    inicio = rng.integers(0, len(buffer) - n)
    return buffer[inicio:inicio + n]


# ---------------------------------------------------------------- instrumentos

def flauta(freq, duracao, sopro=0.08, vibrato=0.004):
    """Flauta de bambu: o tom sobe no ataque, o vibrato entra depois; 4 harmônicos e ruído de sopro."""
    n = amostras(duracao + 0.15)
    t = np.arange(n) / SR
    profundidade = vibrato * np.clip((t - 0.15) / 0.2, 0, 1)
    f = freq * (1 - 0.012 * np.exp(-t / 0.025)) * (1 + profundidade * np.sin(2 * np.pi * 5.2 * t))
    tom = tom_harmonico(f, [(1, 1), (2, 0.22), (3, 0.08), (4, 0.03)])
    envelope = np.clip(t / 0.05, 0, 1) * np.clip((duracao + 0.12 - t) / 0.12, 0, 1) * 0.9
    ataque = 1 + 1.5 * np.exp(-t / 0.04)
    return (tom + sopro * fatia(SOPRO, n) * ataque) * envelope


def tecla(freq, tau, parciais, baqueta):
    """Tecla percutida: fundamental, parciais [(razão, ganho, fração do tau)] e o toque da baqueta."""
    t = tempo(min(5 * tau, 1.6))
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t / tau)
    for razao, ganho, fracao in parciais:
        x += ganho * np.sin(2 * np.pi * freq * razao * t) * np.exp(-t / (tau * fracao))
    x += baqueta * fatia(SOPRO, len(t)) * np.exp(-t / 0.004)
    return bordas(x, 0.001, 0.03)


def marimba(freq, _duracao=0.0):
    """Tecla de madeira: curta, com o 2º parcial duas oitavas acima (4x) e um estalo de baqueta."""
    return tecla(freq, 0.22 * (440 / freq) ** 0.5, [(4, 0.3, 0.3), (9.2, 0.1, 0.1)], 0.2)


def calimba(freq, _duracao=0.0):
    """Lâmina de metal: soa mais longa e limpa, com um 'tim' agudo no ataque."""
    return tecla(freq, 0.4 * (440 / freq) ** 0.5, [(2, 0.1, 0.6), (5.4, 0.2, 0.12)], 0.08)


def corda(freq, _duracao=0.0):
    """Corda dedilhada, tipo banjo: muitos harmônicos, e os mais agudos somem primeiro."""
    t = tempo(0.5)
    x = np.zeros(len(t))
    for k in range(1, int(6000 / freq) + 1):
        x += np.sin(np.pi * k * 0.22) / k * np.sin(2 * np.pi * k * freq * t) * np.exp(-t * (4 + 2.2 * k))
    x += 0.3 * fatia(SOPRO, len(t)) * np.exp(-t / 0.003)
    return bordas(unitario(x), 0.001, 0.03)


def coro(freq, duracao):
    """Pad de vozes: três vozes levemente desafinadas, harmônicos moldados por formantes de 'ô', ataque lento."""
    n = amostras(duracao + 0.7)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for desvio in (-7, 0, 7):  # em cents
        f = freq * 2 ** (desvio / 1200)
        for k in range(1, int(2600 / f) + 1):
            formante = np.exp(-((k * f - 480) / 260) ** 2) + 0.45 * np.exp(-((k * f - 950) / 320) ** 2) + 0.05
            x += formante / k * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    ataque = min(0.6, duracao / 2)
    envelope = (np.sin(0.5 * np.pi * np.clip(t / ataque, 0, 1)) ** 2
                * np.cos(0.5 * np.pi * np.clip((t - duracao) / 0.7, 0, 1)) ** 2)
    return x / np.sqrt(np.mean(x ** 2)) * 0.25 * envelope


def baixo(freq, duracao):
    n = amostras(duracao + 0.08)
    t = np.arange(n) / SR
    tom = tom_harmonico(np.full(n, freq), [(1, 1), (2, 0.35), (3, 0.12)])
    envelope = np.clip(t / 0.01, 0, 1) * (0.6 + 0.4 * np.exp(-t / 0.1)) * np.clip((duracao + 0.06 - t) / 0.06, 0, 1)
    return tom * envelope


def curimbo(forca, freq=110.0, aberto=True):
    """Tambor de tronco tocado com as mãos: corpo com queda de tom, modos da pele e o tapa."""
    tau = 0.15 if aberto else 0.05
    t = tempo(4 * tau)
    ph = fase(freq * (1 + 0.5 * np.exp(-t / 0.018)))
    corpo = (np.sin(ph) * np.exp(-t / tau) + 0.35 * np.sin(1.59 * ph) * np.exp(-t / (0.5 * tau))
             + 0.15 * np.sin(2.14 * ph) * np.exp(-t / (0.3 * tau)))
    tapa = fatia(PELE, len(t)) * np.exp(-t / 0.008)
    return forca * bordas(corpo + (0.3 if aberto else 0.7) * tapa, 0.001, 0.02)


def bumbo(forca):
    t = tempo(0.5)
    corpo = np.sin(fase(58 + 75 * np.exp(-t / 0.03))) * np.exp(-t / 0.2)
    batida = unitario(filtrar(ruido(len(t)), "lowpass", 1500)) * np.exp(-t / 0.006)
    return forca * bordas(corpo + 0.3 * batida, 0.001, 0.02)


def chocalho(forca):
    n = amostras(0.09)
    t = np.arange(n) / SR
    return forca * fatia(AREIA, n) * np.clip(t / 0.004, 0, 1) * np.exp(-t / 0.035)


def bigorna(forca, freq=587.33, tau=0.11):
    """Pancada em metal: parciais inarmônicos de barra e um estalo agudo."""
    t = tempo(4.5 * tau)
    x = sum(g * np.sin(2 * np.pi * freq * r * t) * np.exp(-t * np.sqrt(r) / tau)
            for r, g in [(1, 1), (2.76, 0.7), (5.4, 0.45), (8.93, 0.25)] if freq * r < 0.45 * SR)
    x += 0.5 * fatia(AREIA, len(t)) * np.exp(-t / 0.003)
    return forca * bordas(x, 0.0005, 0.02)


def motor(freq, duracao, forca=1.0):
    """Um tranco de motor: serra uma oitava abaixo da nota, saturada, só entre 70 e 700 Hz."""
    n = amostras(duracao)
    t = np.arange(n) / SR
    x = np.tanh(2.5 * (serra(np.full(n, freq / 2)) + 0.5 * np.sin(2 * np.pi * freq * t)))
    x = filtrar(x, "bandpass", [70, 700])
    return forca * bordas(x * np.exp(-t / (0.4 * duracao)), 0.004, 0.02)


def sino(t, freq, inicio, tau):
    rel, m = a_partir_de(t, inicio)
    x = np.zeros(len(t))
    x[m] = (np.sin(2 * np.pi * freq * rel[m])
            + 0.3 * np.sin(2 * np.pi * freq * 2.76 * rel[m]) * np.exp(-rel[m] / 0.05))
    x[m] *= np.clip(rel[m] / 0.003, 0, 1) * np.exp(-rel[m] / tau)
    return x


def corne(t, freq, inicio, duracao):
    """Búzio / corne de madeira: harmônicos que caem, subida de tom no ataque e sopro."""
    rel, m = a_partir_de(t, inicio)
    x = np.zeros(len(t))
    r = rel[m]
    f = freq * (1 - 0.03 * np.exp(-r / 0.06)) * (1 + 0.004 * np.sin(2 * np.pi * 5 * r))
    tom = tom_harmonico(f, [(k, 1 / k ** 1.3) for k in range(1, 9)])
    envelope = np.clip(r / 0.06, 0, 1) * np.clip((duracao - r) / 0.15, 0, 1)
    x[m] = tom * envelope + 0.15 * fatia(SOPRO, len(r)) * envelope
    return x


def metal(t, freq, inicio, duracao, ganho=1.0):
    """Nota de metal (trompa) para as fanfarras."""
    rel, m = a_partir_de(t, inicio)
    x = np.zeros(len(t))
    r = rel[m]
    envelope = np.clip(r / 0.02, 0, 1) * np.clip((duracao - r) / 0.08, 0, 1)
    x[m] = ganho * tom_harmonico(np.full(len(r), freq), [(k, 1 / k) for k in range(1, 7)]) * envelope
    return x


def pancada_grave(t, inicio, base=55.0, queda=70.0, tau=0.25):
    """Batida grave com o tom caindo, usada como peso em fanfarras e impactos."""
    rel, m = a_partir_de(t, inicio)
    x = np.zeros(len(t))
    x[m] = np.sin(fase(base + queda * np.exp(-rel[m] / 0.03))) * np.exp(-rel[m] / tau)
    return x


# ---------------------------------------------------------------- efeitos

def efeito_golpe():
    t = tempo(0.24)
    n = len(t)
    whoosh = unitario(varredura_filtrada(ruido(n), 700, 3800, q=1.4))
    whoosh *= np.sin(np.pi * np.clip(t / 0.17, 0, 1)) ** 2
    rel, m = a_partir_de(t, 0.11)
    impacto = np.zeros(n)
    impacto[m] = np.sin(fase(90 + 140 * np.exp(-rel[m] / 0.02))) * np.exp(-rel[m] / 0.05)
    clique = np.zeros(n)
    clique[m] = filtrar(ruido(n), "highpass", 2500)[m] * np.exp(-rel[m] / 0.006)
    return 0.7 * whoosh + 0.9 * impacto + 0.25 * unitario(clique)


def efeito_golpe_acerto():
    """Cajado de madeira acertando: estalo seco com um pouco de corpo."""
    t = tempo(0.15)
    madeira = (np.sin(fase(300 + 250 * np.exp(-t / 0.008))) * np.exp(-t / 0.035)
               + 0.5 * np.sin(2 * np.pi * 760 * t) * np.exp(-t / 0.015)
               + 0.25 * np.sin(2 * np.pi * 1480 * t) * np.exp(-t / 0.008))
    corpo = np.sin(fase(110 + 80 * np.exp(-t / 0.02))) * np.exp(-t / 0.05)
    estalo = unitario(filtrar(ruido(len(t)), "bandpass", [1500, 6000])) * np.exp(-t / 0.004)
    return madeira + 0.7 * corpo + 0.45 * estalo


def efeito_dash():
    t = tempo(0.36)
    x = unitario(varredura_filtrada(ruido(len(t)), 400, 4500, q=1.1))
    envelope = (t / t[-1]) ** 1.2
    ar = unitario(filtrar(ruido(len(t)), "highpass", 6000)) * 0.15 * envelope
    return bordas(x * envelope + ar, 0.004, 0.07)


def efeito_dano_heroi():
    t = tempo(0.34)
    batida = np.sin(fase(55 + 110 * np.exp(-t / 0.05))) * np.exp(-t / 0.12)
    rel, m = a_partir_de(t, 0.02)
    queda = np.zeros(len(t))
    freq = 520 * (0.5 ** (rel[m] / 0.25))
    queda[m] = tom_harmonico(freq, [(1, 1), (3, 0.15)]) * np.exp(-rel[m] / 0.13)
    estalo = unitario(filtrar(ruido(len(t)), "lowpass", 1200)) * np.exp(-t / 0.02)
    return 1.0 * batida + 0.45 * queda + 0.3 * estalo


def efeito_vida_baixa():
    """Duas batidas de coração, graves e macias."""
    t = tempo(0.6)
    x = np.zeros(len(t))
    for inicio, ganho in [(0.0, 1.0), (0.24, 0.75)]:
        rel, m = a_partir_de(t, inicio)
        ph = fase(62 + 50 * np.exp(-rel[m] / 0.03))
        x[m] += ganho * (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.clip(rel[m] / 0.008, 0, 1) * np.exp(-rel[m] / 0.085)
    return filtrar(x, "lowpass", 400)


def efeito_dano_arvore():
    t = tempo(0.3)
    n = len(t)
    madeira = (np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.06)
               + 0.6 * np.sin(2 * np.pi * 540 * t) * np.exp(-t / 0.03))
    estalos = np.zeros(n)
    base = unitario(filtrar(ruido(n), "bandpass", [1500, 5000]))
    for inicio, ganho in [(0.0, 1.0), (0.028, 0.7), (0.065, 0.5)]:
        rel, m = a_partir_de(t, inicio)
        estalos[m] += ganho * base[m] * np.exp(-rel[m] / 0.009)
    clique = unitario(filtrar(ruido(n), "highpass", 4000)) * np.exp(-t / 0.002)
    return 0.8 * madeira + 0.7 * estalos + 0.3 * clique


def efeito_arvore_critica():
    """Tronco rangendo: trancos irregulares passando pelas ressonâncias da madeira, sobre um gemido grave."""
    t = tempo(0.9)
    n = len(t)
    arco = np.sin(np.pi * t / t[-1])
    taxa = (18 + 45 * arco ** 2) * (1 + 0.3 * unitario(filtrar(ruido(n), "lowpass", 12)))
    trancos = np.diff(np.floor(fase(taxa) / (2 * np.pi)), prepend=0.0) * rng.uniform(0.5, 1.0, n)
    rangido = sum(g * filtrar(trancos, "bandpass", [0.88 * f, 1.12 * f])
                  for f, g in [(160, 1.0), (390, 0.8), (880, 0.5), (1750, 0.25)])
    gemido = tom_harmonico(70 - 12 * t / t[-1] + 4 * np.sin(2 * np.pi * 6 * t),
                           [(1, 1), (2, 0.5), (3, 0.3), (4, 0.15)])
    return bordas(unitario(rangido) * arco ** 0.5 + 0.3 * gemido * arco, 0.01, 0.1)


def efeito_arvore_curada():
    """Seiva subindo: três tons que deslizam uma quinta acima, folhas e gotas de calimba."""
    t = tempo(0.6)
    n = len(t)
    arco = np.sin(np.pi * t / t[-1]) ** 1.2
    subida = 1.5 ** (t / t[-1])
    brilho = sum(np.sin(fase(hz(nome) * subida)) for nome in ["F4", "C5", "F5"])
    brilho *= 1 - 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t))
    folhas = unitario(varredura_filtrada(ruido(n), 1500, 6000, q=1.2))
    x = (0.3 * brilho + 0.25 * folhas) * arco
    for i, nome in enumerate(["F5", "A5", "C6", "F6"]):
        encaixar(x, calimba(hz(nome)), 0.08 + i * 0.11, 0.6)
    return bordas(x, 0.01, 0.12)


def efeito_inimigo_derrotado():
    t = tempo(0.5)
    n = len(t)
    puf = unitario(varredura_filtrada(ruido(n), 2600, 220, q=0.8))
    corpo = unitario(filtrar(ruido(n), "lowpass", 700))
    envelope = np.clip(t / 0.012, 0, 1) * np.exp(-t / 0.14)
    return bordas((0.8 * puf + 0.5 * corpo) * envelope, 0.002, 0.05)


def efeito_item_caiu():
    t = tempo(0.25)
    return sino(t, hz("C7"), 0.0, 0.06) + 0.7 * sino(t, hz("G7"), 0.045, 0.07)


def efeito_item_fruta():
    t = tempo(0.45)
    return sino(t, 1318.5, 0.0, 0.16) + 0.8 * sino(t, 1975.5, 0.07, 0.2)


def efeito_item_erva():
    t = tempo(0.75)
    x = np.zeros(len(t))
    for i, nome in enumerate(["C5", "E5", "G5", "C6"]):
        rel, m = a_partir_de(t, i * 0.075)
        x[m] += (tom_harmonico(np.full(m.sum(), hz(nome)), [(1, 1), (2, 0.1)])
                 * np.clip(rel[m] / 0.015, 0, 1) * np.exp(-rel[m] / 0.22))
    return filtrar(x, "lowpass", 5000)


def efeito_escudo():
    t = tempo(0.75)
    subida = 1 + 0.05 * t / t[-1]
    x = sum(tom_harmonico(hz(nome) * subida, [(1, 1)]) + tom_harmonico((hz(nome) + 3) * subida, [(1, 0.7)])
            for nome in ["C5", "G5", "C6"])
    x *= 1 - 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * 12 * t))
    brilho = unitario(varredura_filtrada(ruido(len(t)), 2000, 8000, q=2)) * 0.25
    envelope = np.clip(t / 0.03, 0, 1) * np.exp(-t / 0.35)
    return bordas((unitario(x) + brilho) * envelope, 0.003, 0.08)


def efeito_power_velocidade():
    """Pena da velocidade: sopro e assobio subindo, com faíscas no fim."""
    t = tempo(0.5)
    n = len(t)
    envelope = np.clip(t / 0.32, 0, 1) ** 1.5 * np.clip((0.46 - t) / 0.12, 0, 1)
    sopro = unitario(varredura_filtrada(ruido(n), 500, 6500, q=1.6))
    assobio = np.sin(fase(600 * 4 ** (t / 0.4)))
    x = (0.8 * sopro + 0.2 * assobio) * envelope
    for i, nome in enumerate(["C7", "E7", "G7", "C8"]):
        x += 0.45 * sino(t, hz(nome), 0.24 + i * 0.05, 0.05)
    return x


def efeito_power_forca():
    """Açaí da força: carga grave que cresce e estoura numa batida brilhante."""
    t = tempo(0.62)
    n = len(t)
    estouro = 0.36
    subindo = np.clip(t / estouro, 0, 1)
    carga = np.tanh(2 * tom_harmonico(55 * 2 ** subindo, [(1, 1), (2, 0.5), (3, 0.3)]))
    ronco = unitario(filtrar(ruido(n), "lowpass", 400))
    x = (0.7 * carga + 0.4 * ronco) * subindo ** 2 * np.clip((estouro + 0.03 - t) / 0.03, 0, 1)
    rel, m = a_partir_de(t, estouro)
    acorde_final = sum(tom_harmonico(np.full(m.sum(), hz(nome)), [(k, 1 / k) for k in range(1, 6)])
                       for nome in ["D4", "A4", "D5"])
    x[m] += 0.35 * acorde_final * np.exp(-rel[m] / 0.1)
    x[m] += 0.5 * unitario(filtrar(ruido(n), "highpass", 3000))[m] * np.exp(-rel[m] / 0.012)
    return x + 1.2 * pancada_grave(t, estouro, 70, 90, 0.1)


def efeito_onda_iniciada():
    t = tempo(1.25)
    x = corne(t, 146.83, 0.0, 0.45) + corne(t, 220.0, 0.4, 0.8)
    return filtrar(x, "lowpass", 1800)


def efeito_onda_concluida():
    """Começo do tema da Samaúma (sol, dó, ré, mi) fechando na oitava, em Fá maior."""
    t = tempo(0.9)
    x = np.zeros(len(t))
    for i, nome in enumerate(["C5", "F5", "G5", "A5"]):
        encaixar(x, marimba(hz(nome)), i * 0.1)
        x += 0.3 * sino(t, 2 * hz(nome), i * 0.1, 0.08)
    for nome in ["F5", "A5", "C6"]:
        encaixar(x, calimba(hz(nome)), 0.42, 0.8)
    x += 0.35 * sino(t, hz("C7"), 0.42, 0.2)
    return bordas(x, 0.002, 0.15)


def efeito_fogo_nasce():
    """Foco de fogo acendendo: sopro que abre, ronco grave e estalos."""
    t = tempo(0.6)
    n = len(t)
    sopro = unitario(varredura_filtrada(ruido(n), 250, 2200, q=0.9)) * np.clip(t / 0.06, 0, 1) * np.exp(-t / 0.2)
    grave = unitario(filtrar(ruido(n), "lowpass", 250)) * np.clip(t / 0.04, 0, 1) * np.exp(-t / 0.15)
    faiscas = (rng.random(n) < 0.0012) * rng.uniform(0.4, 1.0, n)
    estalos = unitario(filtrar(faiscas, "bandpass", [1800, 7000])) * np.clip(t / 0.08, 0, 1)
    return bordas(sopro + 0.6 * grave + 0.7 * estalos, 0.003, 0.2)


def efeito_fogo_apagado():
    """Fogo apagando: um 'pf' abafado e o chiado de vapor."""
    t = tempo(0.5)
    n = len(t)
    chiado = unitario(filtrar(ruido(n), "highpass", 3500, 4)) * np.clip(t / 0.012, 0, 1) * np.exp(-t / 0.16)
    abafado = unitario(varredura_filtrada(ruido(n), 1800, 500, q=1.0)) * np.exp(-t / 0.07)
    return bordas(chiado + 0.5 * abafado, 0.002, 0.1)


def efeito_motosserra():
    t = tempo(0.8)
    f = 70 + 60 * (1 - np.exp(-t / 0.15)) - 25 * t
    ronco = serra(f) + 0.5 * np.sin(fase(f / 2))
    explosoes = unitario(filtrar(ruido(len(t)), "bandpass", [300, 3000])) * (0.5 + 0.5 * serra(f))
    x = np.tanh(3 * (0.7 * ronco + 0.5 * explosoes))
    x = filtrar(x, "bandpass", [120, 3500])
    return bordas(x, 0.03, 0.12)


def efeito_escavadeira_investida():
    t = tempo(1.0)
    f = 45 + 35 * (1 - np.exp(-t / 0.3))
    giro = serra(f) + 0.6 * np.sign(np.sin(fase(f * 0.5)))
    ronco = unitario(filtrar(ruido(len(t)), "bandpass", [200, 900]))
    ronco *= 0.5 + 0.5 * np.sin(2 * np.pi * 30 * t)
    x = np.tanh(2.5 * (0.8 * giro + 0.6 * ronco))
    x = filtrar(x, "lowpass", 1500)
    envelope = np.clip(t / 0.15, 0, 1)
    return bordas(x * envelope, 0.01, 0.25)


def efeito_chefe_aviso():
    """Aviso da investida: dois bipes de alarme de ré sobre o motor acelerando."""
    t = tempo(0.9)
    bipes = np.zeros(len(t))
    for inicio in (0.0, 0.28):
        rel, m = a_partir_de(t, inicio)
        porta = np.clip(rel[m] / 0.005, 0, 1) * np.clip((0.18 - rel[m]) / 0.005, 0, 1)
        bipes[m] += tom_harmonico(np.full(m.sum(), 1150.0), [(1, 1), (3, 0.3), (5, 0.12)]) * porta
    f = 48 + 70 * (t / t[-1]) ** 2
    giro = np.tanh(2.5 * (serra(f) + 0.6 * np.sign(np.sin(fase(f / 2)))))
    giro = filtrar(giro, "lowpass", 1400) * (0.4 + 0.6 * t / t[-1])
    return bordas(0.6 * bipes + 0.7 * giro, 0.005, 0.08)


def motor_falhando(r, f_ini, tau_tom, tau_volume):
    """Motor perdendo giro e engasgando: liga e desliga cada vez mais devagar."""
    f = 22 + f_ini * np.exp(-r / tau_tom)
    engasgo = 0.5 + 0.5 * np.sign(np.sin(fase(14 * np.exp(-r / 0.7))))
    return filtrar(np.tanh(2.5 * serra(f)) * engasgo, "lowpass", 900) * np.exp(-r / tau_volume)


def efeito_chefe_atordoado():
    """Escavadeira batendo na borda: pancada de lata, peças chacoalhando e o motor engasgando."""
    t = tempo(1.0)
    n = len(t)
    x = sum(g * np.sin(2 * np.pi * 150 * r * t) * np.exp(-t * np.sqrt(r) / 0.3)
            for r, g in [(1, 1), (2.32, 0.8), (3.87, 0.6), (5.61, 0.45), (7.3, 0.3), (9.9, 0.2)])
    x += 0.8 * unitario(filtrar(ruido(n), "bandpass", [800, 6000])) * np.exp(-t / 0.02)
    x += 1.5 * pancada_grave(t, 0.0, 50, 90, 0.12)
    inicio, intervalo, ganho = 0.1, 0.085, 0.5
    while inicio < 0.62:
        encaixar(x, bigorna(ganho, rng.uniform(1500, 2400), 0.02), inicio)
        inicio, intervalo, ganho = inicio + intervalo, intervalo * 0.86, ganho * 0.87
    rel, m = a_partir_de(t, 0.12)
    x[m] += 1.3 * motor_falhando(rel[m], 60, 0.35, 0.4)
    return bordas(x, 0.001, 0.15)


def efeito_chefe_derrotado():
    """A máquina desmontando: metal gemendo, motor morrendo, vapor escapando e o baque final."""
    t = tempo(1.8)
    n = len(t)
    x = 0.9 * motor_falhando(t, 70, 0.5, 0.55)
    for inicio, f_ini, f_fim, duracao in [(0.0, 190, 120, 0.7), (0.35, 260, 150, 0.6), (0.8, 140, 70, 0.7)]:
        r = tempo(duracao)
        f = f_ini * (f_fim / f_ini) ** (r / duracao)
        gemido = tom_harmonico(f, [(1, 1), (2.41, 0.5), (3.83, 0.3), (5.2, 0.15)])
        gemido *= (1 + 0.5 * np.sin(2 * np.pi * 27 * r)) * np.sin(np.pi * r / duracao)
        encaixar(x, gemido, inicio, 0.45)
    rel, m = a_partir_de(t, 0.5)
    vapor = unitario(filtrar(ruido(n), "highpass", 3500, 4))
    x[m] += 0.55 * vapor[m] * np.clip(rel[m] / 0.05, 0, 1) * np.exp(-rel[m] / 0.4)
    baque = 1.38
    rel, m = a_partir_de(t, baque)
    x += 1.6 * pancada_grave(t, baque, 45, 80, 0.16)
    x[m] += 0.8 * unitario(filtrar(ruido(n), "lowpass", 500))[m] * np.exp(-rel[m] / 0.05)
    encaixar(x, bigorna(0.5, 310.0, 0.09), baque)
    return bordas(x, 0.01, 0.15)


def efeito_vitoria():
    """Tema da Samaúma em Ré maior (lá, ré, mi, fá#, lá, fá#) e o acorde final, já no tom da música de vitória."""
    t = tempo(2.3)
    x = np.zeros(len(t))
    for nome, inicio, dur in [("A4", 0.0, 0.12), ("D5", 0.12, 0.12), ("E5", 0.24, 0.12),
                              ("F#5", 0.36, 0.24), ("A5", 0.62, 0.12), ("F#5", 0.74, 0.14)]:
        x += metal(t, hz(nome), inicio, dur)
    for nome in ["D5", "F#5", "A5", "D6"]:
        x += metal(t, hz(nome), 0.9, 1.35, 0.7)
    x += 2.5 * (pancada_grave(t, 0.0) + pancada_grave(t, 0.9))
    return bordas(filtrar(x, "lowpass", 4500), 0.003, 0.2)


def efeito_recorde():
    """Fanfarra de recorde em Fá maior: três notas repetidas, salto e acorde com brilhos."""
    t = tempo(1.2)
    x = np.zeros(len(t))
    for nome, inicio, dur in [("C5", 0.0, 0.08), ("C5", 0.1, 0.08), ("C5", 0.2, 0.08),
                              ("F5", 0.3, 0.22), ("A5", 0.54, 0.14)]:
        x += metal(t, hz(nome), inicio, dur)
    for nome in ["F5", "A5", "C6"]:
        x += metal(t, hz(nome), 0.7, 0.5, 0.75)
    x += 2.0 * (pancada_grave(t, 0.3) + pancada_grave(t, 0.7))
    x = filtrar(x, "lowpass", 5000)
    for i, nome in enumerate(["F7", "A7", "C8"]):
        x += 0.5 * sino(t, hz(nome), 0.72 + i * 0.1, 0.12)
    return bordas(x, 0.003, 0.15)


def efeito_derrota():
    """Tema ao contrário, descendo em Ré menor (lá, fá, mi, ré)."""
    t = tempo(2.1)
    x = np.zeros(len(t))
    for nome, inicio, dur in [("A4", 0.0, 0.35), ("F4", 0.4, 0.35), ("E4", 0.8, 0.35), ("D4", 1.2, 0.75)]:
        encaixar(x, flauta(hz(nome), dur, sopro=0.12, vibrato=0.008), inicio)
    rel, m = a_partir_de(t, 1.2)
    x[m] += 0.4 * np.sin(2 * np.pi * hz("D3") * rel[m]) * np.clip(rel[m] / 0.1, 0, 1)
    return bordas(x, 0.003, 0.25)


def efeito_clique():
    t = tempo(0.07)
    x = np.sin(2 * np.pi * 1500 * t) + 0.3 * np.sin(2 * np.pi * 3000 * t)
    return x * np.exp(-t / 0.012)


def efeito_botao_foco():
    t = tempo(0.04)
    return (np.sin(2 * np.pi * 1900 * t) + 0.25 * np.sin(2 * np.pi * 3800 * t)) * np.exp(-t / 0.007)


def efeito_pausa():
    t = tempo(0.32)
    return sino(t, 880.0, 0.0, 0.08) + sino(t, 659.26, 0.1, 0.1)


def efeito_historia_avancar():
    """Virar de carta: toque de madeira e um roçar de folha."""
    t = tempo(0.12)
    tique = np.sin(2 * np.pi * 950 * t) * np.exp(-t / 0.01) + 0.4 * np.sin(2 * np.pi * 2300 * t) * np.exp(-t / 0.005)
    folha = unitario(filtrar(ruido(len(t)), "bandpass", [2500, 8000])) * np.sin(np.pi * t / t[-1]) ** 2
    return tique + 0.3 * folha


def efeito_texto():
    """Blip de máquina de escrever: senoide curtinha e redonda, para repetir muitas vezes por segundo."""
    t = tempo(0.04)
    return (np.sin(2 * np.pi * 740 * t) + 0.2 * np.sin(2 * np.pi * 1480 * t)) * np.sin(np.pi * t / t[-1]) ** 2


EFEITOS = {
    "golpe": efeito_golpe,
    "golpe_acerto": efeito_golpe_acerto,
    "dash": efeito_dash,
    "dano_heroi": efeito_dano_heroi,
    "vida_baixa": efeito_vida_baixa,
    "dano_arvore": efeito_dano_arvore,
    "arvore_critica": efeito_arvore_critica,
    "arvore_curada": efeito_arvore_curada,
    "inimigo_derrotado": efeito_inimigo_derrotado,
    "item_caiu": efeito_item_caiu,
    "item_fruta": efeito_item_fruta,
    "item_erva": efeito_item_erva,
    "escudo": efeito_escudo,
    "power_velocidade": efeito_power_velocidade,
    "power_forca": efeito_power_forca,
    "onda_iniciada": efeito_onda_iniciada,
    "onda_concluida": efeito_onda_concluida,
    "fogo_nasce": efeito_fogo_nasce,
    "fogo_apagado": efeito_fogo_apagado,
    "motosserra": efeito_motosserra,
    "escavadeira_investida": efeito_escavadeira_investida,
    "chefe_aviso": efeito_chefe_aviso,
    "chefe_atordoado": efeito_chefe_atordoado,
    "chefe_derrotado": efeito_chefe_derrotado,
    "vitoria": efeito_vitoria,
    "recorde": efeito_recorde,
    "derrota": efeito_derrota,
    "clique": efeito_clique,
    "botao_foco": efeito_botao_foco,
    "pausa": efeito_pausa,
    "historia_avancar": efeito_historia_avancar,
    "texto": efeito_texto,
}


# ---------------------------------------------------------------- música: notas, acordes e tema

MAIOR = [0, 2, 4, 5, 7, 9, 11]
MENOR = [0, 2, 3, 5, 7, 8, 10]

# Tema da Samaúma em graus da escala (0 = tônica): a chamada "sol, dó, ré, miii | sol, mi, rééé"
# e a resposta, que começa igual e volta para a tônica.
GRAUS_CHAMADA = [-3, 0, 1, 2, 4, 2, 1]
GRAUS_RESPOSTA = [-3, 0, 1, 2, 1, 0, -2, 0]
RITMO_CHAMADA = [1, 1, .5, 1.5, 1, 1, 2]
RITMO_RESPOSTA = [1, 1, .5, 1.5, 1, .5, .5, 2]
# no combate o tema entra sincopado, na célula 3+3+2 do carimbó
RITMO_CHAMADA_TENSA = [.75, .75, .5, 2, .75, .75, 2.5]
RITMO_RESPOSTA_TENSA = [.75, .75, .5, 2, .75, .75, .5, 2]

# símbolo -> nota do baixo e as três vozes do acompanhamento
ACORDES = {
    "F": "F2 A3 C4 F4", "F/A": "A2 A3 C4 F4", "Dm": "D2 A3 D4 F4", "C": "C3 G3 C4 E4",
    "Bb": "Bb2 Bb3 D4 F4", "Gm": "G2 Bb3 D4 G4", "A": "A2 A3 C#4 E4", "Eb": "Eb2 Bb3 Eb4 G4",
    "D": "D3 A3 D4 F#4", "Bm": "B2 B3 D4 F#4", "D/F#": "F#2 A3 D4 F#4", "G": "G2 B3 D4 G4",
    "Em": "E2 B3 E4 G4",
}


def acorde(simbolo):
    notas = [hz(nome) for nome in ACORDES[simbolo].split()]
    return notas[0], notas[1:]


def registro(freq, minimo):
    """Leva a nota para a oitava que começa em `minimo` Hz."""
    return minimo * 2 ** (np.log2(freq / minimo) % 1)


def tema(graus, ritmo, tonica, escala):
    return [(nota(hz(tonica), escala, grau), tempos) for grau, tempos in zip(graus, ritmo)]


def frase(texto, tempos=None):
    """'C5/1 -/.5 F#5/1.5' -> [(Hz ou None para pausa, tempos)]. Confere a soma se `tempos` for dado."""
    notas = []
    for item in texto.split():
        nome, duracao = item.split("/")
        notas.append((None if nome == "-" else hz(nome), float(duracao)))
    total = sum(d for _, d in notas)
    assert tempos is None or abs(total - tempos) < 1e-9, f"frase com {total} tempos: {texto}"
    return notas


def transpor(notas, fator):
    return [(None if freq is None else freq * fator, tempos) for freq, tempos in notas]


def progressao(texto):
    """'F | Dm C | Bb' -> [(símbolo, batida inicial, tempos)], dividindo cada compasso entre os seus acordes."""
    acordes = []
    for compasso, simbolos in enumerate(texto.split("|")):
        simbolos = simbolos.split()
        tempos = 4 / len(simbolos)
        acordes += [(s, compasso * 4 + i * tempos, tempos) for i, s in enumerate(simbolos)]
    return acordes


def trecho(acordes, de, ate):
    """Só os acordes que começam nos compassos [de, ate)."""
    return [a for a in acordes if de * 4 <= a[1] < ate * 4]


def repetir(acordes, celula, tamanho):
    """Espalha uma célula rítmica [(tempo, ...)] de `tamanho` tempos por dentro de cada acorde."""
    for simbolo, batida, tempos in acordes:
        for volta in range(max(1, int(round(tempos / tamanho)))):
            for evento in celula:
                if volta * tamanho + evento[0] < tempos:
                    yield simbolo, batida + volta * tamanho + evento[0], evento[1:]


# ---------------------------------------------------------------- música: faixa e arranjo

class Faixa:
    """Buffer circular de N compassos 4/4. Cada instrumento tem a sua trilha (stem)."""

    def __init__(self, bpm, compassos):
        self.batida = 60 / bpm
        self.compassos = compassos
        self.n = amostras(compassos * 4 * self.batida)
        self.trilhas = {}

    def colocar(self, trilha, som, batida, ganho=1.0):
        buffer = self.trilhas.setdefault(trilha, np.zeros(self.n))
        indices = (amostras(batida * self.batida) + np.arange(len(som))) % self.n
        buffer[indices] += ganho * som

    def trilha(self, nome):
        return self.trilhas.get(nome, np.zeros(self.n))


def tocar(faixa, trilha, instrumento, notas, compasso, ganho=1.0, ligado=0.92):
    """Toca uma melodia [(Hz ou None, tempos)] a partir de `compasso`; instrumento(freq, segundos) -> som."""
    batida = compasso * 4.0
    for freq, tempos in notas:
        if freq is not None:
            faixa.colocar(trilha, instrumento(freq, tempos * faixa.batida * ligado), batida, ganho)
        batida += tempos


def tocar_coro(faixa, acordes, ganho=1.0):
    """Acordes sustentados; quando as mesmas vozes se repetem em sequência, viram uma nota só."""
    blocos = []
    for simbolo, batida, tempos in acordes:
        vozes = acorde(simbolo)[1]
        if blocos and blocos[-1][0] == vozes and abs(blocos[-1][1] + blocos[-1][2] - batida) < 1e-9:
            blocos[-1][2] += tempos
        else:
            blocos.append([vozes, batida, tempos])
    for vozes, batida, tempos in blocos:
        for freq in vozes:
            faixa.colocar("coro", coro(freq, tempos * faixa.batida), batida, ganho)


def tocar_riff(faixa, trilha, instrumento, acordes, celula, tamanho, oitava=1.0, ganho=1.0):
    """celula: [(tempo, voz, força)]; vozes 0 a 2 são as do acorde e 3 é a primeira uma oitava acima."""
    for simbolo, batida, (voz, forca) in repetir(acordes, celula, tamanho):
        vozes = acorde(simbolo)[1]
        freq = oitava * (vozes + [2 * vozes[0]])[voz]
        faixa.colocar(trilha, instrumento(freq, 0.5 * faixa.batida), batida, ganho * forca)


def tocar_baixo(faixa, acordes, celula, tamanho, minimo=70.0):
    """celula: [(tempo, voz, duração)]; voz 0 = nota do baixo, 1 = quinta, 2 = oitava acima.

    Acorde com baixo trocado (ex.: F/A) fica só na nota do baixo.
    """
    for simbolo, batida, (voz, duracao) in repetir(acordes, celula, tamanho):
        raiz = registro(acorde(simbolo)[0], minimo)
        freq = [raiz, registro(raiz * 1.5, minimo), 2 * raiz][0 if "/" in simbolo else voz]
        faixa.colocar("baixo", baixo(freq, duracao * faixa.batida * 0.9), batida)


def tocar_ritmo(faixa, padrao, inicio_compasso=0, fim_compasso=None):
    """padrao(compasso): dict trilha -> lista de (passo de 1/16, função que gera o som)."""
    fim = faixa.compassos if fim_compasso is None else fim_compasso
    for compasso in range(inicio_compasso, fim):
        for trilha, eventos in padrao(compasso).items():
            for passo, gerar in eventos:
                faixa.colocar(trilha, gerar(), compasso * 4 + passo / 4, rng.uniform(0.88, 1.0))


def virada(compasso, forca):
    """No fim de cada frase de 4 compassos, os curimbós agudos descem em semicolcheias."""
    if compasso % 4 != 3:
        return []
    return [(p, lambda f=f: curimbo(forca * 0.8, f, aberto=False)) for p, f in [(12, 262), (13, 233), (15, 175)]]


def padrao_carimbo(compasso, forca=1.0):
    """Célula do carimbó (colcheia pontuada, semicolcheia, duas colcheias): curimbó grave, tapas e maracas."""
    return {
        "curimbo": [(p, lambda f=f: curimbo(forca * f)) for p, f in [(0, 1.0), (4, 0.7), (8, 0.9), (12, 0.7)]],
        "tapa": [(p, lambda: curimbo(forca * 0.7, 220.0, aberto=False)) for p in (3, 6, 11, 14)]
        + virada(compasso, forca),
        "maraca": [(p, lambda f=(0.6 if p % 8 in (0, 3, 6) else 0.3): chocalho(forca * f)) for p in range(16)],
    }


def padrao_carimbo_solto(compasso, forca=1.0):
    """Variação para a parte B: o grave faz o 3+3+2 inteiro, o tapa marca o contratempo e entra a bigorninha."""
    return {
        "curimbo": [(p, lambda f=f: curimbo(forca * f)) for p, f in [(0, 1.0), (3, 0.6), (6, 0.8), (8, 0.9), (11, 0.6), (14, 0.8)]],
        "tapa": [(p, lambda: curimbo(forca * 0.75, 220.0, aberto=False)) for p in (4, 12)] + virada(compasso, forca),
        "maraca": [(p, lambda f=(0.6 if p % 4 == 2 else 0.3): chocalho(forca * f)) for p in range(16)],
        "metal": [(p, lambda: bigorna(forca * 0.5, 1760.0, 0.03)) for p in (2, 10)],
    }


def bichos(n, passaros, sapos):
    """Grilos em pulsos, cigarra em ondas, pios de pássaro e coaxos de sapo, colocados em volta do loop."""
    buffer = np.zeros(n)

    def colocar(som, inicio):
        buffer[(inicio + np.arange(len(som))) % n] += som

    for portadora, intervalo in [(4400, (0.8, 1.6)), (5100, (1.1, 2.0))]:
        pulso_t = tempo(0.018)
        pulso = np.sin(2 * np.pi * portadora * pulso_t) * np.sin(np.pi * pulso_t / pulso_t[-1]) ** 2
        inicio = rng.uniform(0, 0.5)
        while inicio < n / SR:
            for k in range(3):
                colocar(0.5 * pulso, amostras(inicio + k * 0.045))
            inicio += rng.uniform(*intervalo)
    t = tempo(2.6)
    cigarra = np.sin(2 * np.pi * 5800 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 90 * t)) * np.sin(np.pi * t / t[-1]) ** 2
    for inicio in rng.uniform(0, n / SR, 3):
        colocar(0.25 * cigarra, amostras(inicio))
    t = tempo(0.14)
    pio = np.sin(fase(2000 + 1200 * np.sin(np.pi * t / t[-1]))) * np.sin(np.pi * t / t[-1])
    for inicio in rng.uniform(0, n / SR, passaros):
        colocar(0.6 * pio, amostras(inicio))
        colocar(0.45 * pio, amostras(inicio + 0.2))
    t = tempo(0.12)
    for inicio in rng.uniform(0, n / SR, sapos):
        coaxo = tom_harmonico(np.full(len(t), rng.uniform(330, 520)), [(1, 1), (2, 0.5), (3, 0.25)])
        coaxo *= (0.5 + 0.5 * np.sin(2 * np.pi * 45 * t)) ** 2 * np.sin(np.pi * t / t[-1])
        for k in range(rng.integers(2, 4)):
            colocar(0.5 * coaxo, amostras(inicio + k * 0.21))
    return buffer


def vento(n):
    """Ruído grave filtrado no domínio da frequência (periódico) com ondulação lenta de ciclos inteiros."""
    espectro = np.fft.rfft(ruido(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    forma = (f > 40) / (1 + (f / 450) ** 2)
    x = unitario(np.fft.irfft(espectro * forma, n))
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * np.arange(n) / n))


def reverb_circular(x, duracao=1.4, tau=0.45):
    """Convolução circular com uma resposta de ruído decaindo (não cria emenda no loop).

    Só o que está acima de 180 Hz reverbera, para os graves não embolarem.
    """
    t = tempo(duracao)
    resposta = filtrar(ruido(len(t)), "lowpass", 5000) * np.exp(-t / tau)
    resposta /= np.sqrt(np.sum(resposta ** 2))
    resposta_cheia = np.zeros(len(x))
    resposta_cheia[:len(resposta)] = resposta
    sem_graves = np.fft.rfftfreq(len(x), 1 / SR) > 180
    return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(resposta_cheia) * sem_graves, len(x))


def mixar(faixa, ganhos, envios, ambiente=0.0, passaros=0, sapos=0):
    """ganhos: trilha -> ganho seco; envios: trilha -> quanto vai para o reverb; ambiente: nível da floresta."""
    mix = sum(ganho * faixa.trilha(nome) for nome, ganho in ganhos.items())
    mix = mix + reverb_circular(sum(envio * faixa.trilha(nome) for nome, envio in envios.items()))
    if ambiente > 0:
        mix += ambiente * (0.05 * bichos(faixa.n, passaros, sapos) + 0.12 * vento(faixa.n))
    return mix


# ---------------------------------------------------------------- música: as cinco faixas

ARPEJO = [(0, 0, 1.0), (.5, 1, .7), (1, 2, .85), (1.5, 1, .7)]


def musica_menu():
    """Tema da Samaúma. 80 bpm, Fá maior, 16 compassos (48 s).

    Entrada (calimba anuncia o tema), A (flauta: chamada e resposta), B (ponte em Si bemol),
    A' (flauta dobrada pela calimba, percussão mais presente) e saída que devolve ao começo.
    """
    faixa = Faixa(80, 16)
    acordes = progressao("F | Bb | F | Dm C | F/A | Bb F | Bb | F/A | Gm | C | F | Dm C | F/A | Bb F | Dm | C")
    melodia = tema(GRAUS_CHAMADA, RITMO_CHAMADA, "F5", MAIOR) + tema(GRAUS_RESPOSTA, RITMO_RESPOSTA, "F5", MAIOR)
    ponte = frase("D6/1.5 C6/.5 Bb5/1 F5/1 C6/1.5 A5/.5 F5/2 Bb5/1.5 A5/.5 G5/1 D5/1 E5/1 G5/1 C6/2", 16)
    tocar(faixa, "flauta", lambda f, d: flauta(f, d, sopro=0.1), melodia + ponte + melodia, 2)
    tocar(faixa, "calimba", calimba, transpor(melodia, 0.5), 10, 0.9)
    saida_e_entrada = frase("A4/1 F4/1 D4/1 F4/1 G4/1 E4/1 C4/1 E4/1 C4/1 F4/1 G4/.5 A4/1.5", 12)
    tocar(faixa, "calimba", calimba, saida_e_entrada, 14)
    tocar_riff(faixa, "calimba", calimba, trecho(acordes, 1, 14), ARPEJO, 2, ganho=0.6)
    tocar_coro(faixa, acordes)
    tocar_baixo(faixa, trecho(acordes, 2, 14), [(0, 0, 2), (2, 1, 1), (3, 0, 1)], 4, minimo=80)

    def padrao(compasso):
        eventos = {"curimbo": [(0, lambda: curimbo(0.6, 98.0))],
                   "maraca": [(p, lambda: chocalho(0.25)) for p in (4, 12)]
                   + [(p, lambda: chocalho(0.12)) for p in (2, 6, 10, 14)]}
        if compasso % 2 == 1:
            eventos["curimbo"].append((10, lambda: curimbo(0.35, 98.0)))
        if compasso >= 10:
            eventos["curimbo"] += [(p, lambda: curimbo(0.3, 196.0, aberto=False)) for p in (6, 14)]
        return eventos

    tocar_ritmo(faixa, padrao, 2, 14)
    ganhos = {"flauta": 0.5, "calimba": 0.3, "coro": 0.4, "baixo": 0.3, "curimbo": 0.3, "maraca": 0.2}
    envios = {"flauta": 0.35, "calimba": 0.2, "coro": 0.15, "curimbo": 0.08}
    return mixar(faixa, ganhos, envios, ambiente=1.0, passaros=6, sapos=4)


def musica_calmaria():
    """Respiro entre as ondas. 64 bpm, Fá maior, 8 compassos (30 s).

    A floresta fica na frente. A flauta solta logo no começo as quatro primeiras notas do tema
    (a pausa entre ondas dura só uns 4 s) e, na segunda metade, o fim da resposta; a calimba pontua.
    """
    faixa = Faixa(64, 8)
    acordes = progressao("F | Dm | Bb | C | F | Dm | Bb | C")
    tocar(faixa, "flauta", lambda f, d: flauta(f, d, sopro=0.12), frase("-/.5 C5/.5 F5/.5 G5/.5 A5/2", 4), 0)
    tocar(faixa, "flauta", lambda f, d: flauta(f, d, sopro=0.12), frase("-/.5 G5/.5 F5/.5 D5/.5 F5/2", 4), 4)
    pontos = frase("-/1 A4/1 F4/1 D4/1 -/1 D4/.5 F4/.5 Bb4/2 -/1 E4/1 G4/1 C5/1", 12)
    tocar(faixa, "calimba", calimba, pontos, 1)
    pontos = frase("-/1 F4/1 A4/1 D5/1 -/1 Bb4/.5 F4/.5 D4/2 -/1 G4/1 E4/1 C4/1", 12)
    tocar(faixa, "calimba", calimba, pontos, 5)
    tocar_coro(faixa, acordes)
    tocar_baixo(faixa, acordes, [(0, 0, 3.5)], 4, minimo=80)
    ganhos = {"flauta": 0.4, "calimba": 0.3, "coro": 0.4, "baixo": 0.2}
    envios = {"flauta": 0.4, "calimba": 0.3, "coro": 0.2}
    return mixar(faixa, ganhos, envios, ambiente=2.0, passaros=7, sapos=6)


def musica_combate():
    """Carimbó de batalha. 126 bpm, Ré menor, 24 compassos (45,7 s).

    Entrada (curimbós, maracas e banjo), A (flauta com o tema em menor, sincopado),
    B (vai para Fá maior: marimba puxa o riff, banjo no contratempo, flauta em notas longas)
    e A' (todo mundo junto, flauta dobrada pela marimba).
    """
    faixa = Faixa(126, 24)
    acordes = progressao("Dm | Dm | Dm | Dm | "
                         "Dm | Dm A | Dm | Gm Dm | Dm | Dm A | Dm | Gm A | "
                         "F | C | Gm | A | F | C | Gm | A | "
                         "Dm | Dm A | Dm | Gm A")
    chamada = tema(GRAUS_CHAMADA, RITMO_CHAMADA_TENSA, "D5", MENOR)
    resposta = tema(GRAUS_RESPOSTA, RITMO_RESPOSTA_TENSA, "D5", MENOR)
    sobe = resposta[:4] + frase("G5/.75 F5/.75 G5/.5 A5/2", 4)
    fecha = resposta[:4] + frase("E5/.75 D5/.75 Bb4/.5 A4/2", 4)
    contracanto = frase("A5/3 C6/1 G5/3 E5/1 G5/1 Bb5/1 D6/2 C#6/1.5 A5/.5 E5/2", 16)
    tocar(faixa, "flauta", flauta, chamada + resposta + chamada + sobe, 4, ligado=0.85)
    tocar(faixa, "flauta", flauta, contracanto, 16)
    tocar(faixa, "flauta", flauta, chamada + fecha, 20, ligado=0.85)
    tocar(faixa, "marimba", marimba, chamada + fecha, 20, 0.9)

    dedilhado = [(0, 0, 1.0), (.75, 2, .8), (1, 3, .9), (1.5, 2, .7), (2, 1, 1.0), (2.75, 2, .8), (3, 3, .9), (3.5, 2, .7)]
    contratempo = [(.5, voz, .8) for voz in range(3)]
    riff = [(0, 0, 1.0), (.75, 1, .8), (1.5, 2, .9), (2, 1, .8), (2.5, 3, 1.0), (3, 2, .8), (3.5, 1, .8)]
    tocar_riff(faixa, "banjo", corda, trecho(acordes, 0, 12) + trecho(acordes, 20, 24), dedilhado, 4)
    tocar_riff(faixa, "banjo", corda, trecho(acordes, 12, 20), contratempo, 1, ganho=0.7)
    tocar_riff(faixa, "marimba", marimba, trecho(acordes, 12, 20), riff, 4, oitava=2.0)
    tocar_coro(faixa, trecho(acordes, 12, 24))
    tocar_baixo(faixa, trecho(acordes, 2, 24), [(0, 0, .7), (.75, 1, .25), (1, 0, .45), (1.5, 1, .45)], 2)

    tocar_ritmo(faixa, lambda c: padrao_carimbo(c, 0.85), 0, 4)
    tocar_ritmo(faixa, padrao_carimbo, 4, 12)
    tocar_ritmo(faixa, padrao_carimbo_solto, 12, 20)
    tocar_ritmo(faixa, padrao_carimbo, 20, 24)
    ganhos = {"flauta": 0.5, "marimba": 0.3, "banjo": 0.3, "coro": 0.25, "baixo": 0.35,
              "curimbo": 0.45, "tapa": 0.3, "maraca": 0.2, "metal": 0.15}
    envios = {"flauta": 0.25, "marimba": 0.12, "banjo": 0.08, "coro": 0.1, "curimbo": 0.06, "tapa": 0.08}
    return mixar(faixa, ganhos, envios, ambiente=0.4, passaros=2)


OSTINATO = {  # nota pedal embaixo e uma linha que sobe e desce por cima, com o 2º grau abaixado (Mi bemol)
    "Dm": "D5 A4 Eb5 A4 F5 A4 Eb5 A4",
    "Bb": "D5 Bb4 F5 Bb4 G5 Bb4 F5 Bb4",
    "A": "C#5 A4 E5 A4 G5 A4 E5 A4",
}


def musica_chefe():
    """A máquina. 150 bpm, Ré menor com o 2º grau abaixado, 28 compassos (44,8 s), sem floresta.

    Entrada (motor e bigorna), A (flauta: pedaços do tema, um deles meio tom acima sobre Mi bemol),
    B (oficina: ostinato de marimba, canos batendo, flauta em notas longas) e A' (tema dobrado, tudo ligado).
    """
    faixa = Faixa(150, 28)
    parte_a = "Dm | Dm | Eb | Dm | Dm | Dm | Gm | A"
    acordes = progressao(" | ".join(["Dm | Dm | Dm | Dm", parte_a, "Dm | Dm | Bb | A | Dm | Dm | Bb | A", parte_a]))
    melodia = frase("A4/.5 D5/.5 E5/.5 F5/1.5 -/1 A5/.5 F5/.5 E5/.5 D5/1.5 -/1 "
                    "Bb4/.5 Eb5/.5 F5/.5 G5/1.5 -/1 A5/.5 G5/.5 F5/.5 E5/.5 D5/2 "
                    "A4/.5 D5/.5 E5/.5 F5/1.5 A5/1 F5/.5 E5/.5 F5/.5 A5/1.5 -/1 "
                    "Bb5/1 A5/.5 G5/.5 Bb5/1 D6/1 C#6/1.5 A5/.5 E5/2", 32)
    longas = frase("A5/4 D6/3 C6/1 Bb5/3 D6/1 C#6/4", 16)

    def flauta_tensa(freq, duracao):
        return flauta(freq, duracao, sopro=0.12, vibrato=0.006)

    tocar(faixa, "flauta", flauta_tensa, melodia, 4, ligado=0.85)
    tocar(faixa, "flauta", flauta_tensa, longas, 16)
    tocar(faixa, "flauta", flauta_tensa, melodia, 20, ligado=0.85)
    tocar(faixa, "marimba", marimba, melodia, 20, 0.9)
    for simbolo, batida, _ in trecho(acordes, 12, 20):
        for i, nome in enumerate(OSTINATO[simbolo].split()):
            faixa.colocar("marimba", marimba(hz(nome)), batida + i / 2, 1.0 if i % 2 == 0 else 0.7)
    tocar_coro(faixa, trecho(acordes, 20, 28))
    tocar_baixo(faixa, trecho(acordes, 2, 28),
                [(0, 0, .45), (.75, 0, .45), (1.5, 2, .45), (2, 0, .45), (2.75, 0, .45), (3.5, 2, .45)], 4)
    for simbolo, batida, forca in repetir(acordes, [(i / 2, 1.0 if i % 2 == 0 else 0.7) for i in range(8)], 4):
        faixa.colocar("motor", motor(registro(acorde(simbolo)[0], 70.0), 0.5 * faixa.batida, forca[0]), batida)

    def padrao(compasso):
        oficina = 12 <= compasso < 20
        passos_tique = range(16) if compasso >= 20 else range(0, 16, 2)
        eventos = {"bigorna": [(p, lambda: bigorna(0.8)) for p in (4, 12)],
                   "tique": [(p, lambda f=(0.5 if p % 4 == 2 else 0.3): chocalho(f)) for p in passos_tique],
                   "tapa": virada(compasso, 1.0)}
        if compasso >= 2:
            eventos["bumbo"] = [(p, lambda: bumbo(0.9)) for p in (0, 4, 8, 12)] + [(10, lambda: bumbo(0.6))]
        if oficina:
            eventos["cano"] = [(p, lambda f=f: bigorna(0.7, f, 0.2)) for p, f in
                               [(0, 440.0), (3, 587.33), (6, 440.0), (11, 587.33), (14, 440.0)]]
        if compasso >= 24:
            eventos["bigorna"] += [(p, lambda: bigorna(0.45)) for p in (0, 8)]
        return eventos

    tocar_ritmo(faixa, padrao)
    ganhos = {"flauta": 0.5, "marimba": 0.3, "coro": 0.25, "baixo": 0.3, "motor": 0.3, "bumbo": 0.5,
              "bigorna": 0.2, "cano": 0.15, "tique": 0.2, "tapa": 0.3}
    envios = {"flauta": 0.22, "marimba": 0.1, "bigorna": 0.1, "cano": 0.12, "tapa": 0.08, "bumbo": 0.04}
    return mixar(faixa, ganhos, envios)


def musica_vitoria():
    """Festa mansa depois da batalha. 96 bpm, Ré maior (o Ré menor do combate virou maior), 12 compassos (30 s).

    A (tema na flauta), B (frase nova, mais alegre) e A' (tema com a marimba harmonizando por baixo
    e a resposta subindo até o Ré agudo), sobre um carimbó leve.
    """
    faixa = Faixa(96, 12)
    acordes = progressao("D | Bm A | D/F# | G D | G | D/F# | Em | A | D | Bm A | D/F# | G A D D")
    chamada = tema(GRAUS_CHAMADA, RITMO_CHAMADA, "D5", MAIOR)
    resposta = tema(GRAUS_RESPOSTA, RITMO_RESPOSTA, "D5", MAIOR)
    alegre = frase("D5/.5 G5/.5 B5/1 A5/.5 G5/.5 B5/1 A5/1.5 F#5/.5 D5/1 F#5/1 "
                   "E5/.5 G5/.5 B5/1 A5/.5 G5/.5 E5/1 E5/.5 A5/.5 C#6/1 A5/2", 16)
    sobe = resposta[:4] + frase("E5/1 F#5/.5 A5/.5 D6/2", 4)
    harmonia = frase("F#4/1 A4/1 C#5/.5 D5/1.5 F#5/1 D5/1 C#5/2 "
                     "F#4/1 A4/1 C#5/.5 D5/1.5 B4/1 C#5/.5 E5/.5 F#5/2", 16)
    tocar(faixa, "flauta", flauta, chamada + resposta + alegre + chamada + sobe, 0)
    tocar(faixa, "marimba", marimba, harmonia, 8)
    tocar_riff(faixa, "marimba", marimba, acordes, ARPEJO, 2, ganho=0.6)
    tocar_coro(faixa, acordes)
    tocar_baixo(faixa, acordes, [(0, 0, 1.4), (1.5, 1, .5)], 2, minimo=80)
    tocar_ritmo(faixa, lambda c: padrao_carimbo(c, 0.7 if c < 8 else 0.85))
    ganhos = {"flauta": 0.5, "marimba": 0.3, "coro": 0.4, "baixo": 0.3, "curimbo": 0.3, "tapa": 0.2, "maraca": 0.15}
    envios = {"flauta": 0.3, "marimba": 0.15, "coro": 0.15, "curimbo": 0.06, "tapa": 0.06}
    return mixar(faixa, ganhos, envios, ambiente=0.7, passaros=5)


MUSICAS = {
    "musica_menu": musica_menu,
    "musica_calmaria": musica_calmaria,
    "musica_combate": musica_combate,
    "musica_chefe": musica_chefe,
    "musica_vitoria": musica_vitoria,
}


# ---------------------------------------------------------------- mixagem e gravação

def normalizar_efeito(x):
    return bordas(unitario(x) * db(PICO_EFEITOS_DB), 0.002, 0.01)


def limitar(x, teto_db):
    """Limitador suave: abaixo de 80% do teto não mexe; acima, curva tanh até o teto."""
    teto = db(teto_db)
    joelho = 0.8 * teto
    magnitude = np.abs(x)
    acima = magnitude > joelho
    comprimido = joelho + (teto - joelho) * np.tanh((magnitude[acima] - joelho) / (teto - joelho))
    y = x.copy()
    y[acima] = np.sign(x[acima]) * comprimido
    return y


def normalizar_musica(x):
    x = x - np.mean(x)
    rms = np.sqrt(np.mean(x ** 2))
    return limitar(x * db(RMS_MUSICA_DB) / rms, TETO_MUSICA_DB)


def salvar(x, pasta, nome, qualidade):
    os.makedirs(pasta, exist_ok=True)
    dados = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    if not FFMPEG:
        destino = os.path.join(pasta, nome + ".wav")
        wavfile.write(destino, SR, dados)
        return destino
    destino = os.path.join(pasta, nome + ".ogg")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "audio.wav")
        wavfile.write(wav, SR, dados)
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis",
                        "-q:a", str(qualidade), "-ac", "1", "-ar", str(SR),
                        "-fflags", "+bitexact", "-flags:a", "+bitexact", destino], check=True)
    return destino


def bandas(x):
    """Percentual da energia em graves (< 150 Hz), médios e agudos (> 2 kHz)."""
    energia = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return [100 * energia[faixa].sum() / energia.sum() for faixa in (f < 150, (f >= 150) & (f < 2000), f >= 2000)]


def relatorio(nome, x, destino):
    pico = 20 * np.log10(np.max(np.abs(x)))
    rms = 20 * np.log10(np.sqrt(np.mean(x ** 2)))
    tamanho = os.path.getsize(destino) / 1024
    print(f"  {nome:24s} {len(x) / SR:6.2f} s  pico {pico:6.1f} dBFS  RMS {rms:6.1f} dBFS  {tamanho:7.1f} KB")
    return tamanho


def main():
    print("ffmpeg:", FFMPEG or "não encontrado, salvando .wav")
    total = 0.0
    print("Efeitos:")
    for nome, gerar in EFEITOS.items():
        semear(nome)
        x = normalizar_efeito(gerar())
        total += relatorio(nome, x, salvar(x, PASTA_EFEITOS, nome, QUALIDADE_OGG_EFEITOS))
    print("Músicas:")
    for nome, gerar in MUSICAS.items():
        semear(nome)
        x = normalizar_musica(gerar())
        emenda = abs(x[0] - x[-1])
        graves, medios, agudos = bandas(x)
        total += relatorio(nome, x, salvar(x, PASTA_MUSICA, nome, QUALIDADE_OGG_MUSICA))
        print(f"  {'':24s} salto na emenda do loop: {emenda:.4f}   "
              f"graves/médios/agudos: {graves:.0f}/{medios:.0f}/{agudos:.0f} %")
    print(f"Total: {total / 1024:.2f} MB")


if __name__ == "__main__":
    main()
