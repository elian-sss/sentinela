# Game Jam Semana GameDev III — Guardião da Floresta

## Contexto
Jogo 2D feito por uma pessoa só em 4 dias para a Game Jam da Semana GameDev III (Santarém, PA).
Prazo: publicar no itch.io e enviar o link por e-mail até **13/11 às 12h**.
Apresentação: 13/11 às 20h (pitch de 3 min, depois um jurado joga até 10 min).

## Tema escolhido
**Tema 1 — Heróis da Amazônia.** O herói é um guardião da floresta (inspirado no folclore amazônico) que protege uma árvore sagrada.
A interpretação do tema precisa ser clara e visível no jogo (visual, mecânica ou narrativa).

## Stack
- Godot **4.3 ou mais recente**, GDScript
- 2D, renderizador compatível com exportação **Web (HTML5)**
- Exportar SEM threads (evita problemas de SharedArrayBuffer no itch.io)
- Sem plugins externos, sem dependências

## O jogo (escopo fechado)
Arena de defesa top-down. O herói protege uma árvore sagrada no centro da clareira contra 5 ondas de ameaças.

### Controles
- WASD ou setas: mover
- Clique esquerdo ou J: atacar (corpo a corpo, curto alcance, com cooldown curto)
- Espaço: dash (cooldown de ~1,5 s)
- Esc: pausar

### Estatísticas visíveis (UI)
- Barra de vida do herói
- Barra de vida da árvore
- Indicador da onda atual (ex.: "Onda 2/5")

### Inimigos
1. Onda 1: lenhadores, andam até a árvore e a atacam
2. Onda 2: lenhadores + focos de fogo que se espalham devagar (CORTAR se faltar tempo)
3. Onda 3: motosserristas, mais rápidos e mais frágeis
4. Onda 4: mistura de tudo, em maior quantidade
5. Onda 5: chefe, uma escavadeira com padrão de ataque simples e telegrafado

Inimigos priorizam a árvore, mas atacam o herói se ele chegar perto.

### Itens (dropam dos inimigos, aleatório com baixa chance)
- Fruta: cura o herói
- Erva: regenera a árvore
- Escudo temporário: herói fica imune por poucos segundos (CORTAR se faltar tempo)

### Vitória e derrota
- Vitória: sobreviver às 5 ondas com a árvore de pé
- Derrota: árvore destruída OU herói morto
- Reinício rápido (um clique), sem telas longas

### Telas
- Tela inicial com botão "Jogar" (necessário para liberar áudio no navegador)
- "Como jogar" curto e pulável
- Tela de vitória e tela de derrota, ambas com botão de reiniciar

## Regras do regulamento que NUNCA podem ser violadas
1. Personagem jogável com controles claros
2. Pelo menos uma estatística visível
3. Condição de vitória clara
4. Condição de derrota clara
5. Pelo menos um meio de alterar as estatísticas durante a partida (itens)
6. Antagonismo ativo (inimigos e chefe)
7. Tema visível no jogo
8. Arte do protagonista, inimigos e chefe **original** (feita por mim). Asset pack licenciado só para cenário, props e tilemaps
9. Conteúdo adequado ao público geral: sem sangue, sem nudez, sem discurso de ódio. Inimigos derrotados somem em fumaça ou poeira
10. Jogo publicado no itch.io, jogável no navegador

## Critérios dos jurados (priorizar nesta ordem)
1. Jogabilidade: movimento fluido, sem falhas de animação
2. Controles fáceis de entender
3. Vontade de tentar de novo: ritmo rápido, reinício imediato
4. Progressão de desafio: cada onda um pouco mais difícil
5. Tema, narrativa curta, arte do herói e dos inimigos

Dificuldade: preferível o jogo ser fácil a ser difícil demais. Deixar valores de balanceamento em constantes fáceis de ajustar.

## Placeholders
Até eu avisar, usar formas simples (ColorRect, círculos, quadrados) no lugar de sprites. A arte final entra no dia 11/11. Nomear nós e arquivos para que trocar o placeholder por sprite seja só trocar o nó visual.

## Convenções de código
- GDScript tipado (`var vida: int = 100`)
- Uma cena por entidade: `Heroi.tscn`, `Arvore.tscn`, `Inimigo.tscn`, `Chefe.tscn`, `Item.tscn`, `Arena.tscn`, `HUD.tscn`
- Valores de balanceamento (vida, velocidade, dano, cooldown, quantidade por onda) como `@export` ou constantes no topo do script
- Comunicação entre cenas por **signals** (ex.: `vida_alterada`, `inimigo_morreu`, `onda_concluida`)
- Nomes de variáveis, funções e comentários em português
- Funções curtas, sem código morto e sem otimização prematura

## Como trabalhar comigo
- Fazer UMA tarefa por vez e dizer como testar no editor (qual cena abrir, o que apertar, o que deve acontecer)
- Não reescrever nem reestruturar o que já funciona. Só adicionar ou alterar o que foi pedido
- Não criar features fora do escopo acima. Se achar que vale, sugerir e esperar eu aprovar
- Depois de mexer em scripts, rodar o projeto em modo headless (se o Godot estiver no PATH) para checar erros de parse
- Eu faço commit no git quando algo funcionar. Avisar quando um bom ponto de commit for atingido
- Eu monto cenas visualmente no editor quando for mais simples. Nesses casos, explicar a estrutura de nós passo a passo
- Se algo for ambíguo, perguntar antes de implementar

## Exportação web (itch.io)
- Preset Web com threads DESLIGADAS
- Exportar como `index.html`, compactar tudo em .zip e enviar como "This file will be played in the browser"
- Ajustar o tamanho do viewport na página do itch.io
- Testar no Chrome e no Firefox, incluindo som depois do clique em "Jogar"

## Cronograma
- 09/11: projeto, herói (movimento e dash), árvore com vida, 1 inimigo, teste de exportação e upload no itch.io
- 10/11: sistema de ondas, 4 tipos de inimigo, itens, HUD, vitória e derrota
- 11/11: chefe, tela inicial, pausa, arte original do herói, inimigos e chefe
- 12/11: cenário, som, balanceamento, testes com outras pessoas, página no itch.io, pitch
- 13/11 manhã: conferir link, enviar e-mail antes das 12h

## Ordem de corte se faltar tempo
1. Fogo que se espalha
2. Escudo temporário
3. Pausa
Nunca cortar: 5 ondas, chefe, itens de cura, vitória e derrota, exportação web.
