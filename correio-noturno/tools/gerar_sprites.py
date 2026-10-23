"""
Gera os sprites em pixel art do jogo e salva em assets/img/.

Cada sprite é um "mapa" de texto: cada caractere é um pixel e a letra
indica a cor (veja PALETA). O ponto (.) é transparente. Depois o desenho
é ampliado (ESCALA) para ficar com cara de pixel art.

Para mudar um personagem, basta editar o mapa e rodar de novo:
    python tools/gerar_sprites.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

PASTA = os.path.join(os.path.dirname(__file__), "..", "assets", "img")

# Paleta única do jogo (mantém tudo com a mesma cara)
PALETA = {
    "k": (27, 27, 47),      # contorno
    "g": (138, 143, 163),   # cinza do pombo
    "l": (197, 201, 214),   # cinza claro
    "v": (79, 138, 122),    # pescoço verde
    "p": (122, 92, 158),    # pescoço roxo
    "y": (232, 176, 74),    # bico
    "e": (20, 20, 30),      # olho
    "w": (244, 234, 208),   # branco/creme
    "W": (216, 201, 163),   # creme escuro
    "b": (139, 90, 43),     # bolsa
    "B": (101, 63, 28),     # bolsa escura
    "r": (192, 57, 43),     # vermelho (lacre)
    "o": (217, 130, 43),    # gato laranja
    "O": (168, 90, 28),     # gato laranja escuro
    "n": (232, 138, 160),   # nariz rosa
    "E": (240, 220, 60),    # olho arregalado
    "m": (91, 58, 36),      # madeira
    "a": (255, 215, 106),   # luz da janela
    "A": (255, 179, 71),    # luz forte
    "M": (75, 81, 99),      # metal escuro
    "s": (125, 133, 151),   # metal claro
    "f": (223, 230, 245),   # pena clara
    "F": (159, 176, 208),   # pena sombra
    "q": (201, 162, 107),   # canhão da pena
    "i": (127, 184, 214),   # isolador
    "I": (90, 140, 170),    # isolador escuro
    "h": (44, 62, 112),     # quepe azul
    "H": (192, 57, 43),     # faixa do quepe
    "P": (168, 105, 46),    # pão escuro
    "c": (243, 210, 154),   # miolo do pão
    "t": (217, 160, 91),    # casca do pão
}

# ---------------------------------------------------------------- pombo
# Visto de cima, cabeça para cima. Três quadros de batida de asa.
POMBO_CABECA = [
    "......kyyk......",
    ".....kevvek.....",
    ".....kpvvpk.....",
    "......kggk......",
]
POMBO_CAUDA = [
    "....kkgllgkk....",
    ".....kgllgk.....",
    "......kggk......",
    ".....kgkkgk.....",
    ".....kglglk.....",
    "......kkkk......",
    "................",
]
POMBO_ASAS = [
    [  # asas abertas
        "kk...kgllgk...kk",
        "kglkkgbbbbgkklgk",
        "kgllggbBBbggllgk",
        ".kglllgbbglllgk.",
        "..kkggggggggkk..",
    ],
    [  # asas no meio
        "...kkkgllgkkk...",
        "..kglkgbbgklgk..",
        "..kgllgBBgllgk..",
        "...kgllbbllgk...",
        "....kkggggkk....",
    ],
    [  # asas fechadas
        ".....kgllgk.....",
        "....kglbbglk....",
        "....kglBBglk....",
        "....kgllllgk....",
        ".....kggggk.....",
    ],
]

# ---------------------------------------------------------------- gato
GATO = [
    "................",
    "..kk........kk..",
    ".kOOk......kOOk.",
    ".kOokkkkkkkkoOk.",
    ".kooooooooooook.",
    ".kooeeooooeeook.",
    ".kowwwonnowwwok.",
    "..kowwwwwwwwok..",
    "...kkookkookk...",
    "..kooOooooOook..",
    ".kooOooooooOook.",
    ".kooOooooooOook.",
    ".koowwoooowwook.",
    "..kkkkkkkkkkkoOk",
    "............kOk.",
    "................",
]

# ---------------------------------------------------------------- objetos
CARTA = [
    "kkkkkkkkkkkk",
    "kWwwwwwwwwWk",
    "kwWwwwwwwWwk",
    "kwwWwwwwWwwk",
    "kwwwWrrWwwwk",
    "kwwwwrrwwwwk",
    "kwwwwwwwwwwk",
    "kwwwwwwwwwwk",
    "kkkkkkkkkkkk",
]

JANELA = [
    "kkkkkkkkkkkkk",
    "kmmmmmmmmmmmk",
    "kmaaaamaaaamk",
    "kmaAaamaAaamk",
    "kmaaaamaaaamk",
    "kmaaaamaaaamk",
    "kmmmmmmmmmmmk",
    "kmaaaamaaaamk",
    "kmaAaamaAaamk",
    "kmaaaamaaaamk",
    "kmaaaamaaaamk",
    "kmmmmmmmmmmmk",
    "kkkkkkkkkkkkk",
]

PAO = [
    "..kkkkkk..",
    ".kttcttck.",
    "ktttttttPk",
    "kttcttcttk",
    "kttttttPPk",
    "kPttttttPk",
    ".kPPPPPPk.",
    "..kkkkkk..",
]

LANTERNA = [
    "...kkkk...",
    "..k....k..",
    "..kkkkkk..",
    ".kMMMMMMk.",
    ".ksaaaask.",
    ".ksaAAask.",
    ".ksaAAask.",
    ".ksaaaask.",
    ".kMMMMMMk.",
    "..kssssk..",
    "..kkkkkk..",
    "..........",
]

PENA = [
    ".....kk...",
    "....kffk..",
    "...kfFfk..",
    "...kfFffk.",
    "..kffFffk.",
    "..kfFffk..",
    ".kffFffk..",
    ".kfFffk...",
    "kffFfk....",
    "kfFk......",
    "kqk.......",
    "kk........",
]

POSTE = [
    "..kkkk..",
    ".kmmmmk.",
    "kmmiimmk",
    "kmiIIimk",
    "kmiIIimk",
    "kmmiimmk",
    ".kmmmmk.",
    "..kkkk..",
]

RETRATO_BICO = [
    "....kkkkkkkk....",
    "...khhhhhhhhk...",
    "..khhhhHHhhhhk..",
    ".kkkkkkkkkkkkkk.",
    "..kggggggggggk..",
    ".kggweggggewggk.",
    ".kggwwggggwwggk.",
    ".kggggyyyyggggk.",
    ".kgggggyygggggk.",
    ".kggggggggggggk.",
    "..kvvggggggvvk..",
    "..kpvvvvvvvvpk..",
    "...kpvpvvpvpk...",
    "..kgllllllllgk..",
    ".kggllllllllggk.",
    ".kkkkkkkkkkkkkk.",
]


def desenhar(mapa, escala, paleta=PALETA, troca=None):
    """Converte um mapa de texto numa Surface ampliada."""
    troca = troca or {}
    largura = max(len(linha) for linha in mapa)
    surf = pygame.Surface((largura, len(mapa)), pygame.SRCALPHA)
    for y, linha in enumerate(mapa):
        for x, ch in enumerate(linha):
            if ch == ".":
                continue
            cor = troca.get(ch, paleta.get(ch))
            if cor is None:
                raise ValueError(f"cor desconhecida '{ch}'")
            surf.set_at((x, y), cor)
    return pygame.transform.scale(surf, (largura * escala, len(mapa) * escala))


def salvar(surf, nome):
    pygame.image.save(surf, os.path.join(PASTA, nome))
    print("  ", nome, surf.get_size())


def torre(escala):
    """A Torre do Relógio é desenhada com formas (é grande demais para mapa)."""
    w, h = 30, 46
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    k = PALETA["k"]
    pedra, pedra_esc = (141, 127, 113), (106, 94, 83)
    telhado, telhado_esc = (122, 59, 59), (90, 42, 42)
    ouro = (226, 179, 60)
    # telhado em pirâmide
    pygame.draw.polygon(s, k, [(15, 0), (2, 14), (28, 14)])
    pygame.draw.polygon(s, telhado, [(15, 2), (4, 13), (26, 13)])
    pygame.draw.polygon(s, telhado_esc, [(15, 2), (15, 13), (26, 13)])
    s.set_at((15, 0), ouro)
    # corpo
    pygame.draw.rect(s, k, (4, 14, 22, 32))
    pygame.draw.rect(s, pedra, (5, 15, 20, 30))
    pygame.draw.rect(s, pedra_esc, (17, 15, 8, 30))
    for yy in range(18, 45, 4):  # linhas das pedras
        pygame.draw.line(s, pedra_esc, (5, yy), (16, yy))
    # relógio
    pygame.draw.circle(s, k, (15, 23), 7)
    pygame.draw.circle(s, (242, 234, 216), (15, 23), 6)
    pygame.draw.circle(s, ouro, (15, 23), 6, 1)
    pygame.draw.line(s, k, (15, 23), (15, 18))   # ponteiro dos minutos (12)
    pygame.draw.line(s, k, (15, 23), (19, 23))   # ponteiro das horas (3h... quase 6h, ver no jogo)
    # janela iluminada (destino final)
    pygame.draw.rect(s, k, (11, 33, 8, 10))
    pygame.draw.rect(s, PALETA["a"], (12, 34, 6, 8))
    pygame.draw.line(s, PALETA["m"], (15, 34), (15, 41))
    pygame.draw.line(s, PALETA["m"], (12, 37), (17, 37))
    return pygame.transform.scale(s, (w * escala, h * escala))


# Cada personagem é o mesmo desenho de pombo com outra paleta.
# "h"/"H" são o quepe e a faixa do quepe no retrato.
PALETAS_POMBOS = {
    "bico": {},
    "pipoca": {"g": (206, 196, 178), "l": (244, 238, 222), "v": (222, 150, 110),
               "p": (200, 110, 100), "b": (180, 70, 60), "B": (140, 50, 44),
               "h": (192, 57, 43), "H": (244, 238, 222)},
    "tiao": {"g": (146, 108, 80), "l": (196, 160, 122), "v": (110, 140, 76),
             "p": (84, 110, 60), "b": (90, 70, 50), "B": (66, 50, 36),
             "h": (56, 92, 62), "H": (232, 176, 74)},
    "neblina": {"g": (118, 146, 172), "l": (192, 210, 226), "v": (96, 176, 186),
                "p": (70, 120, 160), "b": (60, 72, 96), "B": (44, 54, 74),
                "h": (40, 50, 72), "H": (127, 184, 214)},
    "dourado": {"g": (214, 168, 58), "l": (248, 216, 120), "v": (204, 120, 40),
                "p": (170, 86, 40), "b": (122, 40, 40), "B": (92, 30, 30),
                "h": (122, 59, 158), "H": (246, 211, 101)},
}


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(PASTA, exist_ok=True)
    print("Gerando sprites em", os.path.abspath(PASTA))

    for i, asas in enumerate(POMBO_ASAS):
        mapa = POMBO_CABECA + asas + POMBO_CAUDA
        salvar(desenhar(mapa, 3), f"pombo_{i}.png")
        # O corvo usa o mesmo desenho com outras cores (preto e olho vermelho)
        corvo = {
            "g": (62, 62, 86), "l": (100, 100, 132), "v": (30, 30, 44),
            "p": (55, 45, 80), "e": (224, 64, 64), "b": (42, 42, 58),
            "B": (30, 30, 44), "y": (150, 140, 100),
        }
        salvar(desenhar(mapa, 3, troca=corvo), f"corvo_{i}.png")

    salvar(desenhar(GATO, 3), "gato_0.png")
    # quadro do bote: olhos arregalados e boca aberta
    gato_bote = [linha.replace("e", "E") for linha in GATO]
    gato_bote[7] = "..kowwwkkwwwok.."
    salvar(desenhar(gato_bote, 3), "gato_1.png")

    salvar(desenhar(CARTA, 3), "carta.png")
    salvar(desenhar(CARTA, 3, troca={"w": (246, 211, 101), "W": (212, 160, 23),
                                      "r": (122, 59, 158)}), "carta_especial.png")
    salvar(desenhar(JANELA, 3), "janela_acesa.png")
    salvar(desenhar(JANELA, 3, troca={"a": (58, 74, 106), "A": (45, 58, 85)}),
           "janela_apagada.png")
    salvar(desenhar(PAO, 3), "pao.png")
    salvar(desenhar(LANTERNA, 3), "lanterna.png")
    salvar(desenhar(PENA, 3), "asa_extra.png")
    salvar(desenhar(PENA, 2), "pena_hud.png")
    salvar(desenhar(PENA, 2, troca={"f": (70, 74, 96), "F": (55, 58, 78),
                                    "q": (70, 74, 96)}), "pena_hud_vazia.png")
    salvar(desenhar(CARTA, 2), "carta_hud.png")
    salvar(desenhar(CARTA, 2, troca={"w": (60, 64, 86), "W": (50, 54, 74),
                                     "r": (50, 54, 74)}), "carta_hud_vazia.png")
    salvar(desenhar(CARTA, 2, troca={"w": (246, 211, 101), "W": (212, 160, 23),
                                     "r": (122, 59, 158)}), "carta_especial_hud.png")
    salvar(desenhar(POSTE, 3), "poste.png")
    for nome, troca in PALETAS_POMBOS.items():
        for i, asas in enumerate(POMBO_ASAS):
            salvar(desenhar(POMBO_CABECA + asas + POMBO_CAUDA, 3, troca=troca),
                   f"pombo_{nome}_{i}.png")
        salvar(desenhar(RETRATO_BICO, 6, troca=troca), f"retrato_{nome}.png")
    salvar(torre(4), "torre.png")
    # ícone da janela do jogo
    salvar(desenhar(POMBO_CABECA + POMBO_ASAS[0] + POMBO_CAUDA, 2), "icone.png")
    pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
