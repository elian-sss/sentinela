class_name Heroi
extends CharacterBody2D
## O Sentinela, guardião da floresta: movimento em 8 direções, dash, ataque corpo a corpo e vida.

signal vida_alterada(atual: int, maxima: int)
signal morreu
signal dano_recebido
signal curado(valor: int)
signal atacou
signal dash_iniciado
signal dash_pronto

const CENA_GOLPE: PackedScene = preload("res://cenas/heroi/Golpe.tscn")
## Tons aplicados ao visual do herói enquanto um power-up dura (a força tem prioridade).
const TOM_VELOCIDADE: Color = Color(1.6, 1.5, 0.5)
const TOM_FORCA: Color = Color(1.5, 0.7, 1.6)
const DURACAO_POSE_ATAQUE: float = 0.18 ## tempo em que o sprite fica na pose de golpe
const INTERVALO_RASTRO: float = 0.03 ## a cada quanto tempo o dash deixa uma imagem para trás
const DURACAO_RASTRO: float = 0.25
const COR_RASTRO: Color = Color(1.0, 0.65, 0.25, 0.6)

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
var _tempo_pose_ataque: float = 0.0
var _tempo_ate_rastro: float = 0.0
## Tempo restante e duração total de cada efeito temporário: "escudo", "velocidade" e "forca".
var _efeitos: Dictionary = {"escudo": 0.0, "velocidade": 0.0, "forca": 0.0}
var _duracoes: Dictionary = {"escudo": 1.0, "velocidade": 1.0, "forca": 1.0}

@onready var _visual: AnimatedSprite2D = $Visual
@onready var _indicador_escudo: Line2D = $Escudo


func _physics_process(delta: float) -> void:
	_atualizar_cooldowns(delta)
	_atualizar_invencibilidade(delta)
	_atualizar_efeitos(delta)

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
		_deixar_rastro(delta)
	else:
		velocity = direcao * velocidade * (multiplicador_velocidade if tem_velocidade() else 1.0)

	move_and_slide()
	_atualizar_animacao()


func _atualizar_cooldowns(delta: float) -> void:
	_tempo_cooldown_ataque = maxf(_tempo_cooldown_ataque - delta, 0.0)
	_tempo_pose_ataque = maxf(_tempo_pose_ataque - delta, 0.0)
	if _tempo_cooldown_restante > 0.0:
		_tempo_cooldown_restante = maxf(_tempo_cooldown_restante - delta, 0.0)
		if _tempo_cooldown_restante == 0.0:
			dash_pronto.emit()


## Vira para o lado em que olha (ou em que acabou de golpear) e escolhe a animação.
func _atualizar_animacao() -> void:
	if _tempo_pose_ataque > 0.0:
		return
	if _direcao_olhar.x != 0.0:
		_visual.flip_h = _direcao_olhar.x < 0.0
	_visual.play("andando" if velocity != Vector2.ZERO else "parado")


func esta_em_dash() -> bool:
	return _tempo_dash_restante > 0.0


## 0 logo depois do dash, 1 quando ele está pronto de novo. A HUD usa para a barrinha do dash.
func fracao_dash() -> float:
	return 1.0 - _tempo_cooldown_restante / cooldown_dash


func _pode_dar_dash() -> bool:
	return _tempo_cooldown_restante <= 0.0 and not esta_em_dash()


func _iniciar_dash() -> void:
	_direcao_dash = _direcao_olhar
	_tempo_dash_restante = duracao_dash
	_tempo_cooldown_restante = cooldown_dash
	_tempo_ate_rastro = 0.0
	dash_iniciado.emit()


## Deixa cópias do sprite que somem, formando um rastro de fogo atrás do dash.
func _deixar_rastro(delta: float) -> void:
	if not Feedback.RASTRO_DO_DASH:
		return
	_tempo_ate_rastro -= delta
	if _tempo_ate_rastro > 0.0:
		return
	_tempo_ate_rastro = INTERVALO_RASTRO
	var copia := Sprite2D.new()
	copia.texture = _visual.sprite_frames.get_frame_texture(_visual.animation, _visual.frame)
	copia.flip_h = _visual.flip_h
	copia.scale = _visual.scale
	copia.modulate = COR_RASTRO
	copia.position = global_position + _visual.position
	get_parent().add_child(copia)
	var tween: Tween = copia.create_tween()
	tween.tween_property(copia, "modulate:a", 0.0, DURACAO_RASTRO)
	tween.tween_callback(copia.queue_free)


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
	_fazer_pose_de_ataque(direcao)
	atacou.emit()


func _fazer_pose_de_ataque(direcao: Vector2) -> void:
	_tempo_pose_ataque = DURACAO_POSE_ATAQUE
	if direcao.x != 0.0:
		_visual.flip_h = direcao.x < 0.0
	_visual.play("atacando")


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
	Feedback.piscar_branco(self, _visual, Feedback.BRILHO_DANO_HEROI)
	dano_recebido.emit()


func curar(valor: int) -> void:
	if esta_morto():
		return
	var antes: int = vida_atual
	vida_atual += valor
	if vida_atual > antes:
		Feedback.numero(self, "+%d" % (vida_atual - antes), Feedback.COR_CURA_HEROI)
		curado.emit(vida_atual - antes)


func esta_invencivel() -> bool:
	return _tempo_invencivel > 0.0


## Fica imune a dano pela duração dada. Pegar outro escudo não encurta o atual.
func ativar_escudo(duracao: float) -> void:
	_ativar_efeito("escudo", duracao)
	_indicador_escudo.show()


## Pegar outro power-up igual renova a duração, sem somar.
func ativar_velocidade(duracao: float) -> void:
	_ativar_efeito("velocidade", duracao)


func ativar_forca(duracao: float) -> void:
	_ativar_efeito("forca", duracao)


func tem_escudo() -> bool:
	return _efeitos["escudo"] > 0.0


func tem_velocidade() -> bool:
	return _efeitos["velocidade"] > 0.0


func tem_forca() -> bool:
	return _efeitos["forca"] > 0.0


## Quanto resta do efeito, de 1 (acabou de pegar) a 0 (acabou). A HUD usa para as barrinhas.
func fracao_do_efeito(nome: String) -> float:
	return _efeitos[nome] / _duracoes[nome]


func esta_morto() -> bool:
	return vida_atual <= 0


func _ativar_efeito(nome: String, duracao: float) -> void:
	_efeitos[nome] = maxf(_efeitos[nome], duracao)
	_duracoes[nome] = maxf(_efeitos[nome], 0.01)


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


## Conta o tempo do escudo e dos power-ups e tinge o visual do herói enquanto algum power-up dura.
func _atualizar_efeitos(delta: float) -> void:
	for nome: String in _efeitos:
		_efeitos[nome] = maxf(_efeitos[nome] - delta, 0.0)
	_indicador_escudo.visible = tem_escudo()
	if tem_forca():
		_visual.modulate = TOM_FORCA
	elif tem_velocidade():
		_visual.modulate = TOM_VELOCIDADE
	else:
		_visual.modulate = Color.WHITE
