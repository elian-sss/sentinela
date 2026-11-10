#!/usr/bin/env python3
"""Gera todo o áudio do Sentinela por síntese, sem nenhum sample de terceiros.

Uso:  python tools/gerar_audio.py
Requer numpy e scipy. Usa o ffmpeg (libvorbis) para salvar .ogg; sem ffmpeg, salva .wav.
Saída (mono, 44,1 kHz):
  assets/audio/efeitos/*.ogg   efeitos normalizados em pico de -6 dBFS
  assets/audio/musica/*.ogg    loops perfeitos normalizados em RMS de -14 dBFS (pico <= -1 dBFS)

É reproduzível: a semente é fixa, e o ffmpeg roda em modo bitexact.
Para que as músicas fechem o loop sem estalo, todo som é colocado num buffer circular:
o que passa do fim volta no começo, e o vento e o reverb são filtrados no domínio da frequência.
"""
import os
import shutil
import subprocess
import tempfile

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


def nota(base_hz, escala, grau):
    oitava, i = divmod(grau, len(escala))
    return base_hz * 2 ** ((escala[i] + 12 * oitava) / 12)


PENTA_MAIOR = [0, 2, 4, 7, 9]
PENTA_MENOR = [0, 3, 5, 7, 10]
C3, C4, C5 = 130.81, 261.63, 523.25
A1, A2, A4 = 55.0, 110.0, 440.0

# ruídos já filtrados, fatiados por cada nota (mais rápido que filtrar nota a nota)
SOPRO = unitario(filtrar(ruido(amostras(4)), "bandpass", [1200, 6000]))
AREIA = unitario(filtrar(ruido(amostras(3)), "highpass", 5000, 4))


def fatia(buffer, n):
    inicio = rng.integers(0, len(buffer) - n)
    return buffer[inicio:inicio + n]


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


def efeito_inimigo_derrotado():
    t = tempo(0.5)
    n = len(t)
    puf = unitario(varredura_filtrada(ruido(n), 2600, 220, q=0.8))
    corpo = unitario(filtrar(ruido(n), "lowpass", 700))
    envelope = np.clip(t / 0.012, 0, 1) * np.exp(-t / 0.14)
    return bordas((0.8 * puf + 0.5 * corpo) * envelope, 0.002, 0.05)


def sino(t, freq, inicio, tau):
    rel, m = a_partir_de(t, inicio)
    x = np.zeros(len(t))
    x[m] = (np.sin(2 * np.pi * freq * rel[m])
            + 0.3 * np.sin(2 * np.pi * freq * 2.76 * rel[m]) * np.exp(-rel[m] / 0.05))
    x[m] *= np.clip(rel[m] / 0.003, 0, 1) * np.exp(-rel[m] / tau)
    return x


def efeito_item_fruta():
    t = tempo(0.45)
    return sino(t, 1318.5, 0.0, 0.16) + 0.8 * sino(t, 1975.5, 0.07, 0.2)


def efeito_item_erva():
    t = tempo(0.75)
    x = np.zeros(len(t))
    for i, f in enumerate([C5, 659.26, 783.99, 1046.5]):
        rel, m = a_partir_de(t, i * 0.075)
        x[m] += (tom_harmonico(np.full(m.sum(), f), [(1, 1), (2, 0.1)])
                 * np.clip(rel[m] / 0.015, 0, 1) * np.exp(-rel[m] / 0.22))
    return filtrar(x, "lowpass", 5000)


def efeito_escudo():
    t = tempo(0.75)
    subida = 1 + 0.05 * t / t[-1]
    x = sum(tom_harmonico(f * subida, [(1, 1)]) + tom_harmonico((f + 3) * subida, [(1, 0.7)])
            for f in [C5, 783.99, 1046.5])
    x *= 1 - 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * 12 * t))
    brilho = unitario(varredura_filtrada(ruido(len(t)), 2000, 8000, q=2)) * 0.25
    envelope = np.clip(t / 0.03, 0, 1) * np.exp(-t / 0.35)
    return bordas((unitario(x) + brilho) * envelope, 0.003, 0.08)


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


def efeito_onda_iniciada():
    t = tempo(1.25)
    x = corne(t, 146.83, 0.0, 0.45) + corne(t, 220.0, 0.4, 0.8)
    return filtrar(x, "lowpass", 1800)


def serra(freqs):
    return 2 * ((fase(freqs) / (2 * np.pi)) % 1) - 1


