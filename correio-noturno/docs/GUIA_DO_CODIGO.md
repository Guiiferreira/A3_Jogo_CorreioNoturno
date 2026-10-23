# Guia do código – para estudar antes da apresentação

O professor pode pedir para qualquer integrante explicar ou alterar qualquer trecho. Este guia mostra onde cada coisa está e como ela funciona, na ordem em que vale a pena estudar.

## 1. O laço principal (`src/jogo.py`)

Todo jogo em pygame é um laço que repete 60 vezes por segundo:

1. **entrada**: `pygame.event.get()` lê teclado, mouse e o botão de fechar;
2. **atualizar**: move tudo e checa colisões;
3. **desenhar**: pinta a tela e chama `pygame.display.flip()`.

No nosso caso isso está em `Jogo.rodar()` e `Jogo.passo()`. O `dt` (delta time) é o tempo em segundos desde o último quadro. Tudo que se move usa `velocidade * dt`, por isso o jogo roda na mesma velocidade em computador rápido ou lento. O `dt` é limitado a 0,05 s para nada "teleportar" se o computador travar um instante.

As teclas M, F11 e F12 são tratadas em `Jogo.tratar_evento()` porque valem em qualquer tela. O resto vai para a cena atual.

## 2. Cenas (telas)

Cada tela é uma classe com três métodos: `evento(e)`, `atualizar(dt)` e `desenhar(tela)` (veja `src/cenas/base.py`). O jogo sempre tem uma cena ativa, e para trocar de tela basta chamar `jogo.trocar_cena(NovaCena(jogo))`.

| Cena | Arquivo | O que faz |
|---|---|---|
| MenuPrincipal | `cenas/menu.py` | Título e opções |
| Narrativa | `cenas/narrativa.py` | Textos da introdução e dos finais, com efeito de máquina de escrever |
| Partida | `cenas/partida.py` | O jogo em si |
| TelaFim | `cenas/fim.py` | Pontuação, recorde e "jogar de novo" |
| ComoJogar, Opcoes, Recordes, Creditos | `cenas/telas.py` | Telas auxiliares |

A `Narrativa` recebe uma função `ao_terminar`. É assim que a introdução sabe que deve abrir a partida e que o final sabe que deve abrir a tela de fim.

## 3. A partida (`src/cenas/partida.py`)

A partida tem uma **máquina de estados** em `self.estado`:

```
interludio --Enter--> jogando --meta cumprida--> concluida --1,8 s--> interludio (próxima fase)
                                                         \--pombo novo--> liberado --Enter--> interludio
                         |  \--P/Esc--> pausado --P/Esc--> (volta)
                         \--6h ou sem penas ou chegou na torre--> terminando --2,6 s--> Narrativa do final
```

Em `atualizar()` cada estado faz uma coisa diferente. No interlúdio e na pausa o relógio da noite não anda.

**Relógio da noite:** `self.minutos` vai de 0 a 360 (meia-noite às 6h). A cada quadro soma `360 / segundos_noite * dt`. O `segundos_noite` vem da dificuldade em `config.py`.

**Surgimento de objetos (`_surgir`)**: cada tipo de objeto tem um cronômetro em `self.timers`. Quando chega a zero, o objeto nasce acima da tela e o cronômetro recomeça com um intervalo sorteado (±25%). Os intervalos de cada fase ficam em `config.FASES`. Inimigos ficam mais frequentes conforme as entregas avançam. Se o jogador fica sem cartas, uma nova aparece mais cedo, para ninguém ficar travado.

**Colisões (`_colisoes`)**: usamos círculos. Dois objetos se tocam quando a distância entre os centros é menor que a soma dos raios (`Entidade.encosta`). O fio é uma linha, então usamos a distância de um ponto até um segmento (`dist_ponto_segmento` em `entidades.py`).

**Dano (`_dano`)**: tira uma pena, deixa o pombo piscando por 1,6 s (invencível), zera o combo, faz a tela tremer e derruba uma carta.

## 4. Personagens (`src/entidades.py`)

Todos herdam de `Entidade`, que guarda `x`, `y`, `vivo` e desce junto com a cidade (`y += rolagem * dt`). Quando sai por baixo da tela, `vivo = False` e a partida remove o objeto da lista.

- **Pombo**: o movimento é suavizado (a velocidade vai se aproximando da velocidade desejada), o que dá sensação de voo sem deixar o controle lento. Na diagonal a velocidade é multiplicada por 0,7071 para não ficar mais rápida. A arrancada multiplica a velocidade por 2,6 por 0,22 s.
- **Gato**: máquina de estados própria: `espreitando -> alerta ("!") -> bote -> voltando`. Só machuca no bote.
- **Fio**: pode ser intermitente: fica 2,2 s ligado e 1,4 s desligado.
- **Corvo**: a cada quadro calcula o ângulo até o pombo com `math.atan2` e vira devagar nessa direção. Como a curva é lenta, dá para despistar.
- **Torre**: desce até `y = 230` e para.

## 4b. Personagens e desbloqueio

