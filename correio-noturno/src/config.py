"""Constantes do jogo: tela, cores, dificuldades e fases.

Quase todo ajuste de balanceamento (velocidade, quantidade de inimigos,
metas de entrega) pode ser feito só mexendo neste arquivo.
"""
import os

TITULO = "Correio Noturno"
LARGURA, ALTURA = 960, 640
FPS = 60

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PASTA_IMG = os.path.join(RAIZ, "assets", "img")
PASTA_SONS = os.path.join(RAIZ, "assets", "sons")
PASTA_DADOS = os.path.join(RAIZ, "dados")

# ---------------------------------------------------------------- paleta
COR_FUNDO = (18, 20, 38)
COR_TEXTO = (240, 232, 210)
COR_TEXTO_APAGADO = (150, 150, 175)
COR_DESTAQUE = (255, 200, 90)       # amarelo das janelas acesas
COR_PERIGO = (235, 90, 80)
COR_SUCESSO = (130, 220, 140)
COR_PAINEL = (24, 26, 50)
COR_BORDA = (90, 96, 140)

# ---------------------------------------------------------------- relógio
HORA_INICIO = 0       # meia-noite
HORA_FIM = 6          # o sol nasce às 6h
MINUTOS_NOITE = (HORA_FIM - HORA_INICIO) * 60

# ---------------------------------------------------------------- pombo
POMBO_VELOCIDADE = 260          # pixels por segundo
POMBO_VIDAS = 3
POMBO_VIDAS_MAX = 5
POMBO_CAPACIDADE = 3            # cartas na bolsa
INVENCIVEL_SEG = 1.6            # tempo piscando depois de levar dano
ARRANCADA_SEG = 0.22            # duração da arrancada (espaço)
ARRANCADA_MULT = 2.6
ARRANCADA_RECARGA = 1.4

# ---------------------------------------------------------------- pontos
PONTOS_COLETA = 10
PONTOS_ENTREGA = 100
PONTOS_COMBO = 25               # extra por entrega seguida sem levar dano
PONTOS_POWERUP = 25
PONTOS_POR_MINUTO_SOBRANDO = 10
PONTOS_POR_PENA = 200

# ---------------------------------------------------------------- dificuldades
# segundos_noite: quanto tempo real dura a noite inteira (00h às 06h)
DIFICULDADES = {
    "Fácil":   {"segundos_noite": 330, "inimigos": 0.8, "vidas": 4},
    "Normal":  {"segundos_noite": 250, "inimigos": 1.0, "vidas": 3},
    "Difícil": {"segundos_noite": 200, "inimigos": 1.25, "vidas": 3},
}
ORDEM_DIFICULDADES = ["Fácil", "Normal", "Difícil"]

# ---------------------------------------------------------------- fases
# Cada fase é uma parte da cidade. Os intervalos são em segundos (média).
FASES = [
    {
        "nome": "Bairro das Acácias",
        "tema": "bairro",
        "meta": 8,
        "rolagem": 70,
        "intervalo_carta": 2.6,
        "intervalo_janela": 3.2,
        "intervalo_gato": 4.5,
        "intervalo_fio": 5.5,
        "intervalo_corvo": None,
        "vento": False,
        "nevoa": False,
        "powerups": ["pao", "asa"],
    },
    {
        "nome": "Centro",
        "tema": "centro",
        "meta": 9,
        "rolagem": 85,
        "intervalo_carta": 2.5,
        "intervalo_janela": 3.0,
        "intervalo_gato": 4.2,
        "intervalo_fio": 4.8,
        "intervalo_corvo": 6.0,
        "vento": False,
        "nevoa": False,
        "powerups": ["pao", "asa", "lanterna"],
    },
    {
        "nome": "Porto",
        "tema": "porto",
        "meta": 10,
        "rolagem": 95,
        "intervalo_carta": 2.4,
        "intervalo_janela": 2.9,
        "intervalo_gato": 5.0,
        "intervalo_fio": 4.5,
        "intervalo_corvo": 5.0,
        "vento": True,
        "nevoa": True,
        "powerups": ["lanterna", "pao", "asa"],
    },
    {
        "nome": "Torre do Relógio",
        "tema": "torre",
        "meta": 8,
        "rolagem": 100,
        "intervalo_carta": 2.3,
        "intervalo_janela": 2.8,
        "intervalo_gato": 3.8,
        "intervalo_fio": 4.2,
        "intervalo_corvo": 4.0,
        "vento": True,
        "nevoa": False,
        "powerups": ["pao", "asa", "lanterna"],
    },
]

