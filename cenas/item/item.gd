class_name Item
extends Area2D
## Item que cai dos inimigos. A fruta cura o herói, a erva cura a árvore de longe,
## o escudo deixa o herói imune a dano por alguns segundos, e os power-ups de velocidade
## e força deixam o herói mais rápido ou com golpe mais forte por alguns segundos.
## Some depois de um tempo no chão, piscando no fim.

signal coletado(tipo: Tipo)

enum Tipo { FRUTA, ERVA, ESCUDO, VELOCIDADE, FORCA }

const TEXTURAS: Dictionary = {
	Tipo.FRUTA: preload("res://assets/personagens/item_fruta.png"),
	Tipo.ERVA: preload("res://assets/personagens/item_erva.png"),
	Tipo.ESCUDO: preload("res://assets/personagens/item_escudo.png"),
	Tipo.VELOCIDADE: preload("res://assets/personagens/item_velocidade.png"),
	Tipo.FORCA: preload("res://assets/personagens/item_forca.png"),
}
const ALTURA_FLUTUAR: float = 2.0 ## pixels que o item sobe e desce no chão
const VELOCIDADE_FLUTUAR: float = 4.0

@export var tipo: Tipo = Tipo.FRUTA
var cura_fruta: int = Balanceamento.ITEM_CURA_FRUTA
var cura_erva: int = Balanceamento.ITEM_CURA_ERVA
var duracao_escudo: float = Balanceamento.ITEM_DURACAO_ESCUDO
var duracao_velocidade: float = Balanceamento.ITEM_DURACAO_VELOCIDADE
var duracao_forca: float = Balanceamento.ITEM_DURACAO_FORCA
var tempo_no_chao: float = Balanceamento.ITEM_TEMPO_NO_CHAO
@export var tempo_piscando: float = 3.0
@export var intervalo_piscar: float = 0.15

var _tempo_restante: float = 0.0

@onready var _visual: Sprite2D = $Visual


func _ready() -> void:
	_tempo_restante = tempo_no_chao
	_visual.texture = TEXTURAS[tipo]
	body_entered.connect(_ao_tocar_corpo)


func _process(delta: float) -> void:
	_tempo_restante -= delta
	_visual.position.y = sin(_tempo_restante * VELOCIDADE_FLUTUAR) * ALTURA_FLUTUAR
	if _tempo_restante <= 0.0:
		queue_free()
	elif _tempo_restante <= tempo_piscando:
		_visual.visible = int(_tempo_restante / intervalo_piscar) % 2 == 0


func _ao_tocar_corpo(corpo: Node2D) -> void:
	if corpo is Heroi:
		_aplicar_efeito(corpo)
		coletado.emit(tipo)
		queue_free()


func _aplicar_efeito(heroi: Heroi) -> void:
	match tipo:
		Tipo.FRUTA:
			heroi.curar(cura_fruta)
		Tipo.ERVA:
			var arvore: Arvore = get_tree().get_first_node_in_group("arvore")
			arvore.curar(cura_erva)
		Tipo.ESCUDO:
			heroi.ativar_escudo(duracao_escudo)
		Tipo.VELOCIDADE:
			heroi.ativar_velocidade(duracao_velocidade)
		Tipo.FORCA:
			heroi.ativar_forca(duracao_forca)