def efeito_motosserra():
    t = tempo(0.8)
    f = 70 + 60 * (1 - np.exp(-t / 0.15)) - 25 * t
    motor = serra(f) + 0.5 * np.sin(fase(f / 2))
    explosoes = unitario(filtrar(ruido(len(t)), "bandpass", [300, 3000])) * (0.5 + 0.5 * serra(f))
    x = np.tanh(3 * (0.7 * motor + 0.5 * explosoes))
    x = filtrar(x, "bandpass", [120, 3500])
    return bordas(x, 0.03, 0.12)


def efeito_escavadeira_investida():
    t = tempo(1.0)
    f = 45 + 35 * (1 - np.exp(-t / 0.3))
    motor = serra(f) + 0.6 * np.sign(np.sin(fase(f * 0.5)))
    ronco = unitario(filtrar(ruido(len(t)), "bandpass", [200, 900]))
    ronco *= 0.5 + 0.5 * np.sin(2 * np.pi * 30 * t)
    x = np.tanh(2.5 * (0.8 * motor + 0.6 * ronco))
    x = filtrar(x, "lowpass", 1500)
    envelope = np.clip(t / 0.15, 0, 1)
    return bordas(x * envelope, 0.01, 0.25)


def metal(t, freq, inicio, duracao, ganho=1.0):
    rel, m = a_partir_de(t, inicio)
    x = np.zeros(len(t))
    r = rel[m]
    envelope = np.clip(r / 0.02, 0, 1) * np.clip((duracao - r) / 0.08, 0, 1)
    x[m] = ganho * tom_harmonico(np.full(len(r), freq), [(k, 1 / k) for k in range(1, 7)]) * envelope
    return x


def efeito_vitoria():
    t = tempo(2.3)
    x = np.zeros(len(t))
    for freq, inicio, dur in [(C5, 0.0, 0.12), (587.33, 0.12, 0.12), (659.26, 0.24, 0.12),
                              (783.99, 0.36, 0.24), (659.26, 0.62, 0.12), (783.99, 0.74, 0.14)]:
        x += metal(t, freq, inicio, dur)
    for freq in [C5, 659.26, 783.99, 1046.5]:
        x += metal(t, freq, 0.9, 1.35, 0.7)
    for inicio in [0.0, 0.9]:
        rel, m = a_partir_de(t, inicio)
        x[m] += 2.5 * np.sin(fase(55 + 70 * np.exp(-rel[m] / 0.03))) * np.exp(-rel[m] / 0.25)
    return bordas(filtrar(x, "lowpass", 4500), 0.003, 0.2)


def flauta(freq, duracao, sopro=0.08, vibrato=0.004):
    """Senoide com vibrato leve que entra depois do ataque, 2º e 3º harmônicos e ruído de sopro."""
    n = amostras(duracao + 0.15)
    t = np.arange(n) / SR
    profundidade = vibrato * np.clip((t - 0.15) / 0.2, 0, 1)
    f = freq * (1 + profundidade * np.sin(2 * np.pi * 5.2 * t))
    tom = tom_harmonico(f, [(1, 1), (2, 0.18), (3, 0.06)])
    envelope = np.clip(t / 0.05, 0, 1) * np.clip((duracao + 0.12 - t) / 0.12, 0, 1) * 0.9
    ataque = 1 + 1.5 * np.exp(-t / 0.04)
    return (tom + sopro * fatia(SOPRO, n) * ataque) * envelope


def efeito_derrota():
    t = tempo(2.1)
    x = np.zeros(len(t))
    for freq, inicio, dur in [(392.0, 0.0, 0.35), (329.63, 0.4, 0.35), (293.66, 0.8, 0.35), (C4, 1.2, 0.75)]:
        som = flauta(freq, dur, sopro=0.12, vibrato=0.008)
        i = amostras(inicio)
        x[i:i + len(som)] += som[:len(x) - i]
    rel, m = a_partir_de(t, 1.2)
    x[m] += 0.4 * np.sin(2 * np.pi * C3 * rel[m]) * np.clip(rel[m] / 0.1, 0, 1)
    return bordas(x, 0.003, 0.25)


def efeito_clique():
    t = tempo(0.07)
    x = np.sin(2 * np.pi * 1500 * t) + 0.3 * np.sin(2 * np.pi * 3000 * t)
    return x * np.exp(-t / 0.012)


