extends CharacterBody2D
## Lenhador: anda em linha reta até a árvore e a ataca periodicamente.

signal morreu(posicao: Vector2)

const CENA_FUMACA: PackedScene = preload("res://cenas/efeitos/Fumaca.tscn")

@export var vida: int = 30:
	set = _definir_vida
@export var velocidade: float = 60.0
@export var dano: int = 5
@export var intervalo_ataque: float = 1.0
@export var alcance_ataque: float = 56.0
@export var dano_heroi: int = 10
@export var raio_dano_heroi: float = 40.0
@export var intervalo_dano_heroi: float = 1.0

var _arvore: Arvore
var _heroi: Heroi
var _tempo_ate_ataque: float = 0.0
var _tempo_ate_dano_heroi: float = 0.0


func _ready() -> void:
	_arvore = get_tree().get_first_node_in_group("arvore")
	_heroi = get_tree().get_first_node_in_group("heroi")
	_tempo_ate_ataque = intervalo_ataque


func _physics_process(delta: float) -> void:
	_atacar_heroi_se_perto(delta)

	if _arvore == null or _arvore.esta_destruida():
		velocity = Vector2.ZERO
		return

	if global_position.distance_to(_arvore.global_position) > alcance_ataque:
		velocity = global_position.direction_to(_arvore.global_position) * velocidade
		move_and_slide()
	else:
		velocity = Vector2.ZERO
		_atacar_arvore(delta)


func receber_dano(valor: int) -> void:
	vida -= valor


func _atacar_arvore(delta: float) -> void:
	_tempo_ate_ataque -= delta
	if _tempo_ate_ataque <= 0.0:
		_arvore.receber_dano(dano)
		_tempo_ate_ataque = intervalo_ataque


## Enquanto o herói estiver dentro do raio, causa dano a cada intervalo.
func _atacar_heroi_se_perto(delta: float) -> void:
	_tempo_ate_dano_heroi = maxf(_tempo_ate_dano_heroi - delta, 0.0)
	if _heroi == null or _tempo_ate_dano_heroi > 0.0:
		return
	if global_position.distance_to(_heroi.global_position) <= raio_dano_heroi:
		_heroi.receber_dano(dano_heroi)
		_tempo_ate_dano_heroi = intervalo_dano_heroi


func _definir_vida(valor: int) -> void:
	vida = maxi(valor, 0)
	if vida == 0 and is_inside_tree() and not is_queued_for_deletion():
		morreu.emit(global_position)
		_soltar_fumaca()
		queue_free()


func _soltar_fumaca() -> void:
	var fumaca: Node2D = CENA_FUMACA.instantiate()
	get_parent().add_child(fumaca)
	fumaca.global_position = global_position
