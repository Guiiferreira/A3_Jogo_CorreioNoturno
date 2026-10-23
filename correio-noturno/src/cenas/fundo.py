"""Fundo animado dos menus: a cidade rolando devagar com o Bico voando."""
import math

from .. import config
from ..cenario import Cenario, Ceu
from ..recursos import imagem
from ..entidades import sombra


class FundoCidade:
    def __init__(self):
        self.cenario = Cenario("bairro", semente=42)
        self.ceu = Ceu()
        self.t = 0.0
        self.progresso_ceu = 0.08    # quase meia-noite

    def atualizar(self, dt):
        self.t += dt
        self.cenario.atualizar(dt, 30)

    def desenhar(self, tela, com_pombo=True):
        self.cenario.desenhar(tela)
        self.ceu.desenhar(tela, self.progresso_ceu)
        self.cenario.desenhar_luzes(tela, Ceu.escuridao(self.progresso_ceu))
        if com_pombo:
            x = config.LARGURA * 0.5 + math.sin(self.t * 0.6) * 300
            y = config.ALTURA * 0.72 + math.sin(self.t * 1.3) * 30
            sombra(tela, x + 10, y + 22, 34, 14)
            img = imagem(f"pombo_{[0, 1, 2, 1][int(self.t * 8) % 4]}")
            tela.blit(img, img.get_rect(center=(int(x), int(y))))
