"""Tela de fim de jogo: resultado, pontuação, recorde e opção de jogar de novo."""
import pygame

from .. import config, dados
from ..recursos import imagem
from ..ui import Menu, painel, texto, escurecer
from .base import Cena

TITULOS = {
    "vitoria": ("Todas as cartas entregues!", config.COR_SUCESSO),
    "amanheceu": ("O sol nasceu primeiro", config.COR_DESTAQUE),
    "sem_penas": ("{nome} ficou sem forças", config.COR_PERIGO),
}


class TelaFim(Cena):
    def __init__(self, jogo, resumo):
        super().__init__(jogo)
        self.r = resumo
        self.digitando = dados.entra_no_ranking(resumo["pontos"])
        self.nome = ""
        self.posicao = None
        self.menu = Menu(["Jogar de novo", "Trocar de pombo", "Recordes", "Menu principal"],
                         jogo.audio, tamanho=36, espaco=42)
        if self.digitando:
            pygame.key.start_text_input()

    def evento(self, e):
        if self.digitando:
            if e.type == pygame.TEXTINPUT:
                for ch in e.text.upper():
                    if ch.isalnum() and len(self.nome) < 3:
                        self.nome += ch
                        self.jogo.audio.tocar("menu_mover")
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    self.nome = self.nome[:-1]
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.nome:
                    self._salvar_recorde()
            return
        r = self.menu.tratar(e)
        if r and r[0] == "escolher":
            escolha = self.menu.rotulo(r[1])
            if escolha == "Jogar de novo":
                from .partida import iniciar_jogo
                iniciar_jogo(self.jogo, pular_intro=True)
            elif escolha == "Trocar de pombo":
                from .selecao import SelecaoPombo
                self.jogo.trocar_cena(SelecaoPombo(self.jogo, pular_intro=True))
            elif escolha == "Recordes":
                from .telas import Recordes
                self.jogo.trocar_cena(Recordes(self.jogo))
            else:
                from .menu import MenuPrincipal
                self.jogo.trocar_cena(MenuPrincipal(self.jogo))

    def _salvar_recorde(self):
        lista = dados.adicionar_recorde(self.nome, self.r["pontos"], self.r["dificuldade"],
                                        self.r["resultado"] == "vitoria", self.r["pombo"])
        for i, rec in enumerate(lista):
            if rec["nome"] == self.nome and rec["pontos"] == self.r["pontos"]:
                self.posicao = i + 1
                break
        self.digitando = False
        pygame.key.stop_text_input()
        self.jogo.audio.tocar("powerup")

    def atualizar(self, dt):
        super().atualizar(dt)
        self.jogo.fundo.atualizar(dt)
        self.menu.atualizar(dt)

    def desenhar(self, tela):
        self.jogo.fundo.desenhar(tela, com_pombo=self.r["resultado"] == "vitoria")
        escurecer(tela, 120)
        cx = config.LARGURA // 2
        titulo, cor = TITULOS[self.r["resultado"]]
        titulo = titulo.format(nome=config.PERSONAGENS_POR_ID[self.r["pombo"]]["nome"])
        texto(tela, titulo, 60, (cx, 64), cor, negrito=True)

        linhas = [
            ("Cartas entregues", str(self.r["entregas"])),
            ("Chegou até a fase", f"{self.r['fase']} de {len(config.FASES)}"),
            ("Hora final", self.r["hora"]),
        ]
        if self.r["resultado"] == "vitoria":
            linhas += [("Bônus de tempo", f"+{self.r['bonus_tempo']}"),
                       ("Bônus de penas", f"+{self.r['bonus_penas']}")]
        caixa = pygame.Rect(cx - 280, 110, 560, 90 + 34 * len(linhas))
        painel(tela, caixa)
        y = caixa.top + 32
        for rotulo, valor in linhas:
            texto(tela, rotulo, 28, (caixa.left + 40, y), config.COR_TEXTO_APAGADO, ancora="midleft")
            texto(tela, valor, 28, (caixa.right - 40, y), ancora="midright")
            y += 34
        pygame.draw.line(tela, config.COR_BORDA, (caixa.left + 30, caixa.bottom - 52),
                         (caixa.right - 30, caixa.bottom - 52), 2)
        texto(tela, "PONTOS", 32, (caixa.left + 40, caixa.bottom - 26), config.COR_DESTAQUE,
              ancora="midleft")
        texto(tela, f"{self.r['pontos']:06d}", 44, (caixa.right - 40, caixa.bottom - 26),
              config.COR_DESTAQUE, ancora="midright", negrito=True)
        if self.r["resultado"] == "vitoria":
            img = pygame.transform.rotozoom(imagem("carta_especial"), 10, 1.3)
            tela.blit(img, img.get_rect(center=(caixa.right + 50, caixa.top + 20)))

        if self.digitando:
            texto(tela, "Novo recorde! Digite suas iniciais:", 32, (cx, 410), config.COR_SUCESSO)
            for i in range(3):
                r = pygame.Rect(0, 0, 56, 64)
                r.center = (cx - 70 + i * 70, 475)
                pygame.draw.rect(tela, config.COR_PAINEL, r, border_radius=8)
                ativo = i == len(self.nome)
                pygame.draw.rect(tela, config.COR_DESTAQUE if ativo else config.COR_BORDA, r, 3,
                                 border_radius=8)
                if i < len(self.nome):
                    texto(tela, self.nome[i], 54, r.center, config.COR_DESTAQUE)
                elif ativo and int(self.t * 3) % 2 == 0:
                    texto(tela, "_", 54, r.center, config.COR_TEXTO_APAGADO)
            texto(tela, "Enter para salvar", 24, (cx, 540), config.COR_TEXTO_APAGADO)
        else:
            if self.posicao:
                texto(tela, f"Você ficou em {self.posicao}º lugar no ranking!", 28, (cx, 392),
                      config.COR_SUCESSO)
            self.menu.desenhar(tela, cx, 450)
