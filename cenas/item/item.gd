class_name Item
extends Area2D
## Item que cai dos inimigos. A fruta cura o herói, a erva cura a árvore de longe,
## o escudo deixa o herói imune a dano por alguns segundos, e os power-ups de velocidade
## e força deixam o herói mais rápido ou com golpe mais forte por alguns segundos.
## Some depois de um tempo no chão, piscando no fim.

signal coletado(tipo: Tipo)

enum Tipo { FRUTA, ERVA, ESCUDO, VELOCIDADE, FORCA }

const CORES: Dictionary = {
	Tipo.FRUTA: Color(0.95, 0.25, 0.35),
	Tipo.ERVA: Color(0.6, 1.0, 0.45),
	Tipo.ESCUDO: Color(0.55, 0.85, 1.0),
	Tipo.VELOCIDADE: Color(1.0, 0.85, 0.2),
	Tipo.FORCA: Color(0.75, 0.4, 1.0),
}

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

@onready var _visual: ColorRect = $Visual


func _ready() -> void:
	_tempo_restante = tempo_no_chao
	_visual.color = CORES[tipo]
	body_entered.connect(_ao_tocar_corpo)


func _process(delta: float) -> void:
	_tempo_restante -= delta
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
