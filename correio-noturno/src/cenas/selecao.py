"""Tela de escolha do pombo.

Os pombos ainda bloqueados aparecem como silhueta, com a dica de como liberar.
Setas escolhem, Enter confirma, Esc volta. Também funciona com o mouse.
"""
import math

import pygame

from .. import config, dados
from ..recursos import imagem
from ..ui import painel, paragrafo, texto, escurecer
from .base import Cena

_silhuetas = {}


def silhueta(nome):
    """Versão escura de um sprite (para pombos bloqueados)."""
    if nome not in _silhuetas:
        mascara = pygame.mask.from_surface(imagem(nome))
        _silhuetas[nome] = mascara.to_surface(setcolor=(14, 15, 30, 255),
                                              unsetcolor=(0, 0, 0, 0))
    return _silhuetas[nome]


def barras(personagem, vidas_base):
    """Valores de 1 a 5 para as barrinhas da ficha do pombo."""
    return [
        ("Velocidade", round(1 + (personagem["velocidade"] - 0.8) / 0.1)),
        ("Penas", vidas_base + personagem["vidas"]),
        ("Bolsa", personagem["capacidade"]),
        ("Arrancada", round(5 - (personagem["recarga"] - 0.8) / 0.3)),
        ("Contra o vento", round(5 - personagem["vento"] * 3)),
    ]


