"""Menu principal."""
import math

import pygame

from .. import config
from ..recursos import imagem
from ..ui import Menu, texto, escurecer
from .base import Cena


class MenuPrincipal(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        jogo.fundo.progresso_ceu = 0.08
        jogo.audio.musica("menu")
        self.menu = Menu(["Jogar", "Como jogar", "Opções", "Recordes", "Créditos", "Sair"],
                         jogo.audio, tamanho=42, espaco=47)

    def evento(self, e):
        r = self.menu.tratar(e)
        if not r or r[0] != "escolher":
            return
        escolha = self.menu.rotulo(r[1])
        from . import telas
        from .selecao import SelecaoPombo
        if escolha == "Jogar":
            self.jogo.trocar_cena(SelecaoPombo(self.jogo))
        elif escolha == "Como jogar":
            self.jogo.trocar_cena(telas.ComoJogar(self.jogo))
        elif escolha == "Opções":
            self.jogo.trocar_cena(telas.Opcoes(self.jogo))
        elif escolha == "Recordes":
            self.jogo.trocar_cena(telas.Recordes(self.jogo))
        elif escolha == "Créditos":
            self.jogo.trocar_cena(telas.Creditos(self.jogo))
        elif escolha == "Sair":
            self.jogo.rodando = False

    def atualizar(self, dt):
        super().atualizar(dt)
        self.jogo.fundo.atualizar(dt)
        self.menu.atualizar(dt)

    def desenhar(self, tela):
        self.jogo.fundo.desenhar(tela)
        escurecer(tela, 70)
        cx = config.LARGURA // 2
        # título com leve balanço
        y = 110 + math.sin(self.t * 1.5) * 4
        texto(tela, "CORREIO", 96, (cx, y), config.COR_DESTAQUE, negrito=True)
        texto(tela, "NOTURNO", 96, (cx, y + 70), config.COR_TEXTO, negrito=True)
        carta = pygame.transform.rotozoom(imagem("carta_especial"), math.sin(self.t * 2) * 8, 1.4)
        tela.blit(carta, carta.get_rect(center=(cx + 230, y - 10)))
        texto(tela, "Um pombo, uma noite e nenhuma carta atrasada.", 26,
              (cx, y + 125), config.COR_TEXTO_APAGADO)
        self.menu.desenhar(tela, cx, 318)
        dif = self.jogo.opcoes["dificuldade"]
        texto(tela, f"Dificuldade: {dif}   ·   Setas e Enter   ·   M = som", 22,
              (cx, config.ALTURA - 22), config.COR_TEXTO_APAGADO)
