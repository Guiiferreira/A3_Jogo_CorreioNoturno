"""
Gera todos os efeitos sonoros e músicas do jogo por síntese (só biblioteca
padrão do Python) e salva em assets/sons/ como WAV.

Nada aqui foi baixado da internet: cada som é montado com ondas simples
(seno, quadrada, triângulo, ruído) e envelopes de volume.

    python tools/gerar_sons.py
"""
import array
import math
import os
import random
import wave

TAXA = 22050  # amostras por segundo
PASTA = os.path.join(os.path.dirname(__file__), "..", "assets", "sons")
random.seed(7)


# ------------------------------------------------------------ utilidades
def buffer(segundos):
    return array.array("f", [0.0]) * int(segundos * TAXA)


def salvar(buf, nome, volume=0.9):
    pico = max(1e-6, max(abs(v) for v in buf))
    ganho = volume / pico
    dados = array.array("h", (int(max(-1, min(1, v * ganho)) * 32000) for v in buf))
    caminho = os.path.join(PASTA, nome)
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(dados.tobytes())
    print(f"   {nome:22s} {len(buf) / TAXA:5.1f}s")


def freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def onda(tipo, fase):
    """fase em ciclos (0..1 repete)."""
    f = fase % 1.0
    if tipo == "seno":
        return math.sin(2 * math.pi * f)
    if tipo == "quadrada":
        return 1.0 if f < 0.5 else -1.0
    if tipo == "pulso":
        return 1.0 if f < 0.25 else -1.0
    if tipo == "triangulo":
        return 4 * abs(f - 0.5) - 1
    if tipo == "serra":
        return 2 * f - 1
    return random.uniform(-1, 1)


def tom(buf, inicio, dur, f0, f1=None, tipo="seno", vol=0.5, ataque=0.005,
        decai=None, vibrato=0.0):
    """Escreve um tom no buffer com glissando f0->f1 e envelope."""
    f1 = f1 or f0
    n = int(dur * TAXA)
    i0 = int(inicio * TAXA)
    fase = 0.0
    for i in range(n):
        if i0 + i >= len(buf):
            break
        t = i / TAXA
        p = i / n
        f = f0 + (f1 - f0) * p
        if vibrato:
            f *= 1 + vibrato * math.sin(2 * math.pi * 5.5 * t)
        fase += f / TAXA
        env = min(1.0, t / ataque) if ataque > 0 else 1.0
        if decai:
            env *= math.exp(-t / decai)
        else:
            env *= min(1.0, (n - i) / (0.02 * TAXA))
        buf[i0 + i] += onda(tipo, fase) * env * vol


def ruido(buf, inicio, dur, vol=0.5, corte=0.3, decai=None, corte_final=None):
    """Ruído com filtro passa-baixa simples (corte entre 0 e 1)."""
    n = int(dur * TAXA)
    i0 = int(inicio * TAXA)
    y = 0.0
    for i in range(n):
        if i0 + i >= len(buf):
            break
        t = i / TAXA
        c = corte if corte_final is None else corte + (corte_final - corte) * i / n
        y += c * (random.uniform(-1, 1) - y)
        env = math.exp(-t / decai) if decai else min(1.0, (n - i) / (0.02 * TAXA))
        buf[i0 + i] += y * env * vol


def eco(buf, atraso=0.23, retorno=0.3):
    d = int(atraso * TAXA)
    for i in range(d, len(buf)):
        buf[i] += buf[i - d] * retorno