class SelecaoPombo(Cena):
    def __init__(self, jogo, pular_intro=False):
        super().__init__(jogo)
        self.pular_intro = pular_intro
        self.liberados = dados.carregar_liberados()
        ids = [p["id"] for p in config.PERSONAGENS]
        atual = jogo.opcoes.get("personagem", "bico")
        self.indice = ids.index(atual) if atual in self.liberados else 0
        self.slots = []
        self.tremer = 0.0          # balança o cadeado quando tenta escolher bloqueado
        jogo.audio.musica("menu")

    @property
    def escolhido(self):
        return config.PERSONAGENS[self.indice]

    def _liberado(self, i):
        return config.PERSONAGENS[i]["id"] in self.liberados

    def _mover(self, passo):
        self.indice = (self.indice + passo) % len(config.PERSONAGENS)
        self.jogo.audio.tocar("menu_mover")

    def _confirmar(self):
        if not self._liberado(self.indice):
            self.tremer = 0.4
            self.jogo.audio.tocar("dano", 0.5)
            return
        self.jogo.audio.tocar("menu_ok")
        self.jogo.opcoes["personagem"] = self.escolhido["id"]
        self.jogo.salvar_opcoes()
        from .partida import iniciar_jogo
        iniciar_jogo(self.jogo, pular_intro=self.pular_intro)

    def evento(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a):
                self._mover(-1)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self._mover(1)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._confirmar()
            elif e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                from .menu import MenuPrincipal
                self.jogo.trocar_cena(MenuPrincipal(self.jogo))
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.slots):
                if r.collidepoint(e.pos):
                    if i == self.indice:
                        self._confirmar()
                    else:
                        self.indice = i
                        self.jogo.audio.tocar("menu_mover")

    def atualizar(self, dt):
        super().atualizar(dt)
        self.jogo.fundo.atualizar(dt)
        self.tremer = max(0.0, self.tremer - dt)

    def desenhar(self, tela):
        self.jogo.fundo.desenhar(tela, com_pombo=False)
        escurecer(tela, 130)
        cx = config.LARGURA // 2
        texto(tela, "Quem voa esta noite?", 56, (cx, 46), config.COR_DESTAQUE, negrito=True)

        # ------------------------------------------------ fileira de pombos
        n = len(config.PERSONAGENS)
        largura, espaco = 150, 16
        x0 = cx - (n * largura + (n - 1) * espaco) // 2
        self.slots = []
        for i, pers in enumerate(config.PERSONAGENS):
            r = pygame.Rect(x0 + i * (largura + espaco), 88, largura, 120)
            self.slots.append(r)
            sel = i == self.indice
            painel(tela, r, alpha=235 if sel else 170,
                   borda=config.COR_DESTAQUE if sel else config.COR_BORDA)
            quadro = [0, 1, 2, 1][int(self.t * (10 if sel else 4)) % 4]
            nome_img = f"pombo_{pers['id']}_{quadro}"
            sobe = math.sin(self.t * 3 + i) * 3
            if self._liberado(i):
                img = imagem(nome_img)
                texto(tela, pers["nome"], 26, (r.centerx, r.bottom - 20),
                      config.COR_DESTAQUE if sel else config.COR_TEXTO)
            else:
                img = silhueta(nome_img)
                texto(tela, "???", 26, (r.centerx, r.bottom - 20), config.COR_TEXTO_APAGADO)
            img = pygame.transform.scale_by(img, 1.3)
            tela.blit(img, img.get_rect(center=(r.centerx, r.top + 48 + sobe)))

        # ------------------------------------------------ ficha do escolhido
        pers = self.escolhido
        livre = self._liberado(self.indice)
        ficha = pygame.Rect(60, 228, config.LARGURA - 120, 330)
        painel(tela, ficha)
        nome_retrato = "retrato_" + pers["id"]
        retrato = imagem(nome_retrato) if livre else silhueta(nome_retrato)
        retrato = pygame.transform.scale_by(retrato, 1.6)
        dx = math.sin(self.t * 60) * 6 * (self.tremer / 0.4) if self.tremer else 0
        tela.blit(retrato, retrato.get_rect(center=(ficha.left + 130 + dx, ficha.top + 120)))

        if livre:
            texto(tela, pers["nome"], 42, (ficha.left + 130, ficha.top + 240),
                  config.COR_DESTAQUE, negrito=True)
            texto(tela, pers["titulo"], 22, (ficha.left + 130, ficha.top + 272),
                  config.COR_TEXTO_APAGADO)
            x = ficha.left + 270
            y = paragrafo(tela, pers["descricao"], 28, x, ficha.top + 26, ficha.width - 300,
                          ancora_x="left")
            vidas_base = config.DIFICULDADES[self.jogo.opcoes["dificuldade"]]["vidas"]
            y = max(y + 14, ficha.top + 96)
            for rotulo, valor in barras(pers, vidas_base):
                texto(tela, rotulo, 24, (x, y), config.COR_TEXTO_APAGADO, ancora="midleft")
                for k in range(5):
                    caixa = pygame.Rect(x + 170 + k * 34, y - 9, 28, 18)
                    cor = config.COR_DESTAQUE if k < valor else (50, 54, 84)
                    pygame.draw.rect(tela, cor, caixa, border_radius=4)
                y += 34
            texto(tela, "Atenção: " + pers["especial"], 22, (x, y + 8), config.COR_PERIGO
                  if pers["especial"] not in ("Sem ponto fraco", "Secreto") else config.COR_SUCESSO,
                  ancora="midleft")
        else:
            texto(tela, "Bloqueado", 40, (ficha.left + 130, ficha.top + 240),
                  config.COR_TEXTO_APAGADO, negrito=True)
            x = ficha.left + 270
            texto(tela, "Como liberar:", 30, (x, ficha.top + 110), config.COR_DESTAQUE,
                  ancora="midleft")
            paragrafo(tela, config.dica_liberar(pers), 30, x, ficha.top + 140,
                      ficha.width - 300, ancora_x="left")
            if pers["libera"] != "vitoria":
                paragrafo(tela, "Você vai conhecer esse pombo pelo caminho.", 24, x,
                          ficha.top + 210, ficha.width - 300, cor=config.COR_TEXTO_APAGADO,
                          ancora_x="left")

        dica = ("Setas para escolher   ·   Enter para voar   ·   Esc para voltar" if livre
                else "Setas para escolher   ·   Esc para voltar")
        texto(tela, dica, 24, (cx, config.ALTURA - 40), config.COR_TEXTO_APAGADO)
        texto(tela, f"{len(self.liberados)} de {len(config.PERSONAGENS)} pombos liberados",
              22, (cx, config.ALTURA - 66), config.COR_TEXTO_APAGADO)
