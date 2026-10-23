"""Efeitos visuais: partículas, textos flutuantes, tremor de tela, vento e névoa."""
import math
import random

import pygame

from . import config
from .recursos import fonte
from .ui import texto


class Particulas:
    """Sistema simples: cada partícula é uma lista [x, y, vx, vy, vida, vida_total, cor, tam]."""

    def __init__(self):
        self.lista = []

    def explodir(self, x, y, cor, qtd=12, velocidade=140, tam=4, vida=0.6, gravidade=0):
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * velocidade
            t = random.uniform(0.6, 1.0) * vida
            self.lista.append([x, y, math.cos(ang) * v, math.sin(ang) * v, t, t, cor, tam, gravidade])

    def penas(self, x, y, qtd=8):
        """Penas caindo quando o pombo leva dano."""
        for _ in range(qtd):
            self.lista.append([x, y, random.uniform(-90, 90), random.uniform(-120, -20),
                               1.2, 1.2, (223, 230, 245), 5, 160])

    def brilho(self, x, y, cor=config.COR_DESTAQUE, qtd=16):
        self.explodir(x, y, cor, qtd=qtd, velocidade=180, tam=3, vida=0.5)

    def atualizar(self, dt, rolagem):
        vivas = []
        for p in self.lista:
            p[0] += p[2] * dt
            p[1] += (p[3] + rolagem) * dt
            p[3] += p[8] * dt
            p[2] *= 0.98
            p[4] -= dt
            if p[4] > 0:
                vivas.append(p)
        self.lista = vivas

    def desenhar(self, tela):
        for x, y, _, _, vida, total, cor, tam, _ in self.lista:
            t = max(1, int(tam * (vida / total) + 1))
            pygame.draw.rect(tela, cor, (int(x) - t // 2, int(y) - t // 2, t, t))


class TextoFlutuante:
    """"+100", "+1 pena" etc. que sobem e somem."""

    def __init__(self):
        self.lista = []

    def adicionar(self, msg, x, y, cor=config.COR_DESTAQUE, tamanho=30):
        self.lista.append({"msg": msg, "x": x, "y": y, "vida": 1.0, "cor": cor, "tam": tamanho})

    def atualizar(self, dt):
        for t in self.lista:
            t["y"] -= 50 * dt
            t["vida"] -= dt
        self.lista = [t for t in self.lista if t["vida"] > 0]

    def desenhar(self, tela):
        for t in self.lista:
            f = fonte(t["tam"], True)
            img = f.render(t["msg"], True, t["cor"])
            sombra = f.render(t["msg"], True, (10, 10, 20))
            alpha = int(255 * min(1, t["vida"] * 2))
            img.set_alpha(alpha)
            sombra.set_alpha(alpha)
            r = img.get_rect(center=(t["x"], t["y"]))
            tela.blit(sombra, r.move(2, 2))
            tela.blit(img, r)


class Tremor:
    """Faz a tela tremer por alguns instantes (colisões)."""

    def __init__(self):
        self.tempo = 0.0
        self.forca = 0.0

    def iniciar(self, forca=8, tempo=0.3):
        self.forca = max(self.forca, forca)
        self.tempo = max(self.tempo, tempo)

    def atualizar(self, dt):
        self.tempo = max(0.0, self.tempo - dt)
        if self.tempo == 0:
            self.forca = 0

    def deslocamento(self):
        if self.tempo <= 0:
            return 0, 0
        f = self.forca * min(1, self.tempo / 0.15)
        return random.randint(-int(f), int(f)), random.randint(-int(f), int(f))


class Vento:
    """Rajadas que empurram o pombo para um lado. Antes de cada rajada aparece um aviso."""

    AVISO = 1.2
    DURACAO = 2.6

    def __init__(self, ativo, forca_mult=1.0):
        self.ativo = ativo
        self.forca_mult = forca_mult
        self.espera = random.uniform(5, 8)
        self.estado = "calmo"      # calmo -> aviso -> soprando
        self.tempo = 0.0
        self.direcao = 1
        self.linhas = []

    def atualizar(self, dt, audio):
        if not self.ativo:
            return
        self.tempo += dt
        if self.estado == "calmo" and self.tempo >= self.espera:
            self.estado, self.tempo = "aviso", 0.0
            self.direcao = random.choice((-1, 1))
        elif self.estado == "aviso" and self.tempo >= self.AVISO:
            self.estado, self.tempo = "soprando", 0.0
            audio.tocar("vento", 0.8)
        elif self.estado == "soprando" and self.tempo >= self.DURACAO:
            self.estado, self.tempo = "calmo", 0.0
            self.espera = random.uniform(5, 9)
        # riscos de vento na tela
        if self.estado == "soprando" and random.random() < 0.6:
            x = -40 if self.direcao > 0 else config.LARGURA + 40
            self.linhas.append([x, random.randint(50, config.ALTURA), random.randint(30, 90)])
        for ln in self.linhas:
            ln[0] += self.direcao * 900 * dt
        self.linhas = [ln for ln in self.linhas if -120 < ln[0] < config.LARGURA + 120]

    def forca(self):
        """Velocidade extra (px/s) aplicada ao pombo."""
        if self.estado != "soprando":
            return 0.0
        intensidade = math.sin(math.pi * self.tempo / self.DURACAO)
        return self.direcao * 190 * intensidade * self.forca_mult

    def desenhar(self, tela, t):
        for x, y, comp in self.linhas:
            pygame.draw.line(tela, (200, 210, 230), (x, y), (x - self.direcao * comp, y), 2)
        if self.estado == "aviso" and int(t * 6) % 2 == 0:
            seta = ">>>" if self.direcao > 0 else "<<<"
            texto(tela, f"{seta}  VENTO  {seta}", 40, (config.LARGURA // 2, 120),
                  config.COR_DESTAQUE)


class Nevoa:
    """Manchas de neblina que passam pela tela e escondem o que está embaixo."""

    def __init__(self, ativa):
        self.ativa = ativa
        self.nuvens = []
        self.img = self._nuvem(170)
        if ativa:
            for _ in range(5):
                self._nova(random.uniform(-200, config.ALTURA))

    @staticmethod
    def _nuvem(raio):
        s = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        for r in range(raio, 0, -6):
            a = int(150 * (1 - r / raio) ** 0.7)
            pygame.draw.circle(s, (190, 196, 210, min(255, a // 3 + 10)), (raio, raio), r)
        return s

    def _nova(self, y=None):
        self.nuvens.append([random.uniform(-150, config.LARGURA - 150),
                            -360 if y is None else y, random.uniform(-20, 20)])

    def atualizar(self, dt, rolagem):
        if not self.ativa:
            return
        for n in self.nuvens:
            n[0] += n[2] * dt
            n[1] += rolagem * 0.6 * dt
        self.nuvens = [n for n in self.nuvens if n[1] < config.ALTURA + 50]
        while len(self.nuvens) < 5:
            self._nova()

    def desenhar(self, tela, transparencia=1.0):
        if not self.ativa or transparencia <= 0:
            return
        self.img.set_alpha(int(255 * transparencia))
        for x, y, _ in self.nuvens:
            tela.blit(self.img, (int(x), int(y)))
