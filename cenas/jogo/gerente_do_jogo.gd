class_name GerenteDoJogo
extends Node
## Escuta a árvore, o herói e as ondas e decide quando a partida termina.
## Também guarda o tempo de partida e o motivo da derrota, para a tela final.

signal derrota(onda: int)
signal vitoria

enum Motivo { NENHUM, ARVORE_CAIU, HEROI_CAIU }

const CENA_ITEM: PackedScene = preload("res://cenas/item/Item.tscn")

@export var arvore: Arvore
@export var heroi: Heroi
@export var gerente_de_ondas: GerenteDeOndas

var motivo_da_derrota: Motivo = Motivo.NENHUM
var tempo_de_partida: float = 0.0

var _partida_encerrada: bool = false


func _ready() -> void:
	arvore.destruida.connect(_perder.bind(Motivo.ARVORE_CAIU))
	heroi.morreu.connect(_perder.bind(Motivo.HEROI_CAIU))
	gerente_de_ondas.vitoria.connect(_vencer)
	gerente_de_ondas.onda_concluida.connect(_regenerar_arvore)
	gerente_de_ondas.onda_concluida.connect(_soltar_frutas)


func _process(delta: float) -> void:
	if not _partida_encerrada:
		tempo_de_partida += delta


func _perder(motivo: Motivo) -> void:
	if _partida_encerrada:
		return
	_partida_encerrada = true
	motivo_da_derrota = motivo
	derrota.emit(gerente_de_ondas.onda_atual())


## Ao fim de cada onda, menos a última, a árvore recupera uma parte da vida.
func _regenerar_arvore(onda: int) -> void:
	if not gerente_de_ondas.eh_ultima_onda(onda):
		arvore.curar(int(arvore.vida_maxima * Balanceamento.ARVORE_REGENERACAO_ENTRE_ONDAS))


## Ao fim de cada onda, menos a última, caem frutas perto da árvore para o herói se curar na pausa.
func _soltar_frutas(onda: int) -> void:
	if gerente_de_ondas.eh_ultima_onda(onda):
		return
	for i in Balanceamento.FRUTAS_FIM_DE_ONDA:
		var fruta: Item = CENA_ITEM.instantiate()
		fruta.tipo = Item.Tipo.FRUTA
		# Ângulo entre 20° e 160°: sempre abaixo da árvore, onde a copa não esconde.
		var angulo: float = deg_to_rad(randf_range(20.0, 160.0))
		fruta.position = arvore.global_position + Vector2.from_angle(angulo) * Balanceamento.FRUTAS_FIM_DE_ONDA_DISTANCIA
		# Adiado: a onda termina dentro do callback de morte de um inimigo, onde não dá para criar áreas.
		get_parent().add_child.call_deferred(fruta)


func _vencer() -> void:
	if _partida_encerrada:
		return
	_partida_encerrada = true
	vitoria.emit()
