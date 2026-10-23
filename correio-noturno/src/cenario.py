"""Cenário da cidade vista de cima, gerado por código e rolando para baixo.

A cidade é montada em "quarteirões" de 240 px de altura (prédios + rua).
A imagem tem altura múltipla disso, então dá para repetir sem emenda.
"""
import math
import random

import pygame

from . import config

QUARTEIRAO = 240          # altura de um quarteirão (prédios + rua)
ALTURA_PREDIOS = 192      # parte do quarteirão ocupada por telhados
ALTURA_CENARIO = QUARTEIRAO * 5

TEMAS = {
    "bairro": {
        "rua": (44, 46, 62), "calcada": (70, 72, 88), "faixa": (150, 140, 110),
        "telhados": [(150, 74, 60), (128, 66, 58), (166, 96, 70), (110, 88, 80),
                     (140, 120, 98)],
        "avenidas": [(300, 338), (624, 662)],
        "arvores": True, "agua": None,
    },
    "centro": {
        "rua": (38, 40, 52), "calcada": (66, 68, 80), "faixa": (200, 190, 120),
        "telhados": [(96, 100, 116), (82, 88, 104), (112, 112, 124), (74, 80, 92),
                     (120, 104, 96)],
        "avenidas": [(250, 296), (560, 606)],
        "arvores": False, "agua": None,
    },
    "porto": {
        "rua": (48, 46, 50), "calcada": (78, 74, 70), "faixa": (190, 170, 90),
        "telhados": [(150, 60, 50), (50, 100, 130), (170, 130, 50), (70, 120, 80),
                     (110, 110, 120)],
        "avenidas": [(330, 370)],
        "arvores": False, "agua": (700, config.LARGURA),
    },
    "torre": {
        "rua": (70, 64, 60), "calcada": (96, 88, 80), "faixa": None,
        "telhados": [(158, 82, 56), (140, 70, 50), (170, 100, 66), (120, 66, 52)],
        "avenidas": [(310, 350), (610, 650)],
        "arvores": True, "agua": None,
    },
}


def _escurecer(cor, f):
    return tuple(max(0, int(c * f)) for c in cor)


