class_name Heroi
extends CharacterBody2D
## Herói guardião da floresta: movimento em 8 direções, dash, ataque corpo a corpo e vida.

signal vida_alterada(atual: int, maxima: int)
signal morreu
signal dano_recebido

const CENA_GOLPE: PackedScene = preload("res://cenas/heroi/Golpe.tscn")

@export var velocidade: float = 220.0
@export var velocidade_dash: float = 700.0
@export var duracao_dash: float = 0.15
@export var cooldown_dash: float = 1.5
@export var dano_ataque: int = 10
@export var cooldown_ataque: float = 0.3
@export var distancia_golpe: float = 34.0
@export var vida_maxima: int = 100
@export var vida_atual: int = 100:
	set = _definir_vida
@export var duracao_invencibilidade: float = 0.8
@export var intervalo_piscar: float = 0.1

var _direcao_olhar: Vector2 = Vector2.RIGHT
var _direcao_dash: Vector2 = Vector2.ZERO
var _tempo_dash_restante: float = 0.0
var _tempo_cooldown_restante: float = 0.0
var _tempo_cooldown_ataque: float = 0.0
var _tempo_invencivel: float = 0.0
var _tempo_escudo: float = 0.0

@onready var _visual: ColorRect = $Visual
@onready var _indicador_escudo: Line2D = $Escudo


func _physics_process(delta: float) -> void:
	_tempo_cooldown_restante = maxf(_tempo_cooldown_restante - delta, 0.0)
	_tempo_cooldown_ataque = maxf(_tempo_cooldown_ataque - delta, 0.0)
	_atualizar_invencibilidade(delta)
	_atualizar_escudo(delta)

	var direcao: Vector2 = Input.get_vector("mover_esquerda", "mover_direita", "mover_cima", "mover_baixo")
	if direcao != Vector2.ZERO:
		_direcao_olhar = direcao

	if Input.is_action_just_pressed("dash") and _pode_dar_dash():
		_iniciar_dash()

	if Input.is_action_just_pressed("atacar") and _tempo_cooldown_ataque <= 0.0:
		_atacar()

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


func _atacar() -> void:
	_tempo_cooldown_ataque = cooldown_ataque
	var direcao: Vector2 = _direcao_do_ataque()
	var golpe: Golpe = CENA_GOLPE.instantiate()
	golpe.dano = dano_ataque
	golpe.position = direcao * distancia_golpe
	golpe.rotation = direcao.angle()
	add_child(golpe)


## Clique mira no mouse; tecla J ataca na última direção de movimento.
func _direcao_do_ataque() -> Vector2:
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		return global_position.direction_to(get_global_mouse_position())
	return _direcao_olhar


func receber_dano(valor: int) -> void:
	if esta_invencivel() or tem_escudo() or esta_morto():
		return
	vida_atual -= valor
	_tempo_invencivel = duracao_invencibilidade
	dano_recebido.emit()


func curar(valor: int) -> void:
	if esta_morto():
		return
	vida_atual += valor


func esta_invencivel() -> bool:
	return _tempo_invencivel > 0.0


## Fica imune a dano pela duração dada. Pegar outro escudo não encurta o atual.
func ativar_escudo(duracao: float) -> void:
	_tempo_escudo = maxf(_tempo_escudo, duracao)
	_indicador_escudo.show()


func tem_escudo() -> bool:
	return _tempo_escudo > 0.0


func esta_morto() -> bool:
	return vida_atual <= 0


func _definir_vida(valor: int) -> void:
	var anterior: int = vida_atual
	vida_atual = clampi(valor, 0, vida_maxima)
	if vida_atual == anterior:
		return
	vida_alterada.emit(vida_atual, vida_maxima)
	if vida_atual == 0:
		morreu.emit()


## Conta o tempo de invencibilidade e faz o visual piscar enquanto ela dura.
func _atualizar_invencibilidade(delta: float) -> void:
	_tempo_invencivel = maxf(_tempo_invencivel - delta, 0.0)
	if esta_invencivel():
		var fase: int = int(_tempo_invencivel / intervalo_piscar)
		_visual.visible = fase % 2 == 0
	else:
		_visual.visible = true


func _atualizar_escudo(delta: float) -> void:
	if not tem_escudo():
		return
	_tempo_escudo = maxf(_tempo_escudo - delta, 0.0)
	if not tem_escudo():
		_indicador_escudo.hide()
