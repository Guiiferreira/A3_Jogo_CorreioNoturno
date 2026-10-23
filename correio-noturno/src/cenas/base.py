"""Classe base de todas as telas (cenas) do jogo.

O jogo sempre tem UMA cena ativa. A cada quadro o laço principal chama:
    evento(e)  -> para cada evento do teclado/mouse
    atualizar(dt)
    desenhar(tela)
Para trocar de tela: self.jogo.trocar_cena(OutraCena(self.jogo)).
"""


class Cena:
    def __init__(self, jogo):
        self.jogo = jogo
        self.t = 0.0

    def evento(self, e):
        pass

    def atualizar(self, dt):
        self.t += dt

    def desenhar(self, tela):
        pass
