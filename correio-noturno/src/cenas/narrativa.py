"""Tela de história: mostra textos em sequência com efeito de máquina de escrever.

Usada na introdução e nos finais. Enter avança, Esc pula tudo.
"""
import pygame

from .. import config
from ..recursos import imagem
from ..ui import painel, paragrafo, texto, escurecer
from .base import Cena

LETRAS_POR_SEG = 48


class Narrativa(Cena):
    def __init__(self, jogo, telas, ao_terminar, titulo=None, progresso_ceu=None,
                 musica="menu"):
        super().__init__(jogo)
        self.telas = telas
        self.ao_terminar = ao_terminar
        self.titulo = titulo
        self.indice = 0
        self.letras = 0.0
        self.terminou = False
        if progresso_ceu is not None:
            jogo.fundo.progresso_ceu = progresso_ceu
        if musica:
            jogo.audio.musica(musica)

    def _texto_atual(self):
        tela = self.telas[self.indice]
        return tela.get("fala") or tela.get("texto", "")

    def evento(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._avancar()
            elif e.key == pygame.K_ESCAPE:
                self._terminar()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self._avancar()

    def _avancar(self):
        if self.terminou:
            return
        if self.letras < len(self._texto_atual()):
            self.letras = len(self._texto_atual())   # completa o texto
            return
        self.jogo.audio.tocar("menu_mover")
        self.indice += 1
        self.letras = 0
        if self.indice >= len(self.telas):
            self._terminar()

    def _terminar(self):
        if not self.terminou:          # evita chamar duas vezes
            self.terminou = True
            self.ao_terminar()

    def atualizar(self, dt):
        super().atualizar(dt)
        self.jogo.fundo.atualizar(dt)
        if self.indice < len(self.telas):
            self.letras = min(len(self._texto_atual()), self.letras + LETRAS_POR_SEG * dt)

    def desenhar(self, tela):
        self.jogo.fundo.desenhar(tela, com_pombo=False)
        escurecer(tela, 110)
        if self.indice >= len(self.telas):
            return
        atual = self.telas[self.indice]
        if self.titulo:
            texto(tela, self.titulo, 52, (config.LARGURA // 2, 90), config.COR_DESTAQUE, negrito=True)

        caixa = pygame.Rect(90, 190, config.LARGURA - 180, 300)
        painel(tela, caixa)
        visivel = self._texto_atual()[:int(self.letras)]
        if "fala" in atual:
            quem = atual.get("quem", "bico")
            retrato = imagem("retrato_" + quem)
            tela.blit(retrato, retrato.get_rect(midleft=(caixa.left + 30, caixa.centery)))
            texto(tela, config.PERSONAGENS_POR_ID[quem]["nome"], 30, (caixa.left + 30 + 48, caixa.centery + 68),
                  config.COR_DESTAQUE)
            paragrafo(tela, '"' + visivel + '"' if visivel else "", 36,
                      caixa.left + 170, caixa.top + 100, caixa.width - 210,
                      ancora_x="left")
        else:
            paragrafo(tela, visivel, 34, caixa.centerx, caixa.top + 50, caixa.width - 90)

        # bolinhas de progresso + dica de tecla
        for i in range(len(self.telas)):
            cor = config.COR_DESTAQUE if i == self.indice else (70, 74, 100)
            pygame.draw.circle(tela, cor, (config.LARGURA // 2 - (len(self.telas) - 1) * 12 + i * 24,
                                           caixa.bottom + 30), 6)
        if self.letras >= len(self._texto_atual()) and int(self.t * 2) % 2 == 0:
            texto(tela, "Enter para continuar  ·  Esc para pular", 24,
                  (config.LARGURA // 2, config.ALTURA - 40), config.COR_TEXTO_APAGADO)
