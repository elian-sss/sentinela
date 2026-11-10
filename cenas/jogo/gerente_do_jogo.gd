class_name GerenteDoJogo
extends Node
## Escuta a árvore, o herói e as ondas e decide quando a partida termina.

signal derrota

@export var arvore: Arvore
@export var heroi: Heroi
@export var gerente_de_ondas: GerenteDeOndas

var _partida_encerrada: bool = false


func _ready() -> void:
	arvore.destruida.connect(_perder)
	heroi.morreu.connect(_perder)
	gerente_de_ondas.vitoria.connect(_vencer)
	derrota.connect(_reiniciar)


func _perder() -> void:
	if _partida_encerrada:
		return
	_partida_encerrada = true
	derrota.emit()


## Provisório: até existir a tela de vitória, só impede que uma derrota posterior reinicie a cena.
func _vencer() -> void:
	_partida_encerrada = true


## Provisório: até existir a tela de derrota, só recarrega a cena.
func _reiniciar() -> void:
	get_tree().reload_current_scene.call_deferred()
