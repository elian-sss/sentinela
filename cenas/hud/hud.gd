class_name HUD
extends CanvasLayer
## Interface da partida: vida do herói, vida da árvore e onda atual.
## Atualiza só quando recebe os signals, sem consultar nada a cada frame.

@export var heroi: Heroi
@export var arvore: Arvore

@onready var _barra_heroi: ProgressBar = $PainelHeroi/BarraVida
@onready var _barra_arvore: ProgressBar = $PainelArvore/BarraVida
@onready var _rotulo_onda: Label = $RotuloOnda


func _ready() -> void:
	heroi.vida_alterada.connect(_atualizar_barra.bind(_barra_heroi))
	arvore.vida_alterada.connect(_atualizar_barra.bind(_barra_arvore))
	_atualizar_barra(heroi.vida_atual, heroi.vida_maxima, _barra_heroi)
	_atualizar_barra(arvore.vida_atual, arvore.vida_maxima, _barra_arvore)


func atualizar_onda(atual: int, total: int) -> void:
	_rotulo_onda.text = "Onda %d/%d" % [atual, total]


func _atualizar_barra(atual: int, maxima: int, barra: ProgressBar) -> void:
	barra.max_value = maxima
	barra.value = atual
