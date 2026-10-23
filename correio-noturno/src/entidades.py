"""Personagens e objetos do jogo.

Coordenadas são da tela (x, y = centro). Tudo, menos o pombo, desce junto
com a cidade (rolagem), então cada update recebe a velocidade de rolagem.
"""
import math
import random

import pygame

from . import config
from .recursos import imagem
from .ui import texto


def distancia(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def dist_ponto_segmento(px, py, ax, ay, bx, by):
    """Menor distância entre o ponto P e o segmento AB (usado nos fios)."""
    abx, aby = bx - ax, by - ay
    comp2 = abx * abx + aby * aby or 1
    t = max(0, min(1, ((px - ax) * abx + (py - ay) * aby) / comp2))
    return distancia(px, py, ax + abx * t, ay + aby * t)


def sombra(tela, x, y, largura, altura=None, alpha=90):
    altura = altura or largura // 2
    s = pygame.Surface((largura, altura), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alpha), s.get_rect())
    tela.blit(s, s.get_rect(center=(int(x), int(y))))


class Entidade:
    raio = 16          # raio usado na colisão (círculo)

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vivo = True
        self.t = random.uniform(0, 10)     # relógio interno p/ animações

    def atualizar(self, dt, rolagem):
        self.t += dt
        self.y += rolagem * dt
        if self.y > config.ALTURA + 80:
            self.vivo = False

    def encosta(self, outro, folga=0):
        return distancia(self.x, self.y, outro.x, outro.y) < self.raio + outro.raio - folga