# ------------------------------------------------------------ efeitos
def efeitos():
    b = buffer(0.25)
    ruido(b, 0, 0.09, corte=0.15, decai=0.04)
    ruido(b, 0.11, 0.09, corte=0.12, decai=0.04, vol=0.4)
    salvar(b, "asa.wav", 0.6)

    b = buffer(0.2)
    tom(b, 0, 0.07, freq(84), tipo="quadrada", vol=0.3, decai=0.05)
    tom(b, 0.06, 0.12, freq(91), tipo="quadrada", vol=0.3, decai=0.06)
    salvar(b, "coleta.wav", 0.5)

    b = buffer(0.7)
    for f, t in ((freq(88), 0), (freq(93), 0.09)):
        tom(b, t, 0.6, f, vol=0.5, decai=0.18)
        tom(b, t, 0.6, f * 2.01, vol=0.15, decai=0.09)
    salvar(b, "entrega.wav", 0.7)

    b = buffer(0.45)
    tom(b, 0, 0.4, 420, 120, tipo="quadrada", vol=0.4, decai=0.2)
    ruido(b, 0, 0.2, corte=0.4, decai=0.07, vol=0.4)
    salvar(b, "dano.wav", 0.7)

    b = buffer(0.6)
    for _ in range(14):
        ruido(b, random.uniform(0, 0.45), 0.03, corte=0.9, decai=0.01, vol=0.6)
    tom(b, 0, 0.5, 120, tipo="serra", vol=0.2)
    salvar(b, "choque.wav", 0.6)

    # miado: "mi-aaau" com harmônicos
    b = buffer(0.7)
    contorno = [(0.0, 650), (0.12, 900), (0.35, 820), (0.6, 480)]
    n = int(0.6 * TAXA)
    fase = 0.0
    for i in range(n):
        t = i / TAXA
        for (ta, fa), (tb, fb) in zip(contorno, contorno[1:]):
            if ta <= t <= tb:
                f = fa + (fb - fa) * (t - ta) / (tb - ta)
                break
        fase += f / TAXA
        env = min(1, t / 0.04) * min(1, (n - i) / (0.15 * TAXA))
        abre = 0.3 + 0.7 * math.sin(math.pi * min(1, t / 0.5))
        v = (math.sin(2 * math.pi * fase) + abre * 0.5 * math.sin(4 * math.pi * fase)
             + abre * 0.3 * math.sin(6 * math.pi * fase))
        b[i] += v * env * 0.4
    salvar(b, "miado.wav", 0.55)

    # corvo: dois "cráás" ásperos
    b = buffer(0.8)
    for t0 in (0.0, 0.38):
        n = int(0.28 * TAXA)
        fase = 0.0
        for i in range(n):
            t = i / TAXA
            f = 380 - 120 * t / 0.28
            fase += f / TAXA
            am = 0.6 + 0.4 * math.sin(2 * math.pi * 32 * t)
            env = min(1, t / 0.02) * min(1, (n - i) / (0.05 * TAXA))
            v = onda("serra", fase) * 0.6 + random.uniform(-1, 1) * 0.35
            b[int(t0 * TAXA) + i] += v * am * env * 0.5
    salvar(b, "corvo.wav", 0.5)

    b = buffer(0.5)
    for i, m in enumerate((72, 76, 79, 84)):
        tom(b, i * 0.07, 0.25, freq(m), tipo="triangulo", vol=0.4, decai=0.12)
    salvar(b, "powerup.wav", 0.6)

    b = buffer(1.6)
    ruido(b, 0, 1.6, corte=0.02, corte_final=0.12, vol=0.8)
    for i in range(len(b)):  # sobe e desce
        t = i / len(b)
        b[i] *= math.sin(math.pi * t)
    salvar(b, "vento.wav", 0.5)

    b = buffer(0.12)
    tom(b, 0, 0.08, 1800, tipo="seno", vol=0.5, decai=0.015)
    ruido(b, 0, 0.03, corte=0.8, decai=0.008, vol=0.3)
    salvar(b, "tique.wav", 0.4)

    b = buffer(0.08)
    tom(b, 0, 0.06, freq(81), tipo="quadrada", vol=0.3, decai=0.03)
    salvar(b, "menu_mover.wav", 0.35)

    b = buffer(0.2)
    tom(b, 0, 0.08, freq(79), tipo="quadrada", vol=0.3, decai=0.05)
    tom(b, 0.07, 0.12, freq(86), tipo="quadrada", vol=0.3, decai=0.06)
    salvar(b, "menu_ok.wav", 0.4)

    b = buffer(0.5)
    tom(b, 0, 0.35, freq(72), tipo="triangulo", vol=0.4, decai=0.15)
    tom(b, 0.12, 0.35, freq(67), tipo="triangulo", vol=0.4, decai=0.15)
    salvar(b, "pausa.wav", 0.4)

    # sino da fase (dim-dom)
    b = buffer(2.2)
    for f, t in ((freq(76), 0), (freq(72), 0.55)):
        for h, a in ((1, 0.5), (2.76, 0.18), (5.4, 0.08)):
            tom(b, t, 1.6, f * h, vol=a, decai=0.5)
    eco(b, 0.19, 0.25)
    salvar(b, "sino.wav", 0.6)

    # jingle de vitória
    b = buffer(2.0)
    notas = [(72, 0, 0.15), (76, 0.15, 0.15), (79, 0.3, 0.15), (84, 0.45, 0.9)]
    for m, t, d in notas:
        tom(b, t, d + 0.4, freq(m), tipo="quadrada", vol=0.18, decai=0.3)
        tom(b, t, d + 0.4, freq(m), tipo="triangulo", vol=0.35, decai=0.4)
    for m in (60, 64, 67):
        tom(b, 0.45, 1.4, freq(m), tipo="triangulo", vol=0.2, decai=0.7)
    salvar(b, "vitoria.wav", 0.7)

    # jingle de derrota
    b = buffer(2.2)
    for i, m in enumerate((67, 66, 65)):
        tom(b, i * 0.35, 0.4, freq(m), tipo="triangulo", vol=0.4, decai=0.3)
    tom(b, 1.05, 1.1, freq(64), tipo="triangulo", vol=0.4, decai=0.5, vibrato=0.01)
    tom(b, 1.05, 1.1, freq(52), tipo="triangulo", vol=0.3, decai=0.6)
    salvar(b, "derrota.wav", 0.6)

    # galo: có-có-ri-cóóó
    b = buffer(1.8)
    silabas = [(0.0, 0.12, 520, 600), (0.16, 0.12, 600, 680),
               (0.33, 0.16, 760, 980), (0.52, 0.9, 900, 640)]
    for t0, d, fa, fb in silabas:
        n = int(d * TAXA)
        fase = 0.0
        for i in range(n):
            t = i / TAXA
            f = (fa + (fb - fa) * i / n) * (1 + 0.025 * math.sin(2 * math.pi * 9 * t))
            fase += f / TAXA
            env = min(1, t / 0.015) * min(1, (n - i) / (0.04 * TAXA))
            v = (math.sin(2 * math.pi * fase) + 0.6 * math.sin(4 * math.pi * fase)
                 + 0.35 * onda("serra", fase * 3) + random.uniform(-0.15, 0.15))
            b[int(t0 * TAXA) + i] += v * env * 0.35
    salvar(b, "galo.wav", 0.55)


