"""HUD: barra no topo com penas (vidas), bolsa de cartas, relógio, entregas e pontos.

Fica numa faixa fina e semitransparente para não cobrir a ação.
"""
import math

import pygame

from . import config
from .recursos import imagem
from .ui import texto

ALTURA_HUD = 52


def hora_texto(minutos):
    h = config.HORA_INICIO + int(minutos) // 60
    m = int(minutos) % 60
    return f"{h:02d}:{m:02d}"


def desenhar(tela, partida):
    p = partida.pombo
    faixa = pygame.Surface((config.LARGURA, ALTURA_HUD), pygame.SRCALPHA)
    faixa.fill((12, 12, 28, 190))
    pygame.draw.line(faixa, (*config.COR_BORDA, 255), (0, ALTURA_HUD - 1),
                     (config.LARGURA, ALTURA_HUD - 1), 2)
    tela.blit(faixa, (0, 0))

    # ---- penas (vidas)
    x = 14
    for i in range(max(p.vidas, p.vidas_iniciais)):
        img = imagem("pena_hud" if i < p.vidas else "pena_hud_vazia")
        tela.blit(img, (x, 14))
        x += 24
    # ---- bolsa
    x += 16
    texto(tela, "Bolsa", 20, (x, 8), config.COR_TEXTO_APAGADO, ancora="topleft")
    for i in range(p.capacidade):
        img = imagem("carta_hud" if i < p.cartas else "carta_hud_vazia")
        tela.blit(img, (x + i * 28, 26))
    if p.carta_especial:
        tela.blit(imagem("carta_especial_hud"), (x + p.capacidade * 28 + 6, 26))

    # ---- relógio no centro + barra da noite (lua -> sol)
    cx = config.LARGURA // 2
    minutos = partida.minutos
    urgente = minutos >= config.MINUTOS_NOITE - 45
    cor = config.COR_PERIGO if urgente and int(partida.t * 4) % 2 == 0 else config.COR_TEXTO
    texto(tela, hora_texto(minutos), 40, (cx, 20), cor, negrito=True)
    barra = pygame.Rect(cx - 110, 38, 220, 8)
    pygame.draw.rect(tela, (40, 44, 70), barra, border_radius=4)
    prog = min(1, minutos / config.MINUTOS_NOITE)
    preenchido = barra.copy()
    preenchido.width = max(4, int(barra.width * prog))
    cor_barra = (int(90 + 165 * prog), int(110 + 60 * prog), int(200 - 120 * prog))
    pygame.draw.rect(tela, cor_barra, preenchido, border_radius=4)
    pygame.draw.circle(tela, (230, 230, 245), (barra.left - 12, barra.centery), 6)  # lua
    pygame.draw.circle(tela, (40, 44, 70), (barra.left - 9, barra.centery - 2), 5)
    pygame.draw.circle(tela, (255, 190, 80), (barra.right + 12, barra.centery), 6)  # sol

    # ---- fase e entregas
    fase = partida.fase
    if partida.indo_para_torre:
        meta_txt = "Leve a carta à torre!"
        cor_meta = config.COR_DESTAQUE
    else:
        meta_txt = f"Entregas {partida.entregas_fase}/{fase['meta']}"
        cor_meta = config.COR_TEXTO
    texto(tela, f"Fase {partida.indice_fase + 1}: {fase['nome']}", 20,
          (636, 8), config.COR_TEXTO_APAGADO, ancora="topleft")
    texto(tela, meta_txt, 24, (636, 28), cor_meta, ancora="topleft")
    texto(tela, f"{partida.pontos:06d}", 30, (config.LARGURA - 14, 18),
          config.COR_DESTAQUE, ancora="midright", negrito=True)
    if partida.combo >= 2:
        texto(tela, f"combo x{partida.combo}", 20, (config.LARGURA - 14, 40),
              config.COR_SUCESSO, ancora="midright")

    # ---- power-ups ativos (canto inferior esquerdo)
    y = config.ALTURA - 40
    for nome, tempo, total, img in (("Pão", p.pao, config.DURACAO_PAO, "pao"),
                                    ("Lanterna", p.lanterna, config.DURACAO_LANTERNA, "lanterna")):
        if tempo > 0:
            icone = imagem(img)
            tela.blit(icone, icone.get_rect(midleft=(14, y)))
            pygame.draw.rect(tela, (40, 44, 70), (52, y - 4, 90, 8), border_radius=4)
            pygame.draw.rect(tela, config.COR_DESTAQUE, (52, y - 4, int(90 * tempo / total), 8),
                             border_radius=4)
            texto(tela, nome, 18, (52, y - 8), config.COR_TEXTO, ancora="bottomleft")
            y -= 44

    # ---- recarga da arrancada (arco em volta do pombo)
    if p.recarga > 0:
        frac = 1 - p.recarga / p.tempo_recarga
        r = pygame.Rect(0, 0, 50, 50)
        r.center = (int(p.x), int(p.y))
        pygame.draw.arc(tela, (150, 200, 255), r, math.pi / 2, math.pi / 2 + math.tau * frac, 3)

    # ---- dica de som mudo
    if partida.jogo.audio.mudo:
        texto(tela, "SOM DESLIGADO (M)", 18, (config.LARGURA - 14, config.ALTURA - 14),
              config.COR_TEXTO_APAGADO, ancora="bottomright")
