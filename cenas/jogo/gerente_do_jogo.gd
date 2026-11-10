class_name GerenteDoJogo
extends Node
## Escuta a árvore, o herói e as ondas e decide quando a partida termina.

signal derrota(onda: int)
signal vitoria

@export var arvore: Arvore
@export var heroi: Heroi
@export var gerente_de_ondas: GerenteDeOndas

var _partida_encerrada: bool = false


func _ready() -> void:
	arvore.destruida.connect(_perder)
	heroi.morreu.connect(_perder)
	gerente_de_ondas.vitoria.connect(_vencer)
	gerente_de_ondas.onda_concluida.connect(_regenerar_arvore)


func _perder() -> void:
	if _partida_encerrada:
		return
	_partida_encerrada = true
	derrota.emit(gerente_de_ondas.onda_atual())


## Ao fim de cada onda, menos a última, a árvore recupera uma parte da vida.
func _regenerar_arvore(onda: int) -> void:
	if not gerente_de_ondas.eh_ultima_onda(onda):
		arvore.curar(int(arvore.vida_maxima * Balanceamento.ARVORE_REGENERACAO_ENTRE_ONDAS))


func _vencer() -> void:
	if _partida_encerrada:
		return
	_partida_encerrada = true
	vitoria.emit()