# ------------------------------------------------------------ músicas
def caixinha(buf, t, m, dur, vol=0.35):
    """Timbre de caixinha de música."""
    f = freq(m)
    tom(buf, t, dur + 0.6, f, vol=vol, decai=0.35, ataque=0.002)
    tom(buf, t, dur + 0.6, f * 3.0, vol=vol * 0.12, decai=0.08, ataque=0.002)


def baixo(buf, t, m, dur, vol=0.3, tipo="triangulo"):
    tom(buf, t, dur, freq(m), tipo=tipo, vol=vol, decai=dur * 0.8, ataque=0.004)


def chimbal(buf, t, vol=0.08):
    ruido(buf, t, 0.05, corte=0.95, decai=0.012, vol=vol)


def bumbo(buf, t, vol=0.5):
    tom(buf, t, 0.18, 110, 45, vol=vol, decai=0.07, ataque=0.001)


def tocar_melodia(buf, inicio, batida, melodia, instrumento, **kw):
    t = inicio
    for nota, tempos in melodia:
        if nota is not None:
            instrumento(buf, t, nota, tempos * batida, **kw)
        t += tempos * batida
    return t


ACORDES = {
    "Am": (57, 60, 64), "F": (53, 57, 60), "C": (48, 52, 55), "G": (55, 59, 62),
    "E": (52, 56, 59), "Dm7": (50, 53, 57, 60), "G7": (55, 59, 62, 65),
    "Cmaj7": (48, 52, 55, 59), "Am7": (57, 60, 64, 67), "Em": (52, 55, 59),
    "D": (50, 54, 57), "B": (47, 51, 54), "Cg": (48, 52, 55),
}


def musica_menu():
    """Valsa de caixinha de música em Lá menor (3/4)."""
    bpm = 92
    bt = 60 / bpm
    compassos = ["Am", "Am", "F", "F", "C", "C", "G", "G",
                 "Am", "Am", "F", "F", "C", "C", "E", "E"]
    mel = [
        (76, 1), (72, 1), (69, 1), (71, 1.5), (72, 0.5), (74, 1),
        (72, 1), (69, 1), (65, 1), (69, 2), (67, 1),
        (76, 1), (79, 1), (76, 1), (74, 1.5), (72, 0.5), (74, 1),
        (71, 1), (74, 1), (79, 1), (77, 2), (76, 1),
        (81, 1), (79, 1), (76, 1), (72, 1.5), (74, 0.5), (76, 1),
        (77, 1), (76, 1), (72, 1), (69, 2), (72, 1),
        (67, 1), (72, 1), (76, 1), (74, 1), (72, 1), (71, 1),
        (68, 1), (71, 1), (74, 1), (76, 3),
    ]
    dur = len(compassos) * 3 * bt
    b = buffer(dur)
    tocar_melodia(b, 0, bt, mel, caixinha, vol=0.32)
    for i, ac in enumerate(compassos):
        t = i * 3 * bt
        notas = ACORDES[ac]
        baixo(b, t, notas[0] - 12, 2.5 * bt, vol=0.25)
        caixinha(b, t + bt, notas[1] + 12, bt, vol=0.12)
        caixinha(b, t + 2 * bt, notas[2] + 12, bt, vol=0.12)
    eco(b, bt * 0.75, 0.22)
    salvar(b, "musica_menu.wav", 0.7)


