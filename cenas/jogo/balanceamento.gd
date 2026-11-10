extends Node
## Autoload "Balanceamento": todos os números que mudam a dificuldade, num lugar só.
## Os scripts leem daqui. Para ajustar o jogo, mude só este arquivo.
## Tempos em segundos, distâncias e velocidades em pixels (e pixels por segundo).

# ---------------------------------------------------------------- herói

const HEROI_VIDA: int = 100
const HEROI_VELOCIDADE: float = 220.0
const HEROI_VELOCIDADE_DASH: float = 700.0
const HEROI_DURACAO_DASH: float = 0.15
const HEROI_COOLDOWN_DASH: float = 1.5
const HEROI_DANO_ATAQUE: int = 10
const HEROI_COOLDOWN_ATAQUE: float = 0.3
const HEROI_DISTANCIA_GOLPE: float = 34.0 ## do centro do herói ao centro da hitbox
const HEROI_DURACAO_GOLPE: float = 0.1 ## tempo em que a hitbox fica ativa
const HEROI_INVENCIBILIDADE: float = 1.0 ## depois de levar dano

# ---------------------------------------------------------------- árvore

const ARVORE_VIDA: int = 300
const ARVORE_REGENERACAO_ENTRE_ONDAS: float = 0.1 ## fração da vida máxima curada ao fim de cada onda (menos a última)

# ---------------------------------------------------------------- inimigos
# As chaves de cada tipo são os nomes das variáveis em inimigo.gd.
# "dano" e "intervalo_ataque" são contra a árvore; "dano_heroi" e "intervalo_dano_heroi", contra o herói.

const INIMIGOS: Dictionary = {
	"lenhador": {
		"vida": 30,
		"velocidade": 60.0,
		"dano": 5,
		"intervalo_ataque": 1.0,
		"alcance_ataque": 56.0,
		"dano_heroi": 8,
		"raio_dano_heroi": 40.0,
		"intervalo_dano_heroi": 1.0,
	},
	"motosserrista": {
		"vida": 20,
		"velocidade": 90.0,
		"dano": 7,
		"intervalo_ataque": 1.0,
		"alcance_ataque": 56.0,
		"dano_heroi": 15,
		"raio_dano_heroi": 40.0,
		"intervalo_dano_heroi": 1.0,
	},
}

# ---------------------------------------------------------------- fogo

const FOGO_VIDA: int = 30
const FOGO_DANO_ARVORE: int = 4
const FOGO_INTERVALO_DANO: float = 1.0
const FOGO_RAIO_INICIAL: float = 16.0
const FOGO_RAIO_MAXIMO: float = 64.0
const FOGO_VELOCIDADE_CRESCIMENTO: float = 3.0 ## pixels de raio por segundo
const FOGO_ALCANCE_DANO_ARVORE: float = 40.0 ## além da borda do fogo
const FOGO_DISTANCIA_MINIMA_ARVORE: float = 80.0
const FOGO_DISTANCIA_MAXIMA_ARVORE: float = 100.0

# ---------------------------------------------------------------- chefe (escavadeira)

const CHEFE_VIDA: int = 500
const CHEFE_VELOCIDADE_AVANCO: float = 35.0
const CHEFE_TEMPO_AVANCO: float = 4.0
const CHEFE_TEMPO_AVISO: float = 1.0
const CHEFE_VELOCIDADE_INVESTIDA: float = 420.0
const CHEFE_TEMPO_ATORDOADO: float = 2.5
const CHEFE_MULTIPLICADOR_DANO_ATORDOADO: int = 3
const CHEFE_DANO_CONTATO_HEROI: int = 10
const CHEFE_DANO_INVESTIDA_HEROI: int = 20
const CHEFE_RAIO_CONTATO_HEROI: float = 56.0
const CHEFE_DANO_ARVORE: int = 10
const CHEFE_INTERVALO_ATAQUE_ARVORE: float = 1.5
const CHEFE_RAIO_CONTATO_ARVORE: float = 80.0
const CHEFE_INTERVALO_INVOCACAO: float = 18.0
const CHEFE_LENHADORES_POR_INVOCACAO: int = 2
const CHEFE_DISTANCIA_INVOCACAO: float = 80.0

# ---------------------------------------------------------------- itens e drops

const DROP_CHANCE_BASE: float = 0.3
const DROP_BONUS_POR_DANO_ARVORE: float = 0.005 ## soma à chance por ponto de dano que o inimigo causou na árvore
const DROP_CHANCE_MAXIMA: float = 0.55
# Pesos do sorteio de qual item cai (não precisam somar 100). Hoje: 30% fruta, 30% erva,
# 15% escudo, 12,5% velocidade, 12,5% força.
const DROP_PESO_FRUTA: float = 3.0
const DROP_PESO_ERVA: float = 3.0
const DROP_PESO_ESCUDO: float = 1.5
const DROP_PESO_VELOCIDADE: float = 1.25
const DROP_PESO_FORCA: float = 1.25
const ITEM_CURA_FRUTA: int = 25
const ITEM_CURA_ERVA: int = 40
const ITEM_DURACAO_ESCUDO: float = 4.0
const ITEM_DURACAO_VELOCIDADE: float = 6.0
const ITEM_MULTIPLICADOR_VELOCIDADE: float = 1.4 ## só no andar, o dash não muda
const ITEM_DURACAO_FORCA: float = 6.0
const ITEM_MULTIPLICADOR_DANO_FORCA: int = 2
const ITEM_ESCALA_GOLPE_FORCA: float = 1.3 ## golpe maior, com hitbox maior junto
const ITEM_TEMPO_NO_CHAO: float = 8.0

# ---------------------------------------------------------------- ondas
# Uma entrada por onda: quantos inimigos de cada tipo e o intervalo entre um nascimento e outro.
# Tipos: "lenhador", "motosserrista", "fogo", "chefe".

const PAUSA_ENTRE_ONDAS: float = 4.0
const ONDAS: Array[Dictionary] = [
	{"inimigos": {"lenhador": 4}, "intervalo": 2.0},
	{"inimigos": {"lenhador": 6, "fogo": 2}, "intervalo": 1.5},
	{"inimigos": {"lenhador": 4, "motosserrista": 8}, "intervalo": 1.1},
	{"inimigos": {"lenhador": 6, "motosserrista": 8, "fogo": 3}, "intervalo": 0.9},
	{"inimigos": {"chefe": 1}, "intervalo": 1.0},
]

# ---------------------------------------------------------------- modo ondas infinitas
# Repete as ONDAS em ciclos de 5 (a 5ª de cada ciclo é sempre o chefe), cada ciclo mais pesado.
# Ciclo 0 = ondas 1 a 5, ciclo 1 = ondas 6 a 10, e assim por diante.

const INFINITO_AUMENTO_QUANTIDADE_POR_CICLO: float = 0.5 ## +50% de inimigos a cada ciclo (arredonda para cima)
const INFINITO_REDUCAO_INTERVALO_POR_CICLO: float = 0.1 ## intervalo entre nascimentos cai 10% a cada ciclo
const INFINITO_INTERVALO_MINIMO: float = 0.5
const INFINITO_ESCOLTA_CHEFE_POR_CICLO: int = 3 ## lenhadores extras na onda do chefe a cada ciclo
