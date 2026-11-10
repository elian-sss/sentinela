class_name Item
extends Area2D
## Item que cai dos inimigos. A fruta cura o herói, a erva cura a árvore de longe
## e o escudo deixa o herói imune a dano por alguns segundos.
## Some depois de um tempo no chão, piscando no fim.

signal coletado(tipo: Tipo)

enum Tipo { FRUTA, ERVA, ESCUDO }

const CORES: Dictionary = {
	Tipo.FRUTA: Color(0.95, 0.25, 0.35),
	Tipo.ERVA: Color(0.6, 1.0, 0.45),
	Tipo.ESCUDO: Color(0.55, 0.85, 1.0),
}

@export var tipo: Tipo = Tipo.FRUTA
@export var cura_fruta: int = 25
@export var cura_erva: int = 40
@export var duracao_escudo: float = 4.0
@export var tempo_no_chao: float = 8.0
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
