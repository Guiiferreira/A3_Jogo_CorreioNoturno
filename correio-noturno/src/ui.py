"""Funções de interface: texto com sombra, painéis, quebra de linha e menus."""
import math

import pygame

from . import config
from .recursos import fonte, imagem


def texto(tela, msg, tamanho, pos, cor=config.COR_TEXTO, ancora="center",
          sombra=True, negrito=False, alpha=255):
    """Desenha texto com sombra para ficar legível sobre qualquer fundo."""
    f = fonte(tamanho, negrito)
    img = f.render(msg, True, cor)
    rect = img.get_rect(**{ancora: pos})
    if sombra:
        sombra_img = f.render(msg, True, (8, 8, 18))
        if alpha < 255:
            sombra_img.set_alpha(alpha)
        tela.blit(sombra_img, rect.move(2, 2))
    if alpha < 255:
        img.set_alpha(alpha)
    tela.blit(img, rect)
    return rect


def quebrar_linhas(msg, tamanho, largura_max):
    """Quebra um texto em linhas que caibam na largura (respeita \\n)."""
    f = fonte(tamanho)
    linhas = []
    for paragrafo in msg.split("\n"):
        if not paragrafo:
            linhas.append("")
            continue
        atual = ""
        for palavra in paragrafo.split(" "):
            teste = (atual + " " + palavra).strip()
            if f.size(teste)[0] <= largura_max:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        linhas.append(atual)
    return linhas


def paragrafo(tela, msg, tamanho, centro_x, topo, largura_max,
              cor=config.COR_TEXTO, espaco=1.25, ancora_x="center"):
    y = topo
    for linha in quebrar_linhas(msg, tamanho, largura_max):
        if ancora_x == "center":
            texto(tela, linha, tamanho, (centro_x, y), cor, ancora="midtop")
        else:
            texto(tela, linha, tamanho, (centro_x, y), cor, ancora="topleft")
        y += int(tamanho * espaco * 0.75)
    return y


def painel(tela, rect, alpha=225, borda=config.COR_BORDA):
    """Retângulo escuro semitransparente com borda (estilo do jogo)."""
    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (*config.COR_PAINEL, alpha), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (*borda, 255), surf.get_rect(), 3, border_radius=10)
    tela.blit(surf, rect)


def escurecer(tela, alpha=150, cor=(8, 8, 20)):
    veu = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    veu.fill((*cor, alpha))
    tela.blit(veu, (0, 0))


class Menu:
    """Lista de opções navegável com setas/W/S e Enter.

    opcoes: lista de textos. O texto pode ser uma função (para valores que mudam,
    ex.: "Música: 6").
    """

    def __init__(self, opcoes, audio, tamanho=40, espaco=52):
        self.opcoes = opcoes
        self.audio = audio
        self.indice = 0
        self.tamanho = tamanho
        self.espaco = espaco
        self.tempo = 0.0
        self.rects = []

    def rotulo(self, i):
        op = self.opcoes[i]
        return op() if callable(op) else op

    def tratar(self, evento):
        """Devolve ('escolher', i), ('esquerda', i), ('direita', i) ou None."""
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - 1) % len(self.opcoes)
                self.audio.tocar("menu_mover")
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.indice = (self.indice + 1) % len(self.opcoes)
                self.audio.tocar("menu_mover")
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.audio.tocar("menu_ok")
                return ("escolher", self.indice)
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                return ("esquerda", self.indice)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                return ("direita", self.indice)
        elif evento.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(evento.pos) and i != self.indice:
                    self.indice = i
                    self.audio.tocar("menu_mover")
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(evento.pos):
                    self.indice = i
                    self.audio.tocar("menu_ok")
                    return ("escolher", i)
        return None

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela, centro_x, topo):
        self.rects = []
        for i in range(len(self.opcoes)):
            y = topo + i * self.espaco
            selecionado = i == self.indice
            cor = config.COR_DESTAQUE if selecionado else config.COR_TEXTO_APAGADO
            rotulo = self.rotulo(i)
            r = texto(tela, rotulo, self.tamanho, (centro_x, y), cor)
            self.rects.append(r.inflate(40, 10))
            if selecionado:
                # cartinha balançando ao lado da opção escolhida
                img = pygame.transform.rotate(
                    _icone_carta(), 8 * math.sin(self.tempo * 5))
                tela.blit(img, img.get_rect(midright=(r.left - 14, y)))


def _icone_carta():
    return imagem("carta_hud")