def efeito_pausa():
    t = tempo(0.32)
    return sino(t, 880.0, 0.0, 0.08) + sino(t, 659.26, 0.1, 0.1)


EFEITOS = {
    "golpe": efeito_golpe,
    "dash": efeito_dash,
    "dano_heroi": efeito_dano_heroi,
    "dano_arvore": efeito_dano_arvore,
    "inimigo_derrotado": efeito_inimigo_derrotado,
    "item_fruta": efeito_item_fruta,
    "item_erva": efeito_item_erva,
    "escudo": efeito_escudo,
    "onda_iniciada": efeito_onda_iniciada,
    "motosserra": efeito_motosserra,
    "escavadeira_investida": efeito_escavadeira_investida,
    "vitoria": efeito_vitoria,
    "derrota": efeito_derrota,
    "clique": efeito_clique,
    "pausa": efeito_pausa,
}


# ---------------------------------------------------------------- música

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


def tambor_grave(forca):
    t = tempo(0.55)
    corpo = np.sin(fase(55 + 70 * np.exp(-t / 0.03))) * np.exp(-t / 0.28)
    batida = unitario(filtrar(ruido(len(t)), "lowpass", 1500)) * np.exp(-t / 0.006)
    return forca * bordas(corpo + 0.3 * batida, 0.001, 0.02)


def tambor_medio(forca, freq):
    t = tempo(0.3)
    corpo = np.sin(fase(freq + 60 * np.exp(-t / 0.02))) * np.exp(-t / 0.13)
    pele = unitario(filtrar(ruido(len(t)), "bandpass", [800, 3000])) * np.exp(-t / 0.01)
    return forca * bordas(corpo + 0.25 * pele, 0.001, 0.02)


def chocalho(forca):
    n = amostras(0.09)
    t = np.arange(n) / SR
    return forca * fatia(AREIA, n) * np.clip(t / 0.004, 0, 1) * np.exp(-t / 0.035)


def baixo(freq, duracao):
    n = amostras(duracao + 0.08)
    t = np.arange(n) / SR
    tom = tom_harmonico(np.full(n, freq), [(1, 1), (2, 0.25), (3, 0.05)])
    envelope = np.clip(t / 0.01, 0, 1) * (0.6 + 0.4 * np.exp(-t / 0.1)) * np.clip((duracao + 0.06 - t) / 0.06, 0, 1)
    return tom * envelope


def completar(frase, batidas=8):
    """Garante que cada frase tenha exatamente `batidas` tempos (completa com pausa)."""
    total = sum(d for _, d in frase)
    assert total <= batidas + 1e-9, f"frase com {total} tempos: {frase}"
    return frase + ([(None, batidas - total)] if total < batidas else [])


PAUSA = [(None, 8)]


def tocar_melodia(faixa, frases, base, escala, ganho=1.0, sopro=0.08, vibrato=0.004):
    batida = 0.0
    for frase in frases:
        for grau, duracao in completar(frase):
            if grau is not None:
                som = flauta(nota(base, escala, grau), duracao * faixa.batida * 0.92, sopro, vibrato)
                faixa.colocar("flauta", som, batida, ganho)
            batida += duracao


def tocar_ritmo(faixa, padrao, inicio_compasso=0, fim_compasso=None):
    """padrao: dict trilha -> lista de (passo de 1/16, função que gera o som)."""
    fim = faixa.compassos if fim_compasso is None else fim_compasso
    for compasso in range(inicio_compasso, fim):
        for trilha, eventos in padrao(compasso).items():
            for passo, gerar in eventos:
                faixa.colocar(trilha, gerar(), compasso * 4 + passo / 4)


def grilos_e_passaros(n, passaros):
    """Insetos (grilos em pulsos, cigarra em ondas) e pios de pássaro, colocados em volta do loop."""
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
    return buffer


def vento(n):
    """Ruído grave filtrado no domínio da frequência (periódico) com ondulação lenta de ciclos inteiros."""
    espectro = np.fft.rfft(ruido(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    forma = (f > 40) / (1 + (f / 450) ** 2)
    x = unitario(np.fft.irfft(espectro * forma, n))
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * np.arange(n) / n))


def reverb_circular(x, duracao=1.4, tau=0.45):
    """Convolução circular com uma resposta de ruído decaindo (não cria emenda no loop)."""
    t = tempo(duracao)
    resposta = filtrar(ruido(len(t)), "lowpass", 5000) * np.exp(-t / tau)
    resposta /= np.sqrt(np.sum(resposta ** 2))
    resposta_cheia = np.zeros(len(x))
    resposta_cheia[:len(resposta)] = resposta
    return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(resposta_cheia), len(x))


