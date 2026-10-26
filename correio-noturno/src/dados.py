"""Salva e carrega opções e recordes em arquivos JSON na pasta dados/."""
import json
import os

from . import config

ARQ_OPCOES = os.path.join(config.PASTA_DADOS, "opcoes.json")
ARQ_RECORDES = os.path.join(config.PASTA_DADOS, "recordes.json")
MAX_RECORDES = 5

OPCOES_PADRAO = {
    "dificuldade": "Normal",
    "vol_musica": 6,
    "vol_efeitos": 7,
    "mudo": False,
    "tela_cheia": False,
    "personagem": "bico",
}


def _ler(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _escrever(caminho, dados):
    try:
        os.makedirs(config.PASTA_DADOS, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # sem permissão de escrita: o jogo continua sem salvar


def carregar_opcoes():
    opcoes = dict(OPCOES_PADRAO)
    opcoes.update(_ler(ARQ_OPCOES, {}))
    if opcoes["dificuldade"] not in config.DIFICULDADES:
        opcoes["dificuldade"] = "Normal"
    return opcoes


def salvar_opcoes(opcoes):
    _escrever(ARQ_OPCOES, opcoes)


def carregar_recordes():
    lista = _ler(ARQ_RECORDES, [])
    return sorted(lista, key=lambda r: r.get("pontos", 0), reverse=True)[:MAX_RECORDES]


def entra_no_ranking(pontos):
    if pontos <= 0:
        return False
    lista = carregar_recordes()
    return len(lista) < MAX_RECORDES or pontos > lista[-1]["pontos"]


def adicionar_recorde(nome, pontos, dificuldade, venceu, pombo="bico"):
    lista = carregar_recordes()
    lista.append({"nome": nome, "pontos": pontos, "dificuldade": dificuldade,
                  "venceu": venceu, "pombo": pombo})
    lista = sorted(lista, key=lambda r: r["pontos"], reverse=True)[:MAX_RECORDES]
    _escrever(ARQ_RECORDES, lista)
    return lista


# ---------------------------------------------------------------- personagens liberados
ARQ_PROGRESSO = os.path.join(config.PASTA_DADOS, "progresso.json")


def carregar_liberados():
    """Lista de ids dos pombos liberados (o Bico sempre está)."""
    dados = _ler(ARQ_PROGRESSO, {})
    liberados = [i for i in dados.get("liberados", []) if i in config.PERSONAGENS_POR_ID]
    if "bico" not in liberados:
        liberados.insert(0, "bico")
    return liberados


def liberar(personagem_id):
    """Libera um pombo. Devolve True se ele ainda não estava liberado."""
    liberados = carregar_liberados()
    if personagem_id in liberados:
        return False
    liberados.append(personagem_id)
    _escrever(ARQ_PROGRESSO, {"liberados": liberados})
    return True


def zerar_liberados():
    """Volta o progresso ao começo: só o Bico liberado. Recordes e opções ficam."""
    _escrever(ARQ_PROGRESSO, {"liberados": ["bico"]})
