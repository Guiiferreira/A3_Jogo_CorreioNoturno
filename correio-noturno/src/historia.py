"""Todos os textos da história ficam aqui, separados do código do jogo.

Cada tela de história é um dicionário:
    {"texto": "..."}                      -> narração
    {"fala": "...", "quem": "pipoca"}     -> fala com o retrato do pombo
Se "quem" não for informado, quem fala é o Bico.
"""

# ------------------------------------------------------------------ introdução
INTRO_COMUM = [
    {"texto": "Vila Garoa, meia-noite.\n\nBico é o pombo-correio mais antigo da agência. "
              "Amanhã de manhã ele se aposenta."},
    {"texto": "Antes de ir embora, ele precisa escolher quem vai herdar o seu quepe "
              "de carteiro-chefe."},
    {"texto": "Mas uma tempestade rasgou o malote da noite. As cartas caíram pelos telhados, "
              "e às 6h a cidade acorda.\n\nCarta atrasada é carta perdida."},
    {"texto": "No fundo da bolsa, intacta, ainda está a carta mais importante.\n\n"
              "Destinatária: Dona Celeste, no alto da Torre do Relógio."},
]

# Última tela da introdução, conforme o pombo escolhido
FALA_INICIAL = {
    "bico": {"fala": "Último turno, velho. Vamos fazer isso direito."},
    "pipoca": {"fala": "Deixa comigo, seu Bico! Hoje eu mostro que estou pronta.",
               "quem": "pipoca"},
    "tiao": {"fala": "Pode descansar a asa, Bico. Hoje quem carrega o malote sou eu.",
             "quem": "tiao"},
    "neblina": {"fala": "Noite feia, do jeito que eu gosto. Vamos nessa.", "quem": "neblina"},
    "dourado": {"fala": "Mais uma noite, mais uma lenda.", "quem": "dourado"},
}


def intro(personagem_id):
    return INTRO_COMUM + [FALA_INICIAL[personagem_id]]


# ------------------------------------------------------------------ entre fases
# Bico fala antes de cada fase (quando outro pombo voa, ele vira o mentor no rádio).
FALAS_FASE = [
    "Bairro tranquilo. Pegue as cartas e entregue nas janelas acesas. "
    "Cuidado com os fios... e com os gatos dos telhados.",
    "No centro os corvos não dormem. E eles adoram papel.",
    "Vento do mar e neblina no porto. Uma lanterna viria bem agora.",
    "Lá está ela, a torre. Mais algumas entregas e depois a carta da Dona Celeste.",
]

# Dicas que aparecem rapidinho dentro da partida (tutorial da fase 1)
DICAS_FASE_1 = [
    "Pegue as cartas espalhadas pelos telhados",
    "Voe sobre uma janela acesa para entregar",
    "Espaço = arrancada. Use para fugir do bote dos gatos!",
]

# ------------------------------------------------------------------ pombos liberados
# Quem a gente conhece pelo caminho (aparece quando o pombo é liberado)
ENCONTROS = {
    "pipoca": {"fala": "Seu Bico! Eu vi a tempestade e vim ajudar. Sou rápida, "
                       "me deixa voar uma noite dessas?", "quem": "pipoca"},
    "tiao": {"fala": "Ô, carteiro! Conheço cada telhado do centro. Sou lento, mas "
                     "carrego carta que é uma beleza. Me chama na próxima.", "quem": "tiao"},
    "neblina": {"fala": "Neblina não me assusta, eu nasci no porto. Se precisar de alguém "
                        "para a próxima noite, é só chamar.", "quem": "neblina"},
    "dourado": {"fala": "Todas as cartas antes do sol? Então você merece voar comigo.",
                "quem": "dourado"},
}

# ------------------------------------------------------------------ finais
CELESTE = [
    {"texto": "O sino da torre começa a tocar. Dona Celeste abre a janela "
              "e recebe o envelope dourado."},
    {"texto": "Dentro, uma foto antiga de duas meninas na praia e um bilhete:\n\n"
              "\"Estou voltando. Me espere no domingo. — Lúcia\""},
    {"texto": "Era a irmã que ela não via havia quarenta anos."},
]

# O final feliz muda conforme o pombo: quem vence herda o quepe.
DESFECHO = {
    "bico": [
        {"fala": "Agora sim. Pode amanhecer."},
        {"texto": "Bico se aposentou naquela manhã. Pendurou o quepe na porta da agência "
                  "com um bilhete:\n\n\"Para quem fizer a próxima noite.\""},
    ],
    "pipoca": [
        {"fala": "Eu consegui, seu Bico! Eu consegui!", "quem": "pipoca"},
        {"texto": "Bico riu, tirou o quepe e colocou na cabeça dela.\n\n"
                  "\"Ficou grande. Você cresce nele.\""},
    ],
    "tiao": [
        {"fala": "Nenhuma carta amassada, chefe.", "quem": "tiao"},
        {"texto": "Bico entregou o quepe a Tião. Dizem que, desde aquela noite, "
                  "nunca mais se perdeu uma carta no centro."},
    ],
    "neblina": [
        {"fala": "Nem vi a neblina passar.", "quem": "neblina"},
        {"texto": "Bico entregou o quepe a Neblina, a primeira carteira-chefe "
                  "vinda do porto."},
    ],
    "dourado": [
        {"fala": "A lenda continua.", "quem": "dourado"},
        {"texto": "Na agência ninguém sabe quem é o pombo dourado. Mas o quepe de Bico "
                  "ficou guardado, esperando por ele."},
    ],
}


def final_vitoria(personagem_id):
    return CELESTE + DESFECHO[personagem_id]


def final_amanheceu(personagem_id, nome):
    return [
        {"texto": "O galo cantou antes da última entrega.\n\n"
                  "A cidade acordou e algumas cartas ficaram sem destino."},
        {"fala": "Desculpe, Dona Celeste... Essa noite foi comprida demais.",
         "quem": personagem_id},
        {"texto": f"O quepe ainda não tem dono. Talvez {nome} tenha mais uma noite."},
    ]


def final_sem_penas(personagem_id, nome):
    return [
        {"texto": f"Cansado e sem forças, {nome} pousou num telhado e não conseguiu "
                  "mais voar."},
        {"fala": "Só um minutinho de descanso... só um...", "quem": personagem_id},
        {"texto": "As cartas vão ter que esperar a próxima noite."},
    ]
