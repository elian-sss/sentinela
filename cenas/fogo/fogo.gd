class_name Fogo
extends Area2D
## Foco de fogo: nasce perto da árvore, cresce devagar e queima a árvore quando o alcance chega nela.
## O herói apaga com alguns golpes.

signal morreu(posicao: Vector2)

const CENA_FUMACA: PackedScene = preload("res://cenas/efeitos/Fumaca.tscn")

@export var vida: int = 30
@export var dano: int = 4
@export var intervalo_dano: float = 1.0
@export var raio_inicial: float = 16.0
@export var raio_maximo: float = 64.0
@export var velocidade_crescimento: float = 3.0 ## pixels de raio por segundo
@export var alcance_dano_arvore: float = 40.0 ## distância além da borda do fogo que ainda queima a árvore
@export var distancia_minima_arvore: float = 60.0
@export var distancia_maxima_arvore: float = 100.0

var _arvore: Arvore
var _raio: float = 0.0
var _tempo_ate_dano: float = 0.0

@onready var _forma: CircleShape2D = $Colisao.shape
@onready var _visual: ColorRect = $Visual


## O fogo escolhe sozinho onde nascer, num ponto aleatório em volta da árvore.
func _ready() -> void:
	_arvore = get_tree().get_first_node_in_group("arvore")
	_tempo_ate_dano = intervalo_dano
	var distancia: float = randf_range(distancia_minima_arvore, distancia_maxima_arvore)
	global_position = _arvore.global_position + Vector2.from_angle(randf() * TAU) * distancia
	_definir_raio(raio_inicial)


func _physics_process(delta: float) -> void:
	if _arvore.esta_destruida():
		return
	_definir_raio(minf(_raio + velocidade_crescimento * delta, raio_maximo))
	_queimar_arvore_se_perto(delta)


func receber_dano(valor: int) -> void:
	if vida <= 0:
		return
	vida -= valor
	if vida <= 0:
		_apagar()


func _queimar_arvore_se_perto(delta: float) -> void:
	if global_position.distance_to(_arvore.global_position) > _raio + alcance_dano_arvore:
		return
	_tempo_ate_dano -= delta
	if _tempo_ate_dano <= 0.0:
		_arvore.receber_dano(dano)
		_tempo_ate_dano = intervalo_dano


func _definir_raio(valor: float) -> void:
	_raio = valor
	_forma.radius = valor
	_visual.size = Vector2.ONE * valor * 2.0
	_visual.position = -Vector2.ONE * valor


func _apagar() -> void:
	morreu.emit(global_position)
	var fumaca: Node2D = CENA_FUMACA.instantiate()
	get_parent().add_child(fumaca)
	fumaca.global_position = global_position
	queue_free()
