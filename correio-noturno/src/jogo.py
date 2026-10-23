"""Classe principal: abre a janela, roda o laço do jogo e troca de telas.

Laço principal (game loop), repetido 60 vezes por segundo:
    1. entrada   -> lê eventos (teclado, mouse, fechar janela)
    2. atualizar -> move personagens, checa colisões, conta o tempo
    3. desenhar  -> pinta tudo na tela e mostra (flip)
"""
import os
import time

import pygame

from . import config, dados
from .recursos import Audio, imagem
from .ui import texto
from .cenas.fundo import FundoCidade
from .cenas.menu import MenuPrincipal


class Jogo:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            print("Aviso: sem dispositivo de som, o jogo vai rodar mudo.")

        self.opcoes = dados.carregar_opcoes()
        self.tela = pygame.display.set_mode((config.LARGURA, config.ALTURA), pygame.SCALED)
        pygame.display.set_caption(config.TITULO)
        pygame.display.set_icon(imagem("icone"))
        if self.opcoes["tela_cheia"]:
            pygame.display.toggle_fullscreen()

        self.relogio = pygame.time.Clock()
        self.audio = Audio(self.opcoes["vol_musica"], self.opcoes["vol_efeitos"],
                           self.opcoes["mudo"])
        self.fundo = FundoCidade()
        self.rodando = True
        self.cena = MenuPrincipal(self)
        self.aviso = ("", 0.0)     # mensagem rápida no canto (ex.: captura salva)

    def trocar_cena(self, nova):
        self.cena = nova

    def salvar_opcoes(self):
        self.opcoes["vol_musica"] = self.audio.vol_musica
        self.opcoes["vol_efeitos"] = self.audio.vol_efeitos
        self.opcoes["mudo"] = self.audio.mudo
        dados.salvar_opcoes(self.opcoes)

    def alternar_tela_cheia(self):
        pygame.display.toggle_fullscreen()
        self.opcoes["tela_cheia"] = not self.opcoes["tela_cheia"]
        self.salvar_opcoes()

    def capturar_tela(self):
        pasta = os.path.join(config.RAIZ, "docs", "capturas")
        os.makedirs(pasta, exist_ok=True)
        nome = time.strftime("captura_%Y%m%d_%H%M%S.png")
        pygame.image.save(self.tela, os.path.join(pasta, nome))
        self.aviso = (f"Captura salva em docs/capturas/{nome}", 2.5)

    def tratar_evento(self, e):
        """Teclas que funcionam em qualquer tela; o resto vai para a cena atual."""
        if e.type == pygame.QUIT:
            self.rodando = False
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_m and not getattr(self.cena, "digitando", False):
                self.audio.alternar_mudo()
                self.salvar_opcoes()
                return
            if e.key == pygame.K_F11:
                self.alternar_tela_cheia()
                return
            if e.key == pygame.K_F12:
                self.capturar_tela()
                return
        self.cena.evento(e)

    def passo(self, dt):
        """Um quadro do jogo (separado para poder testar sem janela)."""
        for e in pygame.event.get():
            self.tratar_evento(e)
        self.cena.atualizar(dt)
        self.cena.desenhar(self.tela)
        msg, tempo = self.aviso
        if tempo > 0:
            texto(self.tela, msg, 22, (12, config.ALTURA - 12), config.COR_SUCESSO,
                  ancora="bottomleft")
            self.aviso = (msg, tempo - dt)

    def rodar(self):
        while self.rodando:
            # dt = segundos desde o último quadro (limitado para não "teleportar"
            # personagens se o computador engasgar)
            dt = min(self.relogio.tick(config.FPS) / 1000, 0.05)
            self.passo(dt)
            pygame.display.flip()
        self.salvar_opcoes()
        pygame.quit()
