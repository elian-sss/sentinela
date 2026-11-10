class_name GerenteDoJogo
extends Node
## Escuta a árvore e o herói e decide quando a partida termina.

signal derrota

@export var arvore: Arvore
@export var heroi: Heroi

var _partida_encerrada: bool = false


func _ready() -> void:
	arvore.destruida.connect(_perder)
	heroi.morreu.connect(_perder)
	derrota.connect(_reiniciar)


func _perder() -> void:
	if _partida_encerrada:
		return
	_partida_encerrada = true
	derrota.emit()


## Provisório: até existir a tela de derrota, só recarrega a cena.
func _reiniciar() -> void:
	get_tree().reload_current_scene.call_deferred()