Os cinco pombos são dados, não classes: cada um é um dicionário em `config.PERSONAGENS` com velocidade, penas a mais ou a menos, capacidade da bolsa, recarga da arrancada, quanto sente o vento e a neblina, tamanho e o que libera. A classe `Pombo` recebe esse dicionário e copia os valores (`self.velocidade`, `self.capacidade`, `self.tempo_recarga`...). Assim, para criar um pombo novo basta acrescentar um dicionário, uma paleta em `tools/gerar_sprites.py` e as falas em `historia.py`.

Os sprites dos pombos são todos o mesmo desenho com paletas diferentes (`PALETAS_POMBOS` em `gerar_sprites.py`).

O desbloqueio acontece em `Partida._entregar`: quando a fase é concluída, o jogo procura o personagem com `libera == número da fase` e chama `dados.liberar()`. Essa função devolve `True` só na primeira vez, e então a partida entra no estado `"liberado"`, que mostra a apresentação do pombo antes da próxima fase. O Dourado é liberado em `_terminar` quando o resultado é vitória. A lista de liberados fica em `dados/progresso.json`.

A tela de seleção (`cenas/selecao.py`) desenha os bloqueados como silhueta usando a máscara do sprite (`pygame.mask`) pintada de uma cor só. As barrinhas da ficha são calculadas a partir dos números do personagem (função `barras`).

## 5. Cenário (`src/cenario.py`)

A cidade é desenhada uma vez, por código, numa imagem de 960 x 1200 px feita de quarteirões de 240 px. Como a altura é múltipla do quarteirão, a imagem repete sem emenda: ela é desenhada duas vezes, uma em cima da outra, deslocadas pela rolagem. Cada fase usa uma semente diferente no `random.Random`, então a cidade é sempre a mesma em cada fase.

`y_em_telhado()` e `y_de_rua()` servem para cartas e janelas nascerem sobre telhados e fios nascerem sobre ruas.

A classe `Ceu` cobre a tela com um véu azul escuro que fica mais transparente conforme o relógio avança. Depois das ~3h40 o véu vai ficando laranja e aparece um degradê no topo (o sol nascendo). As luzes dos postes e das janelas são somadas por cima com `BLEND_ADD`.

## 6. Sprites e sons (`tools/`)

- `gerar_sprites.py`: cada sprite é uma lista de textos em que cada letra é a cor de um pixel (`.` é transparente). A função `desenhar()` converte isso numa imagem e amplia 3 vezes. O corvo é o mesmo desenho do pombo com outra paleta.
- `gerar_sons.py`: cada som é uma soma de ondas (seno, quadrada, triângulo, serra, ruído) com um envelope de volume. As músicas são listas de notas MIDI tocadas por "instrumentos" simples. O resultado é salvo em WAV com o módulo `wave`.

No jogo, `recursos.Audio` usa `pygame.mixer.Sound` para efeitos e `pygame.mixer.music` para as trilhas (menu, noite, madrugada e amanhecer). Se o computador não tiver placa de som, o jogo roda mudo em vez de travar.

## 7. Perguntas que o professor pode fazer

**Como mudar a velocidade do pombo?** `POMBO_VELOCIDADE` em `src/config.py`.

**Como deixar a noite mais longa?** `segundos_noite` em `DIFICULDADES`, no mesmo arquivo.

**Como adicionar uma fase?** Acrescentar um dicionário em `config.FASES`, um tema em `cenario.TEMAS` e uma fala em `historia.FALAS_FASE`.

**Como mudar o que libera um pombo?** O campo `libera` do pombo em `config.PERSONAGENS` (número da fase ou `"vitoria"`).

**Como deixar a Pipoca mais rápida?** O campo `velocidade` dela em `config.PERSONAGENS` (1.0 é a velocidade do Bico).

**Como adicionar um power-up?** Criar o sprite em `tools/gerar_sprites.py`, colocar o nome em `PowerUp.IMAGENS` e tratar o efeito em `Partida._pegar_powerup`.

**Onde fica salvo o recorde?** `dados/recordes.json`, pelo `src/dados.py`.

**Por que a velocidade é multiplicada por `dt`?** Para o movimento depender do tempo e não da quantidade de quadros por segundo.

**Por que a arrancada protege de dano?** Em `_colisoes`, `protegido` é verdadeiro quando `p.arrancada > 0`. É uma recompensa para quem usa a arrancada na hora certa.

**Uma dificuldade técnica que tivemos:** no começo os fios elétricos causavam quase todas as derrotas nos testes, porque atravessavam metade da tela e apareciam com muita frequência. Diminuímos a largura deles, aumentamos o intervalo e criamos fios que ligam e desligam, com aviso piscando antes de religar. Outra foi deixar o pombo visível sobre telhados cinzentos: resolvemos com um contorno claro gerado a partir da máscara do sprite (`Pombo._com_contorno`).

## 8. Versão web (`web/jogo_fonte.html`)

É a mesma lógica traduzida para JavaScript, usando Canvas. As diferenças: a tela é em pé (540 de largura, altura conforme o celular), o controle é um joystick virtual (o ponto onde o dedo encosta vira o centro e a direção do arraste move o pombo) e o áudio usa a Web Audio API, que no iPhone só começa depois do primeiro toque. O `tools/gerar_web.py` embute as imagens e os sons no HTML para virar um arquivo só.