# =================================================================== pombo
class Pombo(Entidade):
    raio = 14

    def __init__(self, personagem, vidas):
        super().__init__(config.LARGURA // 2, config.ALTURA - 120)
        # atributos do personagem escolhido (ver config.PERSONAGENS)
        self.personagem = personagem
        self.velocidade = config.POMBO_VELOCIDADE * personagem["velocidade"]
        self.capacidade = personagem["capacidade"]
        self.tempo_recarga = personagem["recarga"]
        self.raio = int(14 * personagem["escala"])
        quadros = [imagem(f"pombo_{personagem['id']}_{i}") for i in range(3)]
        if personagem["escala"] != 1.0:
            quadros = [pygame.transform.scale_by(q, personagem["escala"]) for q in quadros]
        self.quadros = [self._com_contorno(q) for q in quadros]
        self.vidas = vidas
        self.vidas_iniciais = vidas
        self.cartas = 0
        self.carta_especial = True        # a carta da Dona Celeste
        self.vx = self.vy = 0.0
        self.invencivel = 0.0
        self.arrancada = 0.0
        self.recarga = 0.0
        self.pao = 0.0
        self.lanterna = 0.0
        self.rastro = []                  # posições para o efeito de arrancada

    @staticmethod
    def _com_contorno(img):
        """Contorno claro em volta do sprite: o pombo se destaca dos telhados."""
        mascara = pygame.mask.from_surface(img)
        borda = mascara.to_surface(setcolor=(255, 244, 210, 200), unsetcolor=(0, 0, 0, 0))
        nova = pygame.Surface((img.get_width() + 4, img.get_height() + 4), pygame.SRCALPHA)
        for dx, dy in ((0, 2), (4, 2), (2, 0), (2, 4)):
            nova.blit(borda, (dx, dy))
        nova.blit(img, (2, 2))
        return nova

    def comecar_arrancada(self):
        if self.recarga <= 0:
            self.arrancada = config.ARRANCADA_SEG
            self.recarga = self.tempo_recarga
            return True
        return False

    def atualizar(self, dt, direcao, vento=0.0):
        self.t += dt
        dx, dy = direcao
        if dx and dy:                       # diagonal não fica mais rápida
            dx *= 0.7071
            dy *= 0.7071
        vel = self.velocidade * (1.45 if self.pao > 0 else 1.0)
        if self.arrancada > 0:
            vel *= config.ARRANCADA_MULT
            if not (dx or dy):
                dy = -1                     # arrancada parado vai para frente
        # suaviza o movimento (sensação de voo), mas responde rápido
        alvo_x, alvo_y = dx * vel, dy * vel
        k = min(1, dt * 14)
        self.vx += (alvo_x - self.vx) * k
        self.vy += (alvo_y - self.vy) * k
        self.x += (self.vx + vento) * dt
        self.y += self.vy * dt
        self.x = max(24, min(config.LARGURA - 24, self.x))
        self.y = max(70, min(config.ALTURA - 28, self.y))

        for nome in ("invencivel", "arrancada", "recarga", "pao", "lanterna"):
            setattr(self, nome, max(0.0, getattr(self, nome) - dt))
        if self.arrancada > 0:
            self.rastro.append([self.x, self.y, 0.25])
        for r in self.rastro:
            r[2] -= dt
        self.rastro = [r for r in self.rastro if r[2] > 0]

    def quadro(self):
        # bate asa mais rápido quando se move
        rapido = abs(self.vx) + abs(self.vy) > 40
        ciclo = [0, 1, 2, 1]
        i = int(self.t * (14 if rapido else 7)) % 4
        return self.quadros[ciclo[i]]

    def desenhar(self, tela):
        sombra(tela, self.x + 10, self.y + 22, 34, 14)
        img = self.quadro()
        inclinacao = -self.vx / self.velocidade * 14
        img = pygame.transform.rotate(img, inclinacao)
        for x, y, vida in self.rastro:
            fantasma = img.copy()
            fantasma.set_alpha(int(vida / 0.25 * 110))
            tela.blit(fantasma, fantasma.get_rect(center=(int(x), int(y))))
        if self.invencivel > 0 and int(self.t * 16) % 2 == 0:
            return                           # pisca depois de levar dano
        tela.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        if self.pao > 0:                    # anel dourado de velocidade
            pygame.draw.circle(tela, (240, 190, 90), (int(self.x), int(self.y)), 30, 2)


# =================================================================== cartas
class Carta(Entidade):
    raio = 18

    def __init__(self, x, y, vx=0.0, vy=0.0):
        super().__init__(x, y)
        self.img = imagem("carta")
        self.vx, self.vy = vx, vy          # usada quando a carta cai da bolsa
        self.pegavel = 0.6 if (vx or vy) else 0.0

    def atualizar(self, dt, rolagem):
        super().atualizar(dt, rolagem)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.92
        self.vy *= 0.92
        self.pegavel = max(0.0, self.pegavel - dt)

    def desenhar(self, tela):
        flutua = math.sin(self.t * 3) * 3
        sombra(tela, self.x + 6, self.y + 14, 28, 10, 70)
        img = pygame.transform.rotate(self.img, math.sin(self.t * 2) * 10)
        tela.blit(img, img.get_rect(center=(int(self.x), int(self.y + flutua))))


class Janela(Entidade):
    """Claraboia acesa: alguém esperando carta. Depois de entregue, apaga."""
    raio = 22

    def __init__(self, x, y):
        super().__init__(x, y)
        self.acesa = True
        self.envelope = imagem("carta_hud")
        self.brilho = self._fazer_brilho()

    @staticmethod
    def _fazer_brilho():
        s = pygame.Surface((120, 120))
        for r in range(60, 0, -3):
            f = (1 - r / 60) ** 1.5
            pygame.draw.circle(s, (int(170 * f), int(120 * f), int(40 * f)), (60, 60), r)
        return s

    def desenhar_brilho(self, tela):
        """Brilho somado depois do escurecimento da noite (fica bonito)."""
        if self.acesa:
            pulso = 1 + 0.15 * math.sin(self.t * 4)
            img = pygame.transform.smoothscale(self.brilho, (int(120 * pulso), int(120 * pulso)))
            tela.blit(img, img.get_rect(center=(int(self.x), int(self.y))),
                      special_flags=pygame.BLEND_ADD)

    def desenhar(self, tela):
        img = imagem("janela_acesa" if self.acesa else "janela_apagada")
        tela.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        if self.acesa:
            y = self.y - 36 + math.sin(self.t * 5) * 4
            tela.blit(self.envelope, self.envelope.get_rect(center=(int(self.x), int(y))))
        else:  # "visto" de entregue
            pts = [(self.x - 8, self.y - 26), (self.x - 2, self.y - 20), (self.x + 10, self.y - 34)]
            pygame.draw.lines(tela, (20, 30, 20), False, [(a + 1, b + 1) for a, b in pts], 5)
            pygame.draw.lines(tela, config.COR_SUCESSO, False, pts, 4)


# =================================================================== inimigos
class Gato(Entidade):
    """Fica no telhado. Quando o pombo chega perto, avisa (!) e dá um bote."""
    raio = 18
    ALCANCE = 190

    def __init__(self, x, y, mult=1.0):
        super().__init__(x, y)
        self.casa_x, self.casa_dy = x, 0.0   # posição de origem (relativa)
        self.estado = "espreitando"
        self.tempo = 0.0
        self.mult = mult
        self.alvo = (0, 0)
        self.vx = self.vy = 0.0

    def atualizar(self, dt, rolagem, pombo=None, audio=None):
        super().atualizar(dt, rolagem)
        self.tempo += dt
        if self.estado == "espreitando" and pombo is not None:
            if distancia(self.x, self.y, pombo.x, pombo.y) < self.ALCANCE and pombo.y > self.y - 40:
                self.estado, self.tempo = "alerta", 0.0
                self.alvo = (pombo.x, pombo.y)
        elif self.estado == "alerta":
            if pombo is not None:
                self.alvo = (pombo.x, pombo.y)
            if self.tempo > 0.55 / self.mult:
                self.estado, self.tempo = "bote", 0.0
                ang = math.atan2(self.alvo[1] - self.y, self.alvo[0] - self.x)
                v = 560 * self.mult
                self.vx, self.vy = math.cos(ang) * v, math.sin(ang) * v
                if audio:
                    audio.tocar("miado", 0.7)
        elif self.estado == "bote":
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.tempo > 0.32:
                self.estado, self.tempo = "voltando", 0.0
        elif self.estado == "voltando":
            # volta devagar para o telhado de origem
            self.x += (self.casa_x - self.x) * min(1, dt * 2)
            if self.tempo > 1.6:
                self.estado, self.tempo = "espreitando", 0.0

    def perigoso(self):
        return self.estado == "bote"

    def desenhar(self, tela):
        bote = self.estado == "bote"
        img = imagem("gato_1" if bote or self.estado == "alerta" else "gato_0")
        if bote:
            img = pygame.transform.rotozoom(img, 0, 1.2)
        sombra(tela, self.x + 6, self.y + 20, 36, 12)
        tela.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        if self.estado == "alerta":
            texto(tela, "!", 44, (int(self.x), int(self.y - 40)), config.COR_PERIGO, negrito=True)


class Fio(Entidade):
    """Fio elétrico entre dois postes, atravessando a rua.

    intermitente=True: liga e desliga. Desligado (cinza) dá para passar.
    """

    LIGADO, DESLIGADO = 2.2, 1.4

    def __init__(self, x1, x2, y, intermitente=False):
        super().__init__((x1 + x2) / 2, y)
        self.x1, self.x2 = x1, x2
        self.intermitente = intermitente
        self.ligado = True
        self.ciclo = random.uniform(0, self.LIGADO + self.DESLIGADO)
        self.faiscas = []

    def atualizar(self, dt, rolagem):
        super().atualizar(dt, rolagem)
        if self.intermitente:
            self.ciclo = (self.ciclo + dt) % (self.LIGADO + self.DESLIGADO)
            self.ligado = self.ciclo < self.LIGADO
        if self.ligado and random.random() < 0.25:
            self.faiscas.append([random.uniform(self.x1, self.x2), 0.15])
        for f in self.faiscas:
            f[1] -= dt
        self.faiscas = [f for f in self.faiscas if f[1] > 0]

    def toca(self, pombo):
        if not self.ligado:
            return False
        return dist_ponto_segmento(pombo.x, pombo.y, self.x1, self.y, self.x2, self.y) < 10

    def desenhar(self, tela):
        y = int(self.y)
        # sombra do fio
        pygame.draw.line(tela, (10, 10, 18), (self.x1 + 4, y + 8), (self.x2 + 4, y + 8), 2)
        if self.ligado:
            vibra = math.sin(self.t * 40) * 1.5
            pygame.draw.line(tela, (60, 200, 255), (self.x1, y), (self.x2, y + vibra), 4)
            pygame.draw.line(tela, (220, 250, 255), (self.x1, y), (self.x2, y + vibra), 1)
        else:
            pygame.draw.line(tela, (70, 74, 90), (self.x1, y), (self.x2, y), 3)
            # aviso de que vai religar
            resta = self.LIGADO + self.DESLIGADO - self.ciclo
            if resta < 0.5 and int(self.t * 12) % 2 == 0:
                pygame.draw.line(tela, (60, 140, 200), (self.x1, y), (self.x2, y), 2)
        for fx, _ in self.faiscas:
            pygame.draw.circle(tela, (255, 255, 200), (int(fx), y + random.randint(-4, 4)), 2)
        poste = imagem("poste")
        for px in (self.x1, self.x2):
            tela.blit(poste, poste.get_rect(center=(int(px), y)))


class Corvo(Entidade):
    """Persegue o pombo. Se encostar, rouba uma carta (ou machuca, se a bolsa estiver vazia)."""
    raio = 15

    def __init__(self, x, y, mult=1.0):
        super().__init__(x, y)
        self.quadros = [imagem(f"corvo_{i}") for i in range(3)]
        self.mult = mult
        self.vx, self.vy = 0.0, 120.0
        self.vida = 9.0
        self.fugindo = False
        self.com_carta = False

    def fugir(self, com_carta=False):
        self.fugindo = True
        self.com_carta = com_carta

    def atualizar(self, dt, rolagem, pombo=None):
        self.t += dt
        self.vida -= dt
        if self.vida <= 0:
            self.fugindo = True
        if self.fugindo:
            alvo_vx, alvo_vy = (1 if self.x > config.LARGURA / 2 else -1) * 120, -320
        else:
            ang = math.atan2(pombo.y - self.y, pombo.x - self.x)
            v = 165 * self.mult
            alvo_vx, alvo_vy = math.cos(ang) * v, math.sin(ang) * v
        k = min(1, dt * 1.6)          # curva lenta: dá para despistar
        self.vx += (alvo_vx - self.vx) * k
        self.vy += (alvo_vy - self.vy) * k
        self.x += self.vx * dt
        self.y += self.vy * dt
        fora = (self.y < -120 or self.y > config.ALTURA + 120
                or self.x < -120 or self.x > config.LARGURA + 120)
        if fora and (self.fugindo or self.t > 2):
            self.vivo = False

    def desenhar(self, tela):
        sombra(tela, self.x + 12, self.y + 26, 34, 14, 70)
        img = self.quadros[[0, 1, 2, 1][int(self.t * 12) % 4]]
        ang = math.degrees(math.atan2(-self.vy, self.vx)) - 90
        img = pygame.transform.rotate(img, ang)
        tela.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        if self.com_carta:
            c = imagem("carta_hud")
            tela.blit(c, c.get_rect(center=(int(self.x), int(self.y + 18))))


# =================================================================== power-ups
class PowerUp(Entidade):
    raio = 20
    NOMES = {"pao": "Pão", "lanterna": "Lanterna", "asa": "Asa extra"}
    IMAGENS = {"pao": "pao", "lanterna": "lanterna", "asa": "asa_extra"}

    def __init__(self, x, y, tipo):
        super().__init__(x, y)
        self.tipo = tipo

    def desenhar(self, tela):
        img = imagem(self.IMAGENS[self.tipo])
        flutua = math.sin(self.t * 3) * 4
        raio = int(24 + math.sin(self.t * 5) * 3)
        pygame.draw.circle(tela, (255, 230, 150), (int(self.x), int(self.y + flutua)), raio, 2)
        tela.blit(img, img.get_rect(center=(int(self.x), int(self.y + flutua))))


class Torre(Entidade):
    """Destino final: a janela da Dona Celeste no alto da Torre do Relógio."""
    raio = 30

    def __init__(self):
        super().__init__(config.LARGURA // 2, -140)
        self.img = imagem("torre")
        self.parada_em = 230

    def atualizar(self, dt, rolagem):
        self.t += dt
        self.y = min(self.parada_em, self.y + rolagem * dt)

    def ponto_entrega(self):
        """Centro da janela iluminada (parte de baixo da torre)."""
        return self.x, self.y + 60

    def desenhar(self, tela):
        sombra(tela, self.x + 20, self.y + 96, 140, 40, 110)
        r = self.img.get_rect(center=(int(self.x), int(self.y)))
        tela.blit(self.img, r)
        jx, jy = self.ponto_entrega()
        envelope = imagem("carta_especial_hud")
        tela.blit(envelope, envelope.get_rect(center=(int(jx), int(self.y - 112 + math.sin(self.t * 4) * 4))))