def mixar(faixa, ganhos, nivel_ambiente, passaros):
    flauta_seca = faixa.trilha("flauta")
    mix = ganhos["flauta"] * flauta_seca + ganhos["reverb"] * reverb_circular(flauta_seca)
    for nome in ["baixo", "drone", "grave", "medio", "chocalho"]:
        trilha = faixa.trilha(nome)
        mix += ganhos.get(nome, 0) * trilha
    mix += ganhos.get("reverb_tambores", 0) * reverb_circular(faixa.trilha("grave") + faixa.trilha("medio"))
    ambiente = 0.05 * grilos_e_passaros(faixa.n, passaros) + 0.12 * vento(faixa.n)
    return mix + nivel_ambiente * ambiente


def musica_menu():
    """Calma, 80 bpm, pentatônica maior em Dó, 16 compassos (48 s)."""
    faixa = Faixa(80, 16)
    a = [(2, 1), (3, 1), (4, 2), (3, 1), (2, 1), (1, 2)]
    b = [(0, 1.5), (1, 0.5), (2, 2), (4, 1), (3, 1), (2, 2)]
    c = [(3, 1), (4, 1), (5, 2), (4, 1.5), (3, 0.5), (2, 2)]
    d = [(1, 1), (2, 1), (1, 1), (0, 1), (-1, 2), (0, 2)]
    tocar_melodia(faixa, [PAUSA, a, b, a, d, PAUSA, c, d], C5, PENTA_MAIOR, sopro=0.1)
    raizes = [0, 4, 0, 4, 0, 3, 4, 3, 0, 4, 0, 3, 4, 3, 0, 0]
    for compasso, grau in enumerate(raizes):
        faixa.colocar("baixo", baixo(nota(C3, PENTA_MAIOR, grau), 4 * faixa.batida * 0.95), compasso * 4)

    def padrao(compasso):
        eventos = {"grave": [(0, lambda: tambor_grave(0.6))],
                   "chocalho": [(p, lambda: chocalho(0.25)) for p in (4, 12)]
                   + [(p, lambda: chocalho(0.12)) for p in (2, 6, 10, 14)]}
        if compasso % 2 == 1:
            eventos["grave"].append((10, lambda: tambor_grave(0.3)))
        return eventos

    tocar_ritmo(faixa, padrao)
    ganhos = {"flauta": 0.5, "reverb": 0.35, "baixo": 0.3, "grave": 0.5, "chocalho": 0.25}
    return mixar(faixa, ganhos, nivel_ambiente=1.0, passaros=6)


def musica_combate():
    """Mais rápida e percussiva, 120 bpm, pentatônica menor em Lá, 24 compassos (48 s)."""
    faixa = Faixa(120, 24)
    a = [(0, .5), (2, .5), (3, .5), (2, .5), (0, 1), (None, .5), (4, .5), (3, 1), (2, .5), (0, .5), (1, 1)]
    b = [(3, .5), (4, .5), (5, 1), (4, .5), (3, .5), (2, 1), (0, .5), (2, .5), (3, 1), (2, 2)]
    c = [(5, .5), (4, .5), (3, .5), (2, .5), (3, 1), (0, 1), (2, .5), (3, .5), (4, 1), (0, 2)]
    tocar_melodia(faixa, [PAUSA, a, b, a, c, PAUSA, b, b, a, c, a, c], A4, PENTA_MENOR)
    raizes = [0, 0, 4, 3]
    for compasso in range(faixa.compassos):
        grau = raizes[compasso % 4]
        for passo, oitava in [(0, 0), (3, 0), (6, 5), (8, 0), (11, 0), (14, 5)]:
            som = baixo(nota(A2, PENTA_MENOR, grau + oitava), faixa.batida * 0.45)
            faixa.colocar("baixo", som, compasso * 4 + passo / 4)

    def padrao(compasso):
        eventos = {"grave": [(0, lambda: tambor_grave(1.0)), (6, lambda: tambor_grave(0.6)), (8, lambda: tambor_grave(0.9))],
                   "medio": [(4, lambda: tambor_medio(0.7, 180)), (12, lambda: tambor_medio(0.7, 150))],
                   "chocalho": [(p, (lambda: chocalho(0.6)) if p % 4 == 2 else (lambda: chocalho(0.35))) for p in range(16)]}
        if compasso % 2 == 1:
            eventos["grave"].append((14, lambda: tambor_grave(0.5)))
        if compasso % 4 == 3:
            eventos["medio"] += [(p, lambda f=f: tambor_medio(0.6, f)) for p, f in [(13, 200), (14, 170), (15, 140)]]
        return eventos

    tocar_ritmo(faixa, padrao)
    ganhos = {"flauta": 0.45, "reverb": 0.25, "baixo": 0.32, "grave": 0.6, "medio": 0.4,
              "chocalho": 0.18, "reverb_tambores": 0.12}
    return mixar(faixa, ganhos, nivel_ambiente=0.5, passaros=3)