# duração dos power-ups (segundos)
DURACAO_PAO = 6.0
DURACAO_LANTERNA = 12.0
INTERVALO_POWERUP = 13.0

# ---------------------------------------------------------------- teclas
# (os nomes aparecem na tela "Como jogar" e na pausa)
CONTROLES = [
    ("Setas / W A S D", "Voar"),
    ("Espaço", "Arrancada (desvia rápido)"),
    ("P ou Esc", "Pausar"),
    ("M", "Ligar/desligar som"),
    ("F11", "Tela cheia"),
    ("Enter", "Confirmar / pular texto"),
]

# ---------------------------------------------------------------- personagens
# velocidade e recarga são multiplicadores/valores sobre o Bico.
# vidas: penas a mais (ou a menos) em relação à dificuldade escolhida.
# vento / nevoa: quanto o pombo sente o vento e quanto a neblina atrapalha (1 = normal).
# libera: número da fase que precisa ser concluída, ou "vitoria".
PERSONAGENS = [
    {"id": "bico", "nome": "Bico", "titulo": "O veterano",
     "descricao": "Equilibrado. Conhece a rota de olhos fechados.",
     "especial": "Sem ponto fraco",
     "velocidade": 1.0, "vidas": 0, "capacidade": 3, "recarga": 1.4,
     "vento": 1.0, "nevoa": 1.0, "escala": 1.0, "libera": None},
    {"id": "pipoca", "nome": "Pipoca", "titulo": "A aprendiz",
     "descricao": "Rápida e afobada. A arrancada recarrega quase duas vezes mais rápido.",
     "especial": "Uma pena a menos",
     "velocidade": 1.18, "vidas": -1, "capacidade": 3, "recarga": 0.8,
     "vento": 1.0, "nevoa": 1.0, "escala": 0.9, "libera": 1},
    {"id": "tiao", "nome": "Tião", "titulo": "O grandalhão do centro",
     "descricao": "Lento, mas leva 4 cartas na bolsa e aguenta uma pena a mais.",
     "especial": "Mais lento e maior",
     "velocidade": 0.85, "vidas": 1, "capacidade": 4, "recarga": 1.6,
     "vento": 0.8, "nevoa": 1.0, "escala": 1.15, "libera": 2},
    {"id": "neblina", "nome": "Neblina", "titulo": "A pomba do porto",
     "descricao": "Quase não sente o vento e enxerga através da neblina.",
     "especial": "Bolsa só para 2 cartas",
     "velocidade": 1.0, "vidas": 0, "capacidade": 2, "recarga": 1.4,
     "vento": 0.35, "nevoa": 0.2, "escala": 1.0, "libera": 3},
    {"id": "dourado", "nome": "Dourado", "titulo": "O pombo da lenda",
     "descricao": "Ninguém sabe de onde veio. Um pouco melhor em tudo.",
     "especial": "Secreto",
     "velocidade": 1.12, "vidas": 1, "capacidade": 4, "recarga": 1.0,
     "vento": 0.6, "nevoa": 0.6, "escala": 1.0, "libera": "vitoria"},
]
PERSONAGENS_POR_ID = {p["id"]: p for p in PERSONAGENS}


def dica_liberar(personagem):
    if personagem["libera"] == "vitoria":
        return "Entregue todas as cartas e vença o jogo"
    n = personagem["libera"]
    return f"Conclua a fase {n} ({FASES[n - 1]['nome']})"
