"""Telas simples acessadas pelo menu: Como jogar, Opções, Recordes e Créditos."""
import pygame

from .. import config, dados
from ..recursos import imagem
from ..ui import Menu, painel, texto, escurecer, paragrafo
from .base import Cena


class TelaComFundo(Cena):
    """Tela com o fundo da cidade e Esc para voltar ao menu."""
    titulo = ""

    def voltar(self):
        from .menu import MenuPrincipal
        self.jogo.audio.tocar("menu_ok")
        self.jogo.trocar_cena(MenuPrincipal(self.jogo))

    def evento(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.voltar()

    def atualizar(self, dt):
        super().atualizar(dt)
        self.jogo.fundo.atualizar(dt)

    def desenhar(self, tela):
        self.jogo.fundo.desenhar(tela, com_pombo=False)
        escurecer(tela, 120)
        texto(tela, self.titulo, 56, (config.LARGURA // 2, 50), config.COR_DESTAQUE, negrito=True)
        texto(tela, "Esc para voltar", 22, (config.LARGURA // 2, config.ALTURA - 20),
              config.COR_TEXTO_APAGADO)


# ============================================================== como jogar
class ComoJogar(TelaComFundo):
    titulo = "Como jogar"

    ITENS = [
        ("carta", "Carta perdida: pegue e guarde na bolsa."),
        ("janela_acesa", "Janela acesa: passe por cima para entregar."),
        ("gato_1", "Gato: quando aparece o \"!\", ele dá o bote."),
        ("poste", "Fio azul dá choque. Fio cinza está desligado."),
        ("corvo_0", "Corvo: persegue você e rouba cartas."),
        ("pao", "Pão: voa mais rápido por alguns segundos."),
        ("lanterna", "Lanterna: aponta a janela e corta a neblina."),
        ("asa_extra", "Asa extra: recupera uma pena (vida)."),
    ]

    def desenhar(self, tela):
        super().desenhar(tela)
        # coluna da esquerda: controles
        esq = pygame.Rect(40, 100, 380, 300)
        painel(tela, esq)
        texto(tela, "Controles", 34, (esq.centerx, esq.top + 26), config.COR_DESTAQUE)
        y = esq.top + 64
        for tecla, acao in config.CONTROLES:
            texto(tela, tecla, 24, (esq.left + 20, y), config.COR_DESTAQUE, ancora="midleft")
            texto(tela, acao, 24, (esq.left + 175, y), ancora="midleft")
            y += 36

        # regras
        reg = pygame.Rect(40, 414, 380, 186)
        painel(tela, reg)
        texto(tela, "Regras", 34, (reg.centerx, reg.top + 24), config.COR_DESTAQUE)
        paragrafo(tela, "Cumpra a meta de entregas de cada fase antes das 6h. "
                        "No fim, leve a carta dourada até a Torre do Relógio. "
                        "Perde se amanhecer ou se acabarem as penas. "
                        "Entregas seguidas sem levar dano valem combo.",
                  22, reg.centerx, reg.top + 50, reg.width - 30)

        # coluna da direita: objetos
        dir_ = pygame.Rect(440, 100, 480, 500)
        painel(tela, dir_)
        texto(tela, "O que tem na cidade", 34, (dir_.centerx, dir_.top + 26), config.COR_DESTAQUE)
        y = dir_.top + 76
        for nome, desc in self.ITENS:
            img = imagem(nome)
            if img.get_height() > 44:
                img = pygame.transform.scale(img, (40, 40))
            tela.blit(img, img.get_rect(center=(dir_.left + 40, y)))
            texto(tela, desc, 23, (dir_.left + 76, y), ancora="midleft")
            y += 52


# ============================================================== opções
class Opcoes(TelaComFundo):
    titulo = "Opções"

    def __init__(self, jogo):
        super().__init__(jogo)
        op = jogo.opcoes
        self.menu = Menu([
            lambda: f"Dificuldade:  < {op['dificuldade']} >",
            lambda: f"Música:  < {jogo.audio.vol_musica} >",
            lambda: f"Efeitos:  < {jogo.audio.vol_efeitos} >",
            lambda: f"Som:  {'desligado' if jogo.audio.mudo else 'ligado'}",
            lambda: f"Tela cheia:  {'sim' if op['tela_cheia'] else 'não'}",
            lambda: "Enter de novo para zerar" if self.confirmar > 0 else "Zerar progresso",
            "Voltar",
        ], jogo.audio, tamanho=38, espaco=48)
        self.confirmar = 0.0    # segundos que o pedido de confirmação fica valendo
        self.aviso = 0.0        # segundos que a mensagem "progresso zerado" fica na tela

    def evento(self, e):
        super().evento(e)
        r = self.menu.tratar(e)
        if not r:
            return
        acao, i = r
        passo = -1 if acao == "esquerda" else 1
        op, audio = self.jogo.opcoes, self.jogo.audio
        if i == 0:
            ordem = config.ORDEM_DIFICULDADES
            op["dificuldade"] = ordem[(ordem.index(op["dificuldade"]) + passo) % len(ordem)]
        elif i == 1:
            audio.ajustar(musica=audio.vol_musica + passo)
        elif i == 2:
            audio.ajustar(efeitos=audio.vol_efeitos + passo)
            audio.tocar("coleta")
        elif i == 3:
            audio.alternar_mudo()
        elif i == 4:
            self.jogo.alternar_tela_cheia()
        elif i == 5:
            if acao != "escolher":
                return
            # pede confirmação: só zera no segundo Enter
            if self.confirmar > 0:
                dados.zerar_liberados()
                self.jogo.opcoes["personagem"] = "bico"
                self.confirmar, self.aviso = 0.0, 3.0
                self.jogo.audio.tocar("derrota", 0.5)
            else:
                self.confirmar = 4.0
                self.jogo.audio.tocar("menu_mover")
        elif i == 6 and acao == "escolher":
            self.voltar()
            return
        self.jogo.salvar_opcoes()

    def atualizar(self, dt):
        super().atualizar(dt)
        self.menu.atualizar(dt)
        if self.menu.indice != 5:
            self.confirmar = 0.0
        self.confirmar = max(0.0, self.confirmar - dt)
        self.aviso = max(0.0, self.aviso - dt)

    def desenhar(self, tela):
        super().desenhar(tela)
        caixa = pygame.Rect(180, 110, 600, 430)
        painel(tela, caixa)
        self.menu.desenhar(tela, config.LARGURA // 2, 155)
        if self.aviso > 0:
            msg, cor = "Progresso zerado: só o Bico está liberado.", config.COR_SUCESSO
        elif self.confirmar > 0:
            msg, cor = "Os pombos liberados voltam a ficar bloqueados. Recordes e opções ficam.", config.COR_PERIGO
        else:
            n = len(dados.carregar_liberados())
            msg, cor = f"{n} de {len(config.PERSONAGENS)} pombos liberados", config.COR_TEXTO_APAGADO
        texto(tela, msg, 22, (config.LARGURA // 2, caixa.bottom - 56), cor)
        texto(tela, "Use < e > (ou A e D) para mudar os valores", 22,
              (config.LARGURA // 2, caixa.bottom + 30), config.COR_TEXTO_APAGADO)
        d = config.DIFICULDADES[self.jogo.opcoes["dificuldade"]]
        minutos = d["segundos_noite"] / 60
        texto(tela, f"A noite dura ~{minutos:.1f} min reais · {d['vidas']} penas", 22,
              (config.LARGURA // 2, caixa.bottom - 24), config.COR_TEXTO_APAGADO)


# ============================================================== recordes
class Recordes(TelaComFundo):
    titulo = "Recordes"

    def __init__(self, jogo):
        super().__init__(jogo)
        self.lista = dados.carregar_recordes()

    def desenhar(self, tela):
        super().desenhar(tela)
        caixa = pygame.Rect(160, 110, 640, 420)
        painel(tela, caixa)
        cab_y = caixa.top + 40
        cols = [caixa.left + 50, caixa.left + 130, caixa.left + 280, caixa.left + 440]
        for x, nome in zip(cols, ["#", "Nome", "Pontos", "Dificuldade"]):
            texto(tela, nome, 28, (x, cab_y), config.COR_DESTAQUE, ancora="midleft")
        if not self.lista:
            texto(tela, "Ainda não há recordes. Vá entregar umas cartas!", 28,
                  (caixa.centerx, caixa.centery))
        for i, r in enumerate(self.lista):
            y = cab_y + 60 + i * 56
            cor = config.COR_DESTAQUE if i == 0 else config.COR_TEXTO
            texto(tela, f"{i + 1}º", 32, (cols[0], y), cor, ancora="midleft")
            pombo = pygame.transform.scale_by(imagem(f"pombo_{r.get('pombo', 'bico')}_0"), 0.75)
            tela.blit(pombo, pombo.get_rect(center=(cols[1] + 14, y)))
            texto(tela, r["nome"], 32, (cols[1] + 40, y), cor, ancora="midleft")
            texto(tela, f"{r['pontos']:06d}", 32, (cols[2], y), cor, ancora="midleft")
            texto(tela, r["dificuldade"], 28, (cols[3], y), cor, ancora="midleft")
            if r.get("venceu"):
                img = imagem("carta_especial_hud")
                tela.blit(img, img.get_rect(midleft=(cols[3] + 120, y)))


# ============================================================== créditos
class Creditos(TelaComFundo):
    titulo = "Créditos"

    INTEGRANTES = [
        "Guilherme Loula Teixeira",
        "Guilherme P. N. Ferreira",
        "Leandro Moises Vaz",
        "Murilo Sabino F. De Melo",
        "Taissa Almeida Souza De Jesus",
        "Victor Hugo Luz Rodrigues Barbosa",
    ]

    def desenhar(self, tela):
        super().desenhar(tela)
        caixa = pygame.Rect(120, 100, 720, 470)
        painel(tela, caixa)
        cx = caixa.centerx
        texto(tela, "Correio Noturno", 40, (cx, caixa.top + 34), config.COR_DESTAQUE, negrito=True)
        texto(tela, "A3 · Usabilidade, desenvolvimento web, mobile e jogos · USJT", 22,
              (cx, caixa.top + 68), config.COR_TEXTO_APAGADO)
        texto(tela, "Profs. Elzo Brito dos Santos Filho e Patrícia Vitorino", 22, (cx, caixa.top + 92),
              config.COR_TEXTO_APAGADO)
        y = caixa.top + 136
        for i, nome in enumerate(self.INTEGRANTES):
            x = caixa.left + 190 if i % 2 == 0 else caixa.right - 190
            texto(tela, nome, 26, (x, y + (i // 2) * 34))
        y += 3 * 34 + 26
        paragrafo(tela, "Sprites em pixel art, sons e músicas criados pelo grupo com os "
                        "scripts da pasta tools/ (sem assets de terceiros). "
                        "Feito com Python e pygame-ce.",
                  23, cx, y, caixa.width - 80)
        paragrafo(tela, "Uso de IA declarado no README.", 23, cx, y + 80, caixa.width - 80,
                  cor=config.COR_TEXTO_APAGADO)
        texto(tela, "Obrigado por jogar!", 30, (cx, caixa.bottom - 34), config.COR_DESTAQUE)