def musica_chefe():
    """Tensa, 140 bpm, pentatônica menor em Lá com drone grave pulsando, 28 compassos (48 s)."""
    faixa = Faixa(140, 28)
    a = [(0, .5), (0, .5), (2, .5), (0, .5), (3, 1), (2, .5), (0, .5), (4, 1), (3, .5), (2, .5), (0, 2)]
    b = [(5, .5), (4, .5), (5, .5), (4, .5), (3, 1), (2, 1), (3, .5), (2, .5), (0, .5), (-1, .5), (0, 2)]
    c = [(7, .25), (6, .25), (7, .25), (6, .25), (5, 1), (None, .5), (5, .5), (4, .5), (3, .5), (4, 1), (2, 1), (0, 2)]
    tocar_melodia(faixa, [PAUSA, PAUSA, a, b, a, c, PAUSA, a, b, c, a, b, a, c], A4, PENTA_MENOR,
                  sopro=0.12, vibrato=0.006)
    raizes = [0, 0, 1, 0, 0, 0, 4, 3]
    for compasso in range(faixa.compassos):
        grau = raizes[compasso % len(raizes)]
        for passo in range(0, 16, 2):
            oitava = 5 if passo in (6, 14) else 0
            som = baixo(nota(A2, PENTA_MENOR, grau + oitava), faixa.batida * 0.42)
            faixa.colocar("baixo", som, compasso * 4 + passo / 4)
        t = tempo(4 * faixa.batida)
        drone = (np.sin(2 * np.pi * A1 * t) + 0.5 * np.sin(2 * np.pi * A1 * 1.5 * t))
        drone *= np.sin(np.pi * t / t[-1]) * (0.75 + 0.25 * np.sin(2 * np.pi * 7 * t))
        faixa.colocar("drone", drone, compasso * 4)

    def padrao(compasso):
        eventos = {"grave": [(p, lambda: tambor_grave(0.9)) for p in (0, 4, 8, 12)] + [(10, lambda: tambor_grave(0.6))],
                   "medio": [(2, lambda: tambor_medio(0.5, 220)), (6, lambda: tambor_medio(0.5, 220)),
                             (14, lambda: tambor_medio(0.7, 140))],
                   "chocalho": [(p, (lambda: chocalho(0.55)) if p % 2 == 1 else (lambda: chocalho(0.3))) for p in range(16)]}
        if compasso % 4 == 3:
            eventos["medio"] += [(p, lambda f=f: tambor_medio(0.7, f)) for p, f in [(12, 230), (13, 200), (14, 170), (15, 140)]]
        return eventos

    tocar_ritmo(faixa, padrao)
    ganhos = {"flauta": 0.42, "reverb": 0.22, "baixo": 0.35, "drone": 0.25, "grave": 0.65, "medio": 0.45,
              "chocalho": 0.18, "reverb_tambores": 0.12}
    return mixar(faixa, ganhos, nivel_ambiente=0.3, passaros=0)


MUSICAS = {
    "musica_menu": musica_menu,
    "musica_combate": musica_combate,
    "musica_chefe": musica_chefe,
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
        x = normalizar_efeito(gerar())
        total += relatorio(nome, x, salvar(x, PASTA_EFEITOS, nome, QUALIDADE_OGG_EFEITOS))
    print("Músicas:")
    for nome, gerar in MUSICAS.items():
        x = normalizar_musica(gerar())
        emenda = abs(x[0] - x[-1])
        total += relatorio(nome, x, salvar(x, PASTA_MUSICA, nome, QUALIDADE_OGG_MUSICA))
        print(f"  {'':24s} salto na emenda do loop: {emenda:.4f}")
    print(f"Total: {total / 1024:.2f} MB")


if __name__ == "__main__":
    main()
