class_name Heroi
extends CharacterBody2D
## Herói guardião da floresta: movimento em 8 direções, dash, ataque corpo a corpo e vida.

signal vida_alterada(atual: int, maxima: int)
signal morreu
signal dano_recebido
signal atacou
signal dash_iniciado

const CENA_GOLPE: PackedScene = preload("res://cenas/heroi/Golpe.tscn")
## Tons aplicados ao visual do herói enquanto um power-up dura (a força tem prioridade).
const TOM_VELOCIDADE: Color = Color(1.6, 1.5, 0.5)
const TOM_FORCA: Color = Color(1.5, 0.7, 1.6)

var velocidade: float = Balanceamento.HEROI_VELOCIDADE
var velocidade_dash: float = Balanceamento.HEROI_VELOCIDADE_DASH
var duracao_dash: float = Balanceamento.HEROI_DURACAO_DASH
var cooldown_dash: float = Balanceamento.HEROI_COOLDOWN_DASH
var dano_ataque: int = Balanceamento.HEROI_DANO_ATAQUE
var cooldown_ataque: float = Balanceamento.HEROI_COOLDOWN_ATAQUE
var distancia_golpe: float = Balanceamento.HEROI_DISTANCIA_GOLPE
var vida_maxima: int = Balanceamento.HEROI_VIDA
var vida_atual: int = Balanceamento.HEROI_VIDA:
	set = _definir_vida
var duracao_invencibilidade: float = Balanceamento.HEROI_INVENCIBILIDADE
var multiplicador_velocidade: float = Balanceamento.ITEM_MULTIPLICADOR_VELOCIDADE
var multiplicador_dano_forca: int = Balanceamento.ITEM_MULTIPLICADOR_DANO_FORCA
var escala_golpe_forca: float = Balanceamento.ITEM_ESCALA_GOLPE_FORCA
@export var intervalo_piscar: float = 0.1

var _direcao_olhar: Vector2 = Vector2.RIGHT
var _direcao_dash: Vector2 = Vector2.ZERO
var _tempo_dash_restante: float = 0.0
var _tempo_cooldown_restante: float = 0.0
var _tempo_cooldown_ataque: float = 0.0
var _tempo_invencivel: float = 0.0
var _tempo_escudo: float = 0.0
var _tempo_velocidade: float = 0.0
var _tempo_forca: float = 0.0

@onready var _visual: AnimatedSprite2D = $Visual
@onready var _indicador_escudo: Line2D = $Escudo


func _physics_process(delta: float) -> void:
	_tempo_cooldown_restante = maxf(_tempo_cooldown_restante - delta, 0.0)
	_tempo_cooldown_ataque = maxf(_tempo_cooldown_ataque - delta, 0.0)
	_atualizar_invencibilidade(delta)
	_atualizar_escudo(delta)
	_atualizar_power_ups(delta)

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
		velocity = direcao * velocidade * (multiplicador_velocidade if tem_velocidade() else 1.0)

	move_and_slide()
	_atualizar_animacao()


## Vira para o lado em que olha e troca entre parado e andando.
func _atualizar_animacao() -> void:
	if _direcao_olhar.x != 0.0:
		_visual.flip_h = _direcao_olhar.x < 0.0
	_visual.play("andando" if velocity != Vector2.ZERO else "parado")


func esta_em_dash() -> bool:
	return _tempo_dash_restante > 0.0


func _pode_dar_dash() -> bool:
	return _tempo_cooldown_restante <= 0.0 and not esta_em_dash()


func _iniciar_dash() -> void:
	_direcao_dash = _direcao_olhar
	_tempo_dash_restante = duracao_dash
	_tempo_cooldown_restante = cooldown_dash
	dash_iniciado.emit()


func _atacar() -> void:
	_tempo_cooldown_ataque = cooldown_ataque
	var direcao: Vector2 = _direcao_do_ataque()
	var golpe: Golpe = CENA_GOLPE.instantiate()
	golpe.dano = dano_ataque
	golpe.position = direcao * distancia_golpe
	golpe.rotation = direcao.angle()
	if tem_forca():
		golpe.dano *= multiplicador_dano_forca
		golpe.scale = Vector2.ONE * escala_golpe_forca
		golpe.position *= escala_golpe_forca
		golpe.modulate = TOM_FORCA
	add_child(golpe)
	atacou.emit()


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


## Pegar outro power-up igual renova a duração, sem somar.
func ativar_velocidade(duracao: float) -> void:
	_tempo_velocidade = maxf(_tempo_velocidade, duracao)


func ativar_forca(duracao: float) -> void:
	_tempo_forca = maxf(_tempo_forca, duracao)


func tem_velocidade() -> bool:
	return _tempo_velocidade > 0.0


func tem_forca() -> bool:
	return _tempo_forca > 0.0


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


## Conta o tempo dos power-ups e tinge o visual do herói enquanto algum dura.
func _atualizar_power_ups(delta: float) -> void:
	_tempo_velocidade = maxf(_tempo_velocidade - delta, 0.0)
	_tempo_forca = maxf(_tempo_forca - delta, 0.0)
	if tem_forca():
		_visual.modulate = TOM_FORCA
	elif tem_velocidade():
		_visual.modulate = TOM_VELOCIDADE
	else:
		_visual.modulate = Color.WHITE