def musica_noite():
    """Noturno tranquilo, 4/4, para as primeiras fases."""
    bpm = 96
    bt = 60 / bpm
    prog = ["Dm7", "G7", "Cmaj7", "Am7"] * 4
    dur = len(prog) * 4 * bt
    b = buffer(dur)
    for i, ac in enumerate(prog):
        t = i * 4 * bt
        notas = ACORDES[ac]
        # baixo andando
        for j, nn in enumerate((notas[0] - 12, notas[2] - 12, notas[0] - 12, notas[1] - 12)):
            baixo(b, t + j * bt, nn, bt * 0.9, vol=0.28)
        # acordes tipo piano elétrico
        for nn in notas:
            tom(b, t, 1.6 * bt, freq(nn + 12), vol=0.07, decai=0.6,
                vibrato=0.003)
            tom(b, t + 2.5 * bt, 1.0 * bt, freq(nn + 12), vol=0.05, decai=0.4)
        for k in range(8):
            chimbal(b, t + k * bt / 2, 0.05 if k % 2 else 0.07)
        bumbo(b, t, 0.35)
        bumbo(b, t + 2 * bt, 0.25)
    # melodia assobiada na segunda metade
    mel = [(None, 16),
           (74, 1.5), (72, 0.5), (69, 2), (71, 1), (74, 1), (79, 2),
           (76, 3), (74, 1), (72, 2), (69, 2),
           (77, 1.5), (76, 0.5), (74, 1), (72, 1), (71, 2), (67, 2),
           (69, 4), (None, 4)]
    tocar_melodia(b, 0, bt, mel, lambda bb, t, m, d, **k: tom(
        bb, t, d * 0.95, freq(m), vol=0.16, ataque=0.04, vibrato=0.006))
    eco(b, bt * 0.75, 0.2)
    salvar(b, "musica_noite.wav", 0.7)


def musica_madrugada():
    """Mais rápida e tensa, para o porto e a torre."""
    bpm = 132
    bt = 60 / bpm
    prog = ["Em", "Em", "C", "C", "D", "D", "B", "B"] * 2
    dur = len(prog) * 4 * bt
    b = buffer(dur)
    padrao = [0, 0, 12, 0, 7, 0, 12, 7, 0, 0, 12, 0, 10, 0, 7, 12]
    for i, ac in enumerate(prog):
        t = i * 4 * bt
        raiz = ACORDES[ac][0] - 12
        for k, intervalo in enumerate(padrao):
            baixo(b, t + k * bt / 4, raiz + intervalo, bt / 4, vol=0.16, tipo="pulso")
        for k in range(4):
            bumbo(b, t + k * bt, 0.45)
            chimbal(b, t + k * bt + bt / 2, 0.08)
        if i % 2 == 0:
            for nn in ACORDES[ac]:
                tom(b, t, 8 * bt, freq(nn), vol=0.05, ataque=0.5)
    mel = [(None, 32),
           (83, 2), (79, 2), (76, 4), (84, 2), (83, 2), (79, 4),
           (81, 2), (78, 2), (74, 4), (78, 3), (75, 1), (71, 4)]
    tocar_melodia(b, 0, bt, mel, lambda bb, t, m, d, **k: tom(
        bb, t, d * 0.9, freq(m), tipo="quadrada", vol=0.06, ataque=0.01,
        vibrato=0.005))
    eco(b, bt * 0.75, 0.18)
    salvar(b, "musica_madrugada.wav", 0.7)


def musica_amanhecer():
    """Tema do final feliz, em Dó maior."""
    bpm = 84
    bt = 60 / bpm
    prog = ["C", "G", "Am", "F", "C", "G", "F", "C"]
    dur = len(prog) * 4 * bt + 1.5
    b = buffer(dur)
    for i, ac in enumerate(prog):
        t = i * 4 * bt
        notas = ACORDES[ac]
        baixo(b, t, notas[0] - 12, 3.8 * bt, vol=0.22)
        for nn in notas:
            tom(b, t, 4 * bt, freq(nn + 12), vol=0.06, ataque=0.3)
        for k in range(4):
            caixinha(b, t + k * bt, notas[k % 3] + 24, bt, vol=0.07)
    mel = [(76, 2), (79, 2), (79, 1), (77, 1), (76, 2),
           (72, 3), (74, 1), (76, 2), (72, 2),
           (81, 2), (79, 2), (77, 1), (76, 1), (74, 2),
           (72, 4), (None, 4)]
    tocar_melodia(b, 0, bt, mel, caixinha, vol=0.3)
    eco(b, bt * 0.75, 0.25)
    salvar(b, "musica_amanhecer.wav", 0.7)


def main():
    os.makedirs(PASTA, exist_ok=True)
    print("Gerando sons em", os.path.abspath(PASTA))
    efeitos()
    musica_menu()
    musica_noite()
    musica_madrugada()
    musica_amanhecer()


if __name__ == "__main__":
    main()
