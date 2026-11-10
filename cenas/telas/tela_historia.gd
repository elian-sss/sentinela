class_name TelaHistoria
extends CanvasLayer
## Modo história: no início de cada onda, pausa o jogo e mostra um trecho curto da história.
## Clique, J, Espaço ou Enter continuam. Cada trecho aparece só uma vez por sessão,
## para não atrapalhar quem reinicia várias vezes.

## Um trecho por onda, na mesma ordem de Balanceamento.ONDAS.
const TRECHOS: Array[Dictionary] = [
	{
		"titulo": "O despertar",
		"texto": "Há séculos a árvore sagrada guarda o coração da floresta.\nHoje o som dos machados chegou à clareira.\nDesperte, Sentinela, e proteja a árvore.",
	},
	{
		"titulo": "Fumaça no horizonte",
		"texto": "Os lenhadores voltaram, e trouxeram fogo.\nGolpeie as chamas antes que cheguem à árvore.",
	},
	{
		"titulo": "O ronco das motosserras",
		"texto": "Um barulho de motor corta o silêncio da mata.\nOs motosserristas são rápidos, mas caem fácil.",
	},
	{
		"titulo": "A grande investida",
		"texto": "Eles vieram todos de uma vez.\nA floresta inteira confia em você.",
	},
	{
		"titulo": "A máquina",
		"texto": "O chão treme. Uma escavadeira enorme avança, derrubando tudo pelo caminho.\nQuando ela investir, desvie. Atordoada, ela fica frágil.",
	},
]
const TEXTO_VITORIA: String = "A máquina parou. A floresta respira de novo,\ne a árvore sagrada segue de pé."

## Tempo entre fechar o trecho e o jogo voltar, para a tecla usada não virar dash ou ataque.
const ATRASO_AO_FECHAR: float = 0.1

static var _ondas_ja_vistas: Array[int] = []

@export var gerente_de_ondas: GerenteDeOndas

@onready var _titulo: Label = $Centro/Caixa/Titulo
@onready var _texto: Label = $Centro/Caixa/Texto


func _ready() -> void:
	hide()
	gerente_de_ondas.onda_iniciada.connect(_ao_iniciar_onda)


func _unhandled_input(evento: InputEvent) -> void:
	if not visible:
		return
	if evento.is_action_pressed("ui_accept") or evento.is_action_pressed("atacar"):
		get_viewport().set_input_as_handled()
		_fechar()


func _ao_iniciar_onda(numero: int) -> void:
	if numero > TRECHOS.size() or numero in _ondas_ja_vistas:
		return
	_ondas_ja_vistas.append(numero)
	var trecho: Dictionary = TRECHOS[numero - 1]
	_titulo.text = trecho["titulo"]
	_texto.text = trecho["texto"]
	show()
	get_tree().paused = true


func _fechar() -> void:
	hide()
	await get_tree().create_timer(ATRASO_AO_FECHAR, true).timeout
	get_tree().paused = false