class Cenario:
    def __init__(self, tema, semente=1):
        self.tema_nome = tema
        self.tema = TEMAS[tema]
        self.deslocamento = 0.0
        self.luzes = []                 # (x, y_local, raio, cor)
        self.colunas = []               # faixas de x com telhados
        self._brilhos = {}
        self.rnd = random.Random(semente)
        self.imagem = self._gerar()

    # ------------------------------------------------------------- geração
    def _gerar(self):
        t = self.tema
        L, H = config.LARGURA, ALTURA_CENARIO
        img = pygame.Surface((L, H))
        img.fill(t["rua"])

        # colunas de prédios entre as avenidas (e antes da água no porto)
        limite = t["agua"][0] if t["agua"] else L
        x = 0
        for a0, a1 in t["avenidas"]:
            self.colunas.append((x + 6, a0 - 6))
            x = a1
        self.colunas.append((x + 6, limite - 6))

        for q in range(ALTURA_CENARIO // QUARTEIRAO):
            y0 = q * QUARTEIRAO
            self._rua(img, y0 + ALTURA_PREDIOS, limite)
            for c0, c1 in self.colunas:
                self._quarteirao(img, pygame.Rect(c0, y0 + 4, c1 - c0, ALTURA_PREDIOS - 8))
        for a0, a1 in t["avenidas"]:
            self._avenida(img, a0, a1)
        if t["agua"]:
            self._agua(img, *t["agua"])
        return img

    def _rua(self, img, y, limite):
        t = self.tema
        pygame.draw.rect(img, t["calcada"], (0, y, limite, 6))
        pygame.draw.rect(img, t["calcada"], (0, y + QUARTEIRAO - ALTURA_PREDIOS - 6, limite, 6))
        meio = y + (QUARTEIRAO - ALTURA_PREDIOS) // 2
        if t["faixa"]:
            for x in range(0, limite, 40):
                pygame.draw.rect(img, t["faixa"], (x, meio - 1, 20, 3))
        else:  # paralelepípedos
            for x in range(0, limite, 12):
                for yy in range(y + 8, y + QUARTEIRAO - ALTURA_PREDIOS - 8, 8):
                    pygame.draw.rect(img, _escurecer(t["rua"], 0.85), (x + (yy // 8 % 2) * 6, yy, 10, 6), 1)
        # postes de luz na calçada
        for x in range(60, limite, 180):
            px = x + self.rnd.randint(-20, 20)
            pygame.draw.circle(img, (30, 30, 40), (px, y + 3), 4)
            pygame.draw.circle(img, (255, 230, 160), (px, y + 3), 2)
            self.luzes.append((px, y + 3, 46, (255, 190, 90)))

    def _avenida(self, img, a0, a1):
        t = self.tema
        pygame.draw.rect(img, t["rua"], (a0, 0, a1 - a0, ALTURA_CENARIO))
        pygame.draw.rect(img, t["calcada"], (a0, 0, 5, ALTURA_CENARIO))
        pygame.draw.rect(img, t["calcada"], (a1 - 5, 0, 5, ALTURA_CENARIO))
        meio = (a0 + a1) // 2
        if t["faixa"]:
            for y in range(0, ALTURA_CENARIO, 40):
                pygame.draw.rect(img, t["faixa"], (meio - 1, y, 3, 20))
        # faixas de pedestre nos cruzamentos
        for q in range(ALTURA_CENARIO // QUARTEIRAO):
            yc = q * QUARTEIRAO + ALTURA_PREDIOS + 8
            for i in range(a0 + 6, a1 - 6, 8):
                pygame.draw.rect(img, (190, 190, 200), (i, yc - 14, 4, 10))

    def _quarteirao(self, img, area):
        """Divide a área em prédios de larguras variadas e desenha os telhados."""
        x = area.left
        while x < area.right - 30:
            largura = self.rnd.randint(70, 150)
            if area.right - (x + largura) < 50:
                largura = area.right - x
            y = area.top
            while y < area.bottom - 30:
                altura = self.rnd.randint(70, 110)
                if area.bottom - (y + altura) < 45:
                    altura = area.bottom - y
                self._telhado(img, pygame.Rect(x, y, largura - 5, altura - 5))
                y += altura
            x += largura

    def _telhado(self, img, r):
        t, rnd = self.tema, self.rnd
        cor = rnd.choice(t["telhados"])
        # sombra do prédio (dá sensação de altura)
        pygame.draw.rect(img, (16, 16, 24), r.move(4, 4))
        nome = self.tema_nome
        if nome in ("bairro", "torre"):
            # telhado de telhas, com cumeeira no meio
            pygame.draw.rect(img, cor, r)
            pygame.draw.polygon(img, _escurecer(cor, 0.8),
                                [r.topright, r.bottomright, (r.centerx, r.bottom - r.h // 3),
                                 (r.centerx, r.top + r.h // 3)])
            for yy in range(r.top + 4, r.bottom, 7):
                pygame.draw.line(img, _escurecer(cor, 0.7), (r.left + 2, yy), (r.right - 2, yy))
            pygame.draw.line(img, _escurecer(cor, 1.2) if max(cor) < 200 else cor,
                             (r.centerx, r.top + r.h // 3), (r.centerx, r.bottom - r.h // 3), 3)
            if rnd.random() < 0.5:  # chaminé
                cx, cy = rnd.randint(r.left + 8, r.right - 18), rnd.randint(r.top + 6, r.bottom - 18)
                pygame.draw.rect(img, (90, 70, 64), (cx, cy, 10, 10))
                pygame.draw.rect(img, (30, 26, 26), (cx + 2, cy + 2, 6, 6))
        else:
            # laje plana com caixas d'água, ar-condicionado e respiros
            pygame.draw.rect(img, cor, r)
            pygame.draw.rect(img, _escurecer(cor, 0.75), r, 3)
            for _ in range(rnd.randint(1, 3)):
                tipo = rnd.random()
                cx = rnd.randint(r.left + 10, max(r.left + 11, r.right - 22))
                cy = rnd.randint(r.top + 10, max(r.top + 11, r.bottom - 22))
                if tipo < 0.35:
                    pygame.draw.circle(img, (70, 110, 140), (cx + 6, cy + 6), 8)
                    pygame.draw.circle(img, (50, 80, 110), (cx + 6, cy + 6), 8, 2)
                elif tipo < 0.7:
                    pygame.draw.rect(img, (150, 154, 162), (cx, cy, 16, 11))
                    pygame.draw.circle(img, (90, 94, 102), (cx + 8, cy + 5), 4)
                else:
                    pygame.draw.rect(img, (40, 60, 90), (cx, cy, 20, 12))
                    pygame.draw.line(img, (80, 110, 150), (cx, cy + 6), (cx + 20, cy + 6))
        if t["arvores"] and rnd.random() < 0.3:
            ax = rnd.choice((r.left - 2, r.right + 2))
            ay = rnd.randint(r.top, r.bottom)
            pygame.draw.circle(img, (34, 70, 46), (ax, ay), 11)
            pygame.draw.circle(img, (48, 92, 58), (ax - 3, ay - 3), 7)

    def _agua(self, img, x0, x1):
        pygame.draw.rect(img, (24, 52, 86), (x0, 0, x1 - x0, ALTURA_CENARIO))
        pygame.draw.rect(img, (90, 80, 70), (x0 - 6, 0, 8, ALTURA_CENARIO))  # cais
        for y in range(0, ALTURA_CENARIO, 18):
            for x in range(x0 + 10, x1, 46):
                xx = x + (y // 18 % 2) * 20
                pygame.draw.line(img, (44, 82, 120), (xx, y), (xx + 14, y), 2)
        # píeres de madeira com barcos
        for q in range(ALTURA_CENARIO // QUARTEIRAO):
            y = q * QUARTEIRAO + 70
            pygame.draw.rect(img, (110, 82, 56), (x0, y, 150, 18))
            for xx in range(x0, x0 + 150, 10):
                pygame.draw.line(img, (80, 60, 40), (xx, y), (xx, y + 18))
            bx = x0 + 60 + self.rnd.randint(0, 40)
            pygame.draw.ellipse(img, (16, 16, 24), (bx + 3, y + 25, 70, 30))
            pygame.draw.ellipse(img, (180, 60, 50), (bx, y + 22, 70, 30))
            pygame.draw.ellipse(img, (230, 220, 200), (bx + 20, y + 29, 26, 16))
            self.luzes.append((bx + 33, y + 37, 34, (255, 220, 150)))

    # ------------------------------------------------------------- uso
    def atualizar(self, dt, velocidade):
        self.deslocamento = (self.deslocamento + velocidade * dt) % ALTURA_CENARIO

    def _base(self):
        return int(self.deslocamento)

    def desenhar(self, tela):
        base = self._base()
        tela.blit(self.imagem, (0, base - ALTURA_CENARIO))
        tela.blit(self.imagem, (0, base))

    def desenhar_luzes(self, tela, intensidade):
        """Brilho dos postes (soma de cor), mais forte quanto mais escuro."""
        if intensidade <= 0.02:
            return
        base = self._base()
        for x, yl, raio, cor in self.luzes:
            for y in (yl + base, yl + base - ALTURA_CENARIO):
                if -raio < y < config.ALTURA + raio:
                    tela.blit(self._brilho(raio, cor, intensidade), (x - raio, y - raio),
                              special_flags=pygame.BLEND_ADD)

    def _brilho(self, raio, cor, intensidade):
        chave = (raio, cor, round(intensidade, 1))
        if chave not in self._brilhos:
            s = pygame.Surface((raio * 2, raio * 2))
            for r in range(raio, 0, -2):
                f = (1 - r / raio) ** 2 * 0.55 * chave[2]
                pygame.draw.circle(s, tuple(int(c * f) for c in cor), (raio, raio), r)
            self._brilhos[chave] = s
        return self._brilhos[chave]

    # -------------------------------------------- ajuda para posicionar coisas
    def _local(self, y):
        return (y - self._base()) % ALTURA_CENARIO

    def y_em_telhado(self, y_desejado, margem=24):
        """Ajusta y (acima da tela) para cair sobre uma fileira de prédios."""
        y = y_desejado
        for _ in range(QUARTEIRAO):
            resto = self._local(y) % QUARTEIRAO
            if margem <= resto <= ALTURA_PREDIOS - margem:
                return y
            y -= 4
        return y_desejado

    def y_de_rua(self, y_desejado):
        """Devolve o y (na tela, <= y_desejado) do meio da rua mais próxima acima."""
        meio = ALTURA_PREDIOS + (QUARTEIRAO - ALTURA_PREDIOS) // 2
        resto = (self._local(y_desejado) - meio) % QUARTEIRAO
        return y_desejado - resto

    def x_em_telhado(self, rnd, margem=26):
        c0, c1 = rnd.choice(self.colunas)
        return rnd.randint(c0 + margem, max(c0 + margem + 1, c1 - margem))


class Ceu:
    """Escurece a tela de acordo com a hora e vai clareando até o amanhecer."""

    def __init__(self):
        self.veu = pygame.Surface((config.LARGURA, config.ALTURA), pygame.SRCALPHA)
        # faixa laranja do nascer do sol (desenhada uma vez só)
        self.gradiente = pygame.Surface((config.LARGURA, 180), pygame.SRCALPHA)
        for y in range(0, 180, 4):
            a = int(80 * (1 - y / 180))
            pygame.draw.rect(self.gradiente, (255, 170, 80, a), (0, y, config.LARGURA, 4))

    @staticmethod
    def escuridao(progresso):
        """0 = meia-noite, 1 = 6h. Devolve de 0 a 1 o quanto está escuro."""
        return max(0.0, 1 - progresso ** 1.6)

    def desenhar(self, tela, progresso):
        esc = self.escuridao(progresso)
        alpha = int(40 + 140 * esc)
        # azul-noite que vai virando laranja perto das 6h
        quente = max(0.0, (progresso - 0.62) / 0.38)
        cor = (int(12 + 120 * quente), int(14 + 50 * quente), int(48 - 20 * quente))
        self.veu.fill((*cor, alpha))
        tela.blit(self.veu, (0, 0))
        if quente > 0:  # brilho do sol nascendo no topo da tela
            self.gradiente.set_alpha(int(255 * quente))
            tela.blit(self.gradiente, (0, 0))

def oscilar(t, velocidade=1.0, amplitude=1.0):
    return math.sin(t * velocidade) * amplitude
