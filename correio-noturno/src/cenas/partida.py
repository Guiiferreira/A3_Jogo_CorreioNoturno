"""A partida: fases, relógio da noite, inimigos, colisões, pausa e finais.

Estados internos da partida:
    "interludio"  -> tela entre fases (hora + fala do Bico). Relógio parado.
    "jogando"     -> o jogo em si.
    "pausado"     -> menu de pausa por cima do jogo.
    "concluida"   -> fase acabou, mensagem por 1,8 s antes do próximo interlúdio.
    "liberado"    -> concluir a fase liberou um pombo novo: tela de apresentação.
    "terminando"  -> vitória ou derrota, a tela escurece/clareia antes do final.
"""
import math
import random

import pygame

from .. import config, dados, historia, hud
from ..cenario import Cenario, Ceu
from ..efeitos import Particulas, TextoFlutuante, Tremor, Vento, Nevoa
from ..entidades import (Pombo, Carta, Janela, Gato, Fio, Corvo, PowerUp, Torre,
                         distancia)
from ..recursos import imagem
from ..ui import Menu, painel, paragrafo, texto, escurecer
from .base import Cena


def iniciar_jogo(jogo, pular_intro=False):
    """Mostra a introdução e começa a partida com o pombo escolhido."""
    dificuldade = jogo.opcoes["dificuldade"]
    pombo = jogo.opcoes.get("personagem", "bico")
    if pombo not in dados.carregar_liberados():
        pombo = "bico"

    def comecar():
        jogo.trocar_cena(Partida(jogo, dificuldade, pombo))

    if pular_intro:
        comecar()
    else:
        from .narrativa import Narrativa
        jogo.trocar_cena(Narrativa(jogo, historia.intro(pombo), comecar, progresso_ceu=0.0))


