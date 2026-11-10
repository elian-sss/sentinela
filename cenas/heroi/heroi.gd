extends CharacterBody2D
## Herói guardião da floresta: movimento em 8 direções e dash.

@export var velocidade: float = 220.0
@export var velocidade_dash: float = 700.0
@export var duracao_dash: float = 0.15
@export var cooldown_dash: float = 1.5

var _direcao_olhar: Vector2 = Vector2.RIGHT
var _direcao_dash: Vector2 = Vector2.ZERO
var _tempo_dash_restante: float = 0.0
var _tempo_cooldown_restante: float = 0.0


func _physics_process(delta: float) -> void:
	_tempo_cooldown_restante = maxf(_tempo_cooldown_restante - delta, 0.0)

	var direcao: Vector2 = Input.get_vector("mover_esquerda", "mover_direita", "mover_cima", "mover_baixo")
	if direcao != Vector2.ZERO:
		_direcao_olhar = direcao

	if Input.is_action_just_pressed("dash") and _pode_dar_dash():
		_iniciar_dash()

	if esta_em_dash():
		_tempo_dash_restante -= delta
		velocity = _direcao_dash * velocidade_dash
	else:
		velocity = direcao * velocidade

	move_and_slide()


func esta_em_dash() -> bool:
	return _tempo_dash_restante > 0.0


func _pode_dar_dash() -> bool:
	return _tempo_cooldown_restante <= 0.0 and not esta_em_dash()


func _iniciar_dash() -> void:
	_direcao_dash = _direcao_olhar
	_tempo_dash_restante = duracao_dash
	_tempo_cooldown_restante = cooldown_dash
