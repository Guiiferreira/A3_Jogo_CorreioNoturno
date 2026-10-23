"""Carrega imagens, sons e fontes uma única vez e guarda em cache."""
import os

import pygame

from . import config

_imagens = {}
_fontes = {}


def imagem(nome):
    """Devolve a imagem assets/img/<nome>.png (carregada só na 1ª vez)."""
    if nome not in _imagens:
        caminho = os.path.join(config.PASTA_IMG, nome + ".png")
        _imagens[nome] = pygame.image.load(caminho).convert_alpha()
    return _imagens[nome]


def fonte(tamanho, negrito=False):
    chave = (tamanho, negrito)
    if chave not in _fontes:
        f = pygame.font.Font(None, tamanho)
        f.set_bold(negrito)
        _fontes[chave] = f
    return _fontes[chave]


class Audio:
    """Controla efeitos (pygame.mixer.Sound) e trilha (pygame.mixer.music).

    Funciona mesmo em computador sem placa de som: nesse caso fica mudo.
    """

    EFEITOS = ["asa", "coleta", "entrega", "dano", "choque", "miado", "corvo",
               "powerup", "vento", "tique", "menu_mover", "menu_ok", "pausa",
               "sino", "vitoria", "derrota", "galo"]

    def __init__(self, vol_musica=6, vol_efeitos=7, mudo=False):
        self.vol_musica = vol_musica      # 0 a 10
        self.vol_efeitos = vol_efeitos    # 0 a 10
        self.mudo = mudo
        self.trilha_atual = None
        self.sons = {}
        self.ativo = pygame.mixer.get_init() is not None
        if not self.ativo:
            return
        pygame.mixer.set_num_channels(16)
        for nome in self.EFEITOS:
            caminho = os.path.join(config.PASTA_SONS, nome + ".wav")
            self.sons[nome] = pygame.mixer.Sound(caminho)

    # ---------------------------------------------------------- efeitos
    def tocar(self, nome, volume=1.0):
        if not self.ativo or self.mudo or self.vol_efeitos == 0:
            return
        som = self.sons.get(nome)
        if som:
            som.set_volume(volume * self.vol_efeitos / 10)
            som.play()

    # ---------------------------------------------------------- música
    def musica(self, nome, repetir=True):
        """Troca a trilha. Não reinicia se já estiver tocando a mesma."""
        if not self.ativo or nome == self.trilha_atual:
            return
        self.trilha_atual = nome
        caminho = os.path.join(config.PASTA_SONS, "musica_" + nome + ".wav")
        pygame.mixer.music.load(caminho)
        self._aplicar_volume_musica()
        pygame.mixer.music.play(-1 if repetir else 0, fade_ms=600)

    def parar_musica(self, fade_ms=500):
        if self.ativo:
            pygame.mixer.music.fadeout(fade_ms)
        self.trilha_atual = None

    def _aplicar_volume_musica(self):
        if self.ativo:
            vol = 0 if self.mudo else self.vol_musica / 10 * 0.8
            pygame.mixer.music.set_volume(vol)

    def alternar_mudo(self):
        self.mudo = not self.mudo
        self._aplicar_volume_musica()
        return self.mudo

    def ajustar(self, musica=None, efeitos=None):
        if musica is not None:
            self.vol_musica = max(0, min(10, musica))
        if efeitos is not None:
            self.vol_efeitos = max(0, min(10, efeitos))
        self._aplicar_volume_musica()