class Partida(Cena):
    def __init__(self, jogo, dificuldade, personagem_id="bico"):
        super().__init__(jogo)
        self.dificuldade = dificuldade
        self.dif = config.DIFICULDADES[dificuldade]
        self.mult = self.dif["inimigos"]
        self.personagem = config.PERSONAGENS_POR_ID[personagem_id]
        vidas = max(1, self.dif["vidas"] + self.personagem["vidas"])
        self.pombo = Pombo(self.personagem, vidas)
        self.novo_pombo = None          # pombo liberado nesta fase (se houver)
        self.dourado_liberado = False
        self.minutos = 0.0
        self.pontos = 0
        self.combo = 0
        self.entregas_total = 0
        self.ceu = Ceu()
        self.particulas = Particulas()
        self.textos = TextoFlutuante()
        self.tremor = Tremor()
        self.mundo = pygame.Surface((config.LARGURA, config.ALTURA))
        self.ultimo_tique = -1
        self.aviso_bolsa = 0.0
        self.resultado = None
        self.menu_pausa = Menu(["Continuar", "Reiniciar", "Menu principal"], jogo.audio,
                               tamanho=40, espaco=54)
        self.indice_fase = -1
        self.proxima_fase()

    # ================================================================ fases
    @property
    def fase(self):
        return config.FASES[self.indice_fase]

    def proxima_fase(self):
        self.indice_fase += 1
        f = self.fase
        self.cenario = Cenario(f["tema"], semente=self.indice_fase * 17 + 3)
        self.cartas, self.janelas, self.gatos = [], [], []
        self.fios, self.corvos, self.powerups = [], [], []
        self.torre = None
        self.indo_para_torre = False
        self.entregas_fase = 0
        self.vento = Vento(f["vento"], self.mult)
        self.nevoa = Nevoa(f["nevoa"])
        self.tempo_fase = 0.0
        # cronômetros de surgimento (começam meio adiantados)
        self.timers = {
            "carta": 0.3, "janela": 1.5, "gato": 3.0, "fio": 4.0,
            "corvo": 5.0, "powerup": config.INTERVALO_POWERUP * 0.6,
        }
        # já começa com algumas cartas e uma janela na tela
        for y in (140, 300):
            self._nova_carta(y)
        self._nova_janela(60)
        self.estado = "interludio"
        self.tempo_estado = 0.0
        self.jogo.audio.tocar("sino", 0.7)
        self.jogo.audio.musica("noite" if self.indice_fase < 2 else "madrugada")

    # ================================================================ surgimento
    def _intervalo(self, chave):
        base = self.fase.get("intervalo_" + chave)
        if base is None:
            return None
        if chave in ("gato", "fio", "corvo"):
            base /= self.mult
            # fica um pouco mais difícil conforme a fase avança
            base *= 1 - 0.25 * min(1, self.entregas_fase / self.fase["meta"])
        return base * random.uniform(0.75, 1.25)

    def _nova_carta(self, y=-30):
        x = self.cenario.x_em_telhado(random)
        self.cartas.append(Carta(x, self.cenario.y_em_telhado(y)))

    def _nova_janela(self, y=-40):
        for _ in range(10):  # tenta não colar em outra janela
            x = self.cenario.x_em_telhado(random, margem=40)
            yy = self.cenario.y_em_telhado(y, margem=30)
            if all(distancia(x, yy, j.x, j.y) > 110 for j in self.janelas):
                self.janelas.append(Janela(x, yy))
                return

    def _novo_fio(self):
        y = self.cenario.y_de_rua(-20)
        largura = random.randint(200, 440)
        x1 = random.choice([random.randint(-20, 120), random.randint(200, config.LARGURA - largura)])
        x2 = min(config.LARGURA + 20, x1 + largura)
        intermitente = self.indice_fase >= 1 and random.random() < 0.55
        self.fios.append(Fio(x1, x2, y, intermitente))

    def _surgir(self, dt):
        for chave in self.timers:
            self.timers[chave] -= dt
        p = self.pombo
        sem_cartas_visiveis = not self.cartas and p.cartas == 0
        if not self.indo_para_torre:
            if self.timers["carta"] <= 0 or (sem_cartas_visiveis and self.timers["carta"] < 1.2):
                if len(self.cartas) < 5:
                    self._nova_carta()
                self.timers["carta"] = self._intervalo("carta")
            if self.timers["janela"] <= 0:
                if sum(j.acesa for j in self.janelas) < 3:
                    self._nova_janela()
                self.timers["janela"] = self._intervalo("janela")
        if self.timers["gato"] <= 0:
            x = self.cenario.x_em_telhado(random)
            self.gatos.append(Gato(x, self.cenario.y_em_telhado(-40), self.mult))
            self.timers["gato"] = self._intervalo("gato")
        if self.timers["fio"] <= 0:
            self._novo_fio()
            self.timers["fio"] = self._intervalo("fio")
        intervalo_corvo = self._intervalo("corvo")
        if intervalo_corvo is not None and self.timers["corvo"] <= 0:
            limite = 3 if self.indice_fase == 3 else 2
            if sum(not c.fugindo for c in self.corvos) < limite:
                lado = random.choice(("cima", "esq", "dir"))
                if lado == "cima":
                    x, y = random.randint(100, config.LARGURA - 100), -40
                else:
                    x = -40 if lado == "esq" else config.LARGURA + 40
                    y = random.randint(80, 300)
                self.corvos.append(Corvo(x, y, self.mult))
                self.jogo.audio.tocar("corvo", 0.6)
            self.timers["corvo"] = intervalo_corvo
        if self.timers["powerup"] <= 0:
            opcoes = list(self.fase["powerups"])
            if p.vidas >= config.POMBO_VIDAS_MAX:
                opcoes = [o for o in opcoes if o != "asa"]
            if p.vidas == 1 and "asa" in opcoes:
                opcoes += ["asa"]          # com 1 pena, a asa aparece mais
            x = self.cenario.x_em_telhado(random)
            self.powerups.append(PowerUp(x, -30, random.choice(opcoes)))
            self.timers["powerup"] = config.INTERVALO_POWERUP * random.uniform(0.8, 1.2)

    # ================================================================ eventos
    def evento(self, e):
        if self.estado == "pausado":
            r = self.menu_pausa.tratar(e)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_p):
                self._despausar()
            elif r and r[0] == "escolher":
                escolha = self.menu_pausa.rotulo(r[1])
                if escolha == "Continuar":
                    self._despausar()
                elif escolha == "Reiniciar":
                    iniciar_jogo(self.jogo, pular_intro=True)
                else:
                    from .menu import MenuPrincipal
                    self.jogo.trocar_cena(MenuPrincipal(self.jogo))
            return

        if e.type == pygame.KEYDOWN:
            if self.estado == "interludio" and self.tempo_estado > 0.4:
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.estado = "jogando"
                    self.jogo.audio.tocar("menu_ok")
                    return
            if self.estado == "liberado":
                if self.tempo_estado > 0.8:
                    r = self.menu_liberado.tratar(e)
                    if r and r[0] == "escolher":
                        if r[1] == 1:
                            self._trocar_pombo(self.novo_pombo)
                        self.novo_pombo = None
                        self.proxima_fase()
                return
            if e.key in (pygame.K_ESCAPE, pygame.K_p) and self.estado in ("jogando", "interludio"):
                self._pausar()
            elif e.key == pygame.K_SPACE and self.estado == "jogando":
                if self.pombo.comecar_arrancada():
                    self.jogo.audio.tocar("asa")
        elif e.type == pygame.WINDOWFOCUSLOST and self.estado == "jogando":
            self._pausar()   # pausa sozinho se o jogador trocar de janela

    def _pausar(self):
        self.estado_antes_pausa = self.estado
        self.estado = "pausado"
        self.menu_pausa.indice = 0
        self.jogo.audio.tocar("pausa")
        if self.jogo.audio.ativo:
            pygame.mixer.music.pause()

    def _despausar(self):
        self.estado = self.estado_antes_pausa
        if self.jogo.audio.ativo:
            pygame.mixer.music.unpause()

    # ================================================================ atualização
    def atualizar(self, dt):
        super().atualizar(dt)
        self.tempo_estado += dt
        if self.estado == "pausado":
            self.menu_pausa.atualizar(dt)
            return
        if self.estado in ("interludio", "liberado"):
            if self.estado == "liberado":
                self.menu_liberado.atualizar(dt)
            self.cenario.atualizar(dt, self.fase["rolagem"] * 0.3)
            return
        if self.estado == "terminando":
            self._atualizar_mundo(dt, controles=False)
            if self.tempo_estado > 2.6:
                self._ir_para_final()
            return
        if self.estado == "concluida":
            self._atualizar_mundo(dt, controles=True, surgir=False)
            if self.tempo_estado > 1.8:
                if self.novo_pombo:
                    self.estado, self.tempo_estado = "liberado", 0.0
                    novo = config.PERSONAGENS_POR_ID[self.novo_pombo]
                    self.menu_liberado = Menu(
                        [f"Seguir com {self.personagem['nome']}", f"Voar com {novo['nome']}"],
                        self.jogo.audio, tamanho=34, espaco=44)
                    self.jogo.audio.tocar("vitoria", 0.7)
                else:
                    self.proxima_fase()
            return
        self._atualizar_mundo(dt, controles=True)
        self.tempo_fase += dt
        # relógio da noite
        self.minutos += config.MINUTOS_NOITE / self.dif["segundos_noite"] * dt
        if self.minutos >= config.MINUTOS_NOITE - 30:
            minuto_inteiro = int(self.minutos)
            if minuto_inteiro % 5 == 0 and minuto_inteiro != self.ultimo_tique:
                self.ultimo_tique = minuto_inteiro
                self.jogo.audio.tocar("tique")
        if self.minutos >= config.MINUTOS_NOITE:
            self.minutos = config.MINUTOS_NOITE
            self._terminar("amanheceu")

    def _direcao(self):
        k = pygame.key.get_pressed()
        dx = (k[pygame.K_RIGHT] or k[pygame.K_d]) - (k[pygame.K_LEFT] or k[pygame.K_a])
        dy = (k[pygame.K_DOWN] or k[pygame.K_s]) - (k[pygame.K_UP] or k[pygame.K_w])
        return dx, dy

    def _atualizar_mundo(self, dt, controles=True, surgir=True):
        rolagem = self.fase["rolagem"]
        audio = self.jogo.audio
        self.cenario.atualizar(dt, rolagem)
        self.vento.atualizar(dt, audio)
        self.nevoa.atualizar(dt, rolagem)
        direcao = self._direcao() if controles else (0, -0.4)
        vento = self.vento.forca() * self.personagem["vento"] if controles else 0
        self.pombo.atualizar(dt, direcao, vento)
        if surgir and self.estado == "jogando":
            self._surgir(dt)

        for c in self.cartas + self.janelas + self.fios + self.powerups:
            c.atualizar(dt, rolagem)
        for g in self.gatos:
            g.atualizar(dt, rolagem, self.pombo, audio)
        for c in self.corvos:
            c.atualizar(dt, rolagem, self.pombo)
        if self.torre:
            self.torre.atualizar(dt, rolagem)

        self.particulas.atualizar(dt, rolagem * 0.5)
        self.textos.atualizar(dt)
        self.tremor.atualizar(dt)
        self.aviso_bolsa = max(0.0, self.aviso_bolsa - dt)

        if controles and self.estado in ("jogando", "concluida"):
            self._colisoes()
        for nome in ("cartas", "janelas", "gatos", "fios", "corvos", "powerups"):
            setattr(self, nome, [e for e in getattr(self, nome) if e.vivo])

    # ================================================================ colisões
    def _colisoes(self):
        p, audio = self.pombo, self.jogo.audio

        for c in self.cartas:
            if c.pegavel == 0 and p.encosta(c):
                if p.cartas < p.capacidade:
                    c.vivo = False
                    p.cartas += 1
                    self.pontos += config.PONTOS_COLETA
                    audio.tocar("coleta")
                    self.particulas.brilho(c.x, c.y, (250, 240, 210), 10)
                elif self.aviso_bolsa == 0:
                    self.textos.adicionar("Bolsa cheia!", p.x, p.y - 40, config.COR_PERIGO, 26)
                    self.aviso_bolsa = 1.5

        for j in self.janelas:
            if j.acesa and p.cartas > 0 and p.encosta(j):
                self._entregar(j)

        for pu in self.powerups:
            if p.encosta(pu):
                pu.vivo = False
                self._pegar_powerup(pu)

        if self.torre and self.indo_para_torre:
            jx, jy = self.torre.ponto_entrega()
            if distancia(p.x, p.y, jx, jy) < 46:
                self.particulas.brilho(jx, jy, config.COR_DESTAQUE, 40)
                self._terminar("vitoria")
                return

        # ---------------- perigos (não machucam durante arrancada ou piscando)
        protegido = p.invencivel > 0 or p.arrancada > 0 or self.estado == "concluida"
        for c in self.corvos:
            if not c.fugindo and p.encosta(c, folga=4) and not protegido:
                if p.cartas > 0:            # corvo rouba uma carta e vai embora
                    p.cartas -= 1
                    c.fugir(com_carta=True)
                    self.combo = 0
                    p.invencivel = 0.8
                    audio.tocar("corvo")
                    self.textos.adicionar("Roubaram uma carta!", p.x, p.y - 40,
                                          config.COR_PERIGO, 26)
                    self.tremor.iniciar(5, 0.2)
                else:
                    c.fugir()
                    self._dano(p.x, p.y)
                return
        if protegido:
            return
        for g in self.gatos:
            if g.perigoso() and p.encosta(g, folga=6):
                self._dano(g.x, g.y)
                return
        for f in self.fios:
            if f.toca(p):
                audio.tocar("choque")
                self._dano(p.x, p.y)
                return

    def _entregar(self, janela):
        p = self.pombo
        janela.acesa = False
        p.cartas -= 1
        self.combo += 1
        ganho = config.PONTOS_ENTREGA + config.PONTOS_COMBO * (self.combo - 1)
        self.pontos += ganho
        self.entregas_fase += 1
        self.entregas_total += 1
        self.jogo.audio.tocar("entrega")
        self.particulas.brilho(janela.x, janela.y, config.COR_DESTAQUE, 24)
        self.textos.adicionar(f"+{ganho}", janela.x, janela.y - 50)
        if self.entregas_fase >= self.fase["meta"] and not self.indo_para_torre:
            if self.indice_fase == len(config.FASES) - 1:
                # última fase: agora falta só a carta da Dona Celeste
                self.indo_para_torre = True
                self.torre = Torre()
                self.textos.adicionar("Agora, a carta dourada!", config.LARGURA // 2, 200,
                                      config.COR_DESTAQUE, 40)
                self.jogo.audio.tocar("sino", 0.6)
            else:
                self.estado = "concluida"
                self.tempo_estado = 0.0
                self.jogo.audio.tocar("powerup")
                # concluir a fase libera um pombo novo (só na primeira vez)
                for pers in config.PERSONAGENS:
                    if pers["libera"] == self.indice_fase + 1 and dados.liberar(pers["id"]):
                        self.novo_pombo = pers["id"]

    def _trocar_pombo(self, personagem_id):
        """Troca de pombo entre as fases, sem perder a noite.

        As penas acompanham a diferença entre os pombos (o Tião chega com uma a
        mais, a Pipoca com uma a menos), mas nunca ficam abaixo de 1.
        """
        antigo, novo = self.personagem, config.PERSONAGENS_POR_ID[personagem_id]
        velho = self.pombo
        vidas = velho.vidas + novo["vidas"] - antigo["vidas"]
        vidas = max(1, min(config.POMBO_VIDAS_MAX, vidas))
        p = Pombo(novo, vidas)
        p.vidas_iniciais = max(1, self.dif["vidas"] + novo["vidas"])
        p.x, p.y = velho.x, velho.y
        p.cartas = min(velho.cartas, p.capacidade)
        p.carta_especial = velho.carta_especial
        self.pombo, self.personagem = p, novo
        # a próxima partida já começa com ele selecionado
        self.jogo.opcoes["personagem"] = personagem_id
        self.jogo.salvar_opcoes()
        self.jogo.audio.tocar("asa")

    def _pegar_powerup(self, pu):
        p = self.pombo
        self.pontos += config.PONTOS_POWERUP
        self.jogo.audio.tocar("powerup")
        self.particulas.brilho(pu.x, pu.y, (255, 240, 170), 18)
        if pu.tipo == "pao":
            p.pao = config.DURACAO_PAO
            msg = "Mais rápido!"
        elif pu.tipo == "lanterna":
            p.lanterna = config.DURACAO_LANTERNA
            msg = "Lanterna!"
        else:
            p.vidas = min(config.POMBO_VIDAS_MAX, p.vidas + 1)
            msg = "+1 pena"
        self.textos.adicionar(msg, pu.x, pu.y - 30, config.COR_SUCESSO, 28)

    def _dano(self, x, y):
        p = self.pombo
        p.vidas -= 1
        p.invencivel = config.INVENCIVEL_SEG
        self.combo = 0
        self.jogo.audio.tocar("dano")
        self.tremor.iniciar(10, 0.35)
        self.particulas.penas(p.x, p.y, 10)
        # derruba uma carta, que dá para pegar de volta
        if p.cartas > 0:
            p.cartas -= 1
            ang = math.atan2(p.y - y, p.x - x) + random.uniform(-0.6, 0.6)
            self.cartas.append(Carta(p.x, p.y, math.cos(ang) * 260, math.sin(ang) * 260 - 60))
        if p.vidas <= 0:
            self._terminar("sem_penas")

    # ================================================================ fim
    def _terminar(self, resultado):
        if self.estado == "terminando":
            return
        self.resultado = resultado
        self.estado = "terminando"
        self.tempo_estado = 0.0
        audio = self.jogo.audio
        audio.parar_musica(800)
        if resultado == "vitoria":
            sobra = config.MINUTOS_NOITE - self.minutos
            self.bonus_tempo = int(sobra) * config.PONTOS_POR_MINUTO_SOBRANDO
            self.bonus_penas = self.pombo.vidas * config.PONTOS_POR_PENA
            self.pontos += self.bonus_tempo + self.bonus_penas
            audio.tocar("vitoria")
            self.dourado_liberado = dados.liberar("dourado")
        else:
            self.bonus_tempo = self.bonus_penas = 0
            audio.tocar("galo" if resultado == "amanheceu" else "derrota")

    def _ir_para_final(self):
        from .narrativa import Narrativa
        from .fim import TelaFim
        pid, nome = self.personagem["id"], self.personagem["nome"]
        if self.resultado == "vitoria":
            textos = historia.final_vitoria(pid)
        elif self.resultado == "amanheceu":
            textos = historia.final_amanheceu(pid, nome)
        else:
            textos = historia.final_sem_penas(pid, nome)
        resumo = {
            "resultado": self.resultado,
            "pontos": self.pontos,
            "entregas": self.entregas_total,
            "fase": self.indice_fase + 1,
            "hora": hud.hora_texto(self.minutos),
            "bonus_tempo": self.bonus_tempo,
            "bonus_penas": self.bonus_penas,
            "dificuldade": self.dificuldade,
            "pombo": pid,
        }
        jogo = self.jogo
        if self.resultado == "vitoria":
            ceu, musica = 1.0, "amanhecer"
        elif self.resultado == "amanheceu":
            ceu, musica = 0.9, "menu"
        else:
            ceu, musica = self.minutos / config.MINUTOS_NOITE, "menu"
        def ir_para_fim():
            jogo.trocar_cena(TelaFim(jogo, resumo))

        depois = ir_para_fim
        if self.dourado_liberado:
            # vencer pela primeira vez revela o pombo secreto
            def depois():
                jogo.trocar_cena(Narrativa(jogo, [historia.ENCONTROS["dourado"]], ir_para_fim,
                                           titulo="Novo pombo liberado!", musica=None))
        jogo.trocar_cena(Narrativa(jogo, textos, depois, progresso_ceu=ceu, musica=musica))

    # ================================================================ desenho
    def _progresso(self):
        return self.minutos / config.MINUTOS_NOITE

    def desenhar(self, tela):
        m = self.mundo
        progresso = self._progresso()
        self.cenario.desenhar(m)
        self.ceu.desenhar(m, progresso)
        escuro = Ceu.escuridao(progresso)
        self.cenario.desenhar_luzes(m, escuro)
        for j in self.janelas:
            j.desenhar_brilho(m)
        for grupo in (self.janelas, self.fios, self.cartas, self.powerups, self.gatos):
            for e in grupo:
                e.desenhar(m)
        if self.torre:
            self.torre.desenhar(m)
        for c in self.corvos:
            c.desenhar(m)
        self.pombo.desenhar(m)
        self.particulas.desenhar(m)
        nevoa = min(self.personagem["nevoa"], 0.25 if self.pombo.lanterna > 0 else 1.0)
        self.nevoa.desenhar(m, nevoa)
        self.vento.desenhar(m, self.t)
        if self.pombo.lanterna > 0 or self.indo_para_torre:
            self._seta_destino(m)
        self.textos.desenhar(m)

        tela.fill((0, 0, 0))
        tela.blit(m, self.tremor.deslocamento())
        hud.desenhar(tela, self)
        self._dicas(tela)

        if self.estado == "interludio":
            self._desenhar_interludio(tela)
        elif self.estado == "pausado":
            self._desenhar_pausa(tela)
        elif self.estado == "concluida":
            texto(tela, "Fase concluída!", 64, (config.LARGURA // 2, config.ALTURA // 2 - 20),
                  config.COR_SUCESSO, negrito=True)
            texto(tela, f"{self.entregas_fase} cartas entregues no {self.fase['nome']}", 28,
                  (config.LARGURA // 2, config.ALTURA // 2 + 30))
        elif self.estado == "terminando":
            self._desenhar_transicao_final(tela)
        elif self.estado == "liberado":
            self._desenhar_liberado(tela)

    def _seta_destino(self, tela):
        """Seta em volta do pombo apontando a janela acesa mais perto (ou a torre)."""
        p = self.pombo
        if self.indo_para_torre and self.torre:
            alvo = self.torre.ponto_entrega()
        else:
            acesas = [j for j in self.janelas if j.acesa]
            if not acesas or p.cartas == 0:
                acesas = [c for c in self.cartas] if p.cartas == 0 else acesas
            if not acesas:
                return
            mais_perto = min(acesas, key=lambda j: distancia(p.x, p.y, j.x, j.y))
            alvo = (mais_perto.x, mais_perto.y)
        if distancia(p.x, p.y, *alvo) < 60:
            return
        ang = math.atan2(alvo[1] - p.y, alvo[0] - p.x)
        cx, cy = p.x + math.cos(ang) * 46, p.y + math.sin(ang) * 46
        pontos = [(cx + math.cos(ang) * 12, cy + math.sin(ang) * 12),
                  (cx + math.cos(ang + 2.4) * 10, cy + math.sin(ang + 2.4) * 10),
                  (cx + math.cos(ang - 2.4) * 10, cy + math.sin(ang - 2.4) * 10)]
        pygame.draw.polygon(tela, (20, 20, 30), [(x + 2, y + 2) for x, y in pontos])
        pygame.draw.polygon(tela, config.COR_DESTAQUE, pontos)

    def _dicas(self, tela):
        """Tutorial curto no começo da primeira fase."""
        if self.indice_fase != 0 or self.estado != "jogando" or self.tempo_fase > 15:
            return
        i = min(len(historia.DICAS_FASE_1) - 1, int(self.tempo_fase / 5))
        caixa = pygame.Rect(0, 0, 620, 44)
        caixa.midbottom = (config.LARGURA // 2, config.ALTURA - 16)
        painel(tela, caixa, alpha=200)
        texto(tela, historia.DICAS_FASE_1[i], 26, caixa.center)

    def _desenhar_interludio(self, tela):
        escurecer(tela, 140)
        f = self.fase
        cx = config.LARGURA // 2
        texto(tela, hud.hora_texto(self.minutos), 80, (cx, 120), config.COR_DESTAQUE, negrito=True)
        texto(tela, f"Fase {self.indice_fase + 1} de {len(config.FASES)}", 28, (cx, 175),
              config.COR_TEXTO_APAGADO)
        texto(tela, f["nome"], 52, (cx, 220), negrito=True)
        caixa = pygame.Rect(130, 270, config.LARGURA - 260, 170)
        painel(tela, caixa)
        retrato = imagem("retrato_bico")
        tela.blit(retrato, retrato.get_rect(midleft=(caixa.left + 24, caixa.centery)))
        paragrafo(tela, '"' + historia.FALAS_FASE[self.indice_fase] + '"', 30,
                  caixa.left + 140, caixa.top + 36, caixa.width - 170, ancora_x="left")
        meta = f"Meta: entregar {f['meta']} cartas"
        if self.indice_fase == len(config.FASES) - 1:
            meta += " e levar a carta dourada à torre"
        texto(tela, meta, 30, (cx, 480), config.COR_SUCESSO)
        novidades = []
        if f["intervalo_corvo"] and self.indice_fase == 1:
            novidades.append("Novo: corvos e fios que ligam e desligam")
        if f["vento"] and self.indice_fase == 2:
            novidades.append("Novo: rajadas de vento e neblina")
        if novidades:
            texto(tela, novidades[0], 24, (cx, 515), config.COR_DESTAQUE)
        if self.tempo_estado > 0.4 and int(self.t * 2) % 2 == 0:
            texto(tela, "Enter para voar", 30, (cx, 575))

    def _desenhar_liberado(self, tela):
        """Apresenta o pombo que acabou de ser liberado (quem o Bico conheceu na rota)."""
        escurecer(tela, 215)
        novo = config.PERSONAGENS_POR_ID[self.novo_pombo]
        cx = config.LARGURA // 2
        pulo = abs(math.sin(self.t * 3)) * 6
        texto(tela, "Novo pombo liberado!", 60, (cx, 80), config.COR_DESTAQUE, negrito=True)
        caixa = pygame.Rect(110, 130, config.LARGURA - 220, 300)
        painel(tela, caixa)
        retrato = pygame.transform.scale_by(imagem("retrato_" + novo["id"]), 1.5)
        tela.blit(retrato, retrato.get_rect(center=(caixa.left + 110, caixa.top + 110 - pulo)))
        texto(tela, novo["nome"], 40, (caixa.left + 110, caixa.top + 210), config.COR_DESTAQUE,
              negrito=True)
        texto(tela, novo["titulo"], 22, (caixa.left + 110, caixa.top + 240),
              config.COR_TEXTO_APAGADO)
        fala = historia.ENCONTROS[novo["id"]]["fala"]
        y = paragrafo(tela, '"' + fala + '"', 30, caixa.left + 220, caixa.top + 40,
                      caixa.width - 250, ancora_x="left")
        paragrafo(tela, novo["descricao"], 24, caixa.left + 220, y + 20, caixa.width - 250,
                  cor=config.COR_SUCESSO, ancora_x="left")
        texto(tela, "Quer trocar de pombo agora? As penas e as cartas da bolsa seguem com você.",
              22, (cx, caixa.bottom + 26), config.COR_TEXTO_APAGADO)
        if self.tempo_estado > 0.8:
            self.menu_liberado.desenhar(tela, cx, caixa.bottom + 74)

    def _desenhar_pausa(self, tela):
        escurecer(tela, 160)
        cx = config.LARGURA // 2
        texto(tela, "Pausado", 70, (cx, 110), config.COR_DESTAQUE, negrito=True)
        caixa = pygame.Rect(cx - 200, 170, 400, 200)
        painel(tela, caixa)
        self.menu_pausa.desenhar(tela, cx, caixa.top + 46)
        ajuda = pygame.Rect(cx - 300, 400, 600, 190)
        painel(tela, ajuda, alpha=180)
        y = ajuda.top + 26
        for tecla, acao in config.CONTROLES[:5]:
            texto(tela, tecla, 24, (ajuda.left + 120, y), config.COR_DESTAQUE, ancora="midleft")
            texto(tela, acao, 24, (ajuda.left + 300, y), ancora="midleft")
            y += 34

    def _desenhar_transicao_final(self, tela):
        prog = min(1, self.tempo_estado / 2.6)
        if self.resultado == "vitoria":
            cor, msg = (255, 220, 160), "Carta entregue!"
        elif self.resultado == "amanheceu":
            cor, msg = (255, 170, 90), "Amanheceu..."
        else:
            cor, msg = (10, 10, 20), "Sem forças..."
        veu = pygame.Surface((config.LARGURA, config.ALTURA))
        veu.fill(cor)
        veu.set_alpha(int(220 * prog))
        tela.blit(veu, (0, 0))
        cor_txt = (60, 30, 20) if self.resultado != "sem_penas" else config.COR_TEXTO
        texto(tela, msg, 72, (config.LARGURA // 2, config.ALTURA // 2), cor_txt,
              negrito=True, sombra=False, alpha=int(255 * prog))
