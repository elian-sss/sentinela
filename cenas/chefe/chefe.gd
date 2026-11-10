class_name Chefe
extends CharacterBody2D
## Escavadeira, chefe da onda 5. Ciclo: avança devagar → para e pisca com uma linha de aviso →
## investe em linha reta até bater numa borda → fica atordoada e leva dano multiplicado.
## A investida passa por cima da árvore sem parar, então o atordoamento sempre acontece longe dela.
## De tempos em tempos invoca lenhadores ao redor. Ao ser derrotada, desmonta em fumaça antes de sumir.

signal vida_alterada(atual: int, maxima: int)
signal morreu(posicao: Vector2)
signal investiu
signal estado_alterado(estado: Estado)

enum Estado { AVANCANDO, AVISANDO, INVESTINDO, ATORDOADO, DERROTADO }

const CENA_FUMACA: PackedScene = preload("res://cenas/efeitos/Fumaca.tscn")
const CENA_LENHADOR: PackedScene = preload("res://cenas/inimigo/Inimigo.tscn")
const COMPRIMENTO_LINHA_AVISO: float = 2000.0
const COR_ATORDOADO: Color = Color(0.5, 0.7, 1.0)
const COR_DERROTADO: Color = Color(0.45, 0.42, 0.4)
const FRACAO_FUMACA_DE_DANO: float = 0.5 ## abaixo dessa fração de vida o motor solta fumaça escura
const TEMPO_DESMONTANDO: float = 1.4 ## quanto dura a queda antes de sumir
const INTERVALO_FUMACA_DERROTA: float = 0.2
const TREMOR_DERROTA: float = 3.0 ## pixels que o desenho chacoalha enquanto desmonta

var vida_maxima: int = Balanceamento.CHEFE_VIDA
var velocidade_avanco: float = Balanceamento.CHEFE_VELOCIDADE_AVANCO
var tempo_avanco: float = Balanceamento.CHEFE_TEMPO_AVANCO
var tempo_aviso: float = Balanceamento.CHEFE_TEMPO_AVISO
@export var intervalo_piscar_aviso: float = 0.1
var velocidade_investida: float = Balanceamento.CHEFE_VELOCIDADE_INVESTIDA
var tempo_atordoado: float = Balanceamento.CHEFE_TEMPO_ATORDOADO
var multiplicador_dano_atordoado: int = Balanceamento.CHEFE_MULTIPLICADOR_DANO_ATORDOADO
var dano_contato_heroi: int = Balanceamento.CHEFE_DANO_CONTATO_HEROI
var dano_investida_heroi: int = Balanceamento.CHEFE_DANO_INVESTIDA_HEROI
var raio_contato_heroi: float = Balanceamento.CHEFE_RAIO_CONTATO_HEROI
var dano_arvore: int = Balanceamento.CHEFE_DANO_ARVORE
var intervalo_ataque_arvore: float = Balanceamento.CHEFE_INTERVALO_ATAQUE_ARVORE
var raio_contato_arvore: float = Balanceamento.CHEFE_RAIO_CONTATO_ARVORE
@export var area_arena: Rect2 = Rect2(0, 0, 1152, 648) ## bordas onde a investida termina
@export var margem_borda: float = 48.0 ## metade do tamanho: a investida para quando a lateral encosta na borda
var intervalo_invocacao: float = Balanceamento.CHEFE_INTERVALO_INVOCACAO
var lenhadores_por_invocacao: int = Balanceamento.CHEFE_LENHADORES_POR_INVOCACAO
var distancia_invocacao: float = Balanceamento.CHEFE_DISTANCIA_INVOCACAO

var vida_atual: int = 0
var _estado: Estado = Estado.AVANCANDO
var _tempo_no_estado: float = 0.0
var _direcao_investida: Vector2 = Vector2.ZERO
var _tempo_ate_ataque_arvore: float = 0.0
var _tempo_ate_invocacao: float = 0.0
var _tempo_ate_fumaca: float = 0.0
var _arvore: Arvore
var _heroi: Heroi

@onready var _visual: AnimatedSprite2D = $Visual
@onready var _linha_aviso: Line2D = $LinhaAviso
@onready var _alerta: Label = $Alerta
@onready var _estrelas: CPUParticles2D = $Estrelas
@onready var _fumaca_dano: CPUParticles2D = $FumacaDano


func _ready() -> void:
	_arvore = get_tree().get_first_node_in_group("arvore")
	_heroi = get_tree().get_first_node_in_group("heroi")
	vida_atual = vida_maxima
	_tempo_ate_ataque_arvore = intervalo_ataque_arvore
	_tempo_ate_invocacao = intervalo_invocacao
	_mudar_estado(Estado.AVANCANDO)


func _physics_process(delta: float) -> void:
	_tempo_no_estado += delta
	match _estado:
		Estado.AVANCANDO:
			_avancar(delta)
		Estado.AVISANDO:
			_avisar()
		Estado.INVESTINDO:
			_investir()
		Estado.ATORDOADO:
			if _tempo_no_estado >= tempo_atordoado:
				_mudar_estado(Estado.AVANCANDO)
		Estado.DERROTADO:
			_desmontar(delta)
			return
	_contar_invocacao(delta)
	_ferir_heroi_se_encostar()
	_atualizar_animacao()


## As esteiras só giram quando a escavadeira se move. O braço aponta para onde ela vai.
func _atualizar_animacao() -> void:
	if velocity.x != 0.0:
		_visual.flip_h = velocity.x < 0.0
	if velocity == Vector2.ZERO:
		_visual.pause()
	else:
		_visual.play("andando")


func receber_dano(valor: int) -> void:
	if vida_atual <= 0:
		return
	var forte: bool = _estado == Estado.ATORDOADO
	if forte:
		valor *= multiplicador_dano_atordoado
	vida_atual = maxi(vida_atual - valor, 0)
	vida_alterada.emit(vida_atual, vida_maxima)
	Feedback.piscar_branco(self, _visual)
	Feedback.numero(self, str(valor), Feedback.COR_DANO_FORTE if forte else Feedback.COR_DANO, forte)
	_fumaca_dano.emitting = vida_atual < vida_maxima * FRACAO_FUMACA_DE_DANO
	if vida_atual == 0:
		_mudar_estado(Estado.DERROTADO)


func esta_atordoado() -> bool:
	return _estado == Estado.ATORDOADO


func estado() -> Estado:
	return _estado


func _avancar(delta: float) -> void:
	if _tempo_no_estado >= tempo_avanco:
		_mudar_estado(Estado.AVISANDO)
	elif _distancia_arvore() > raio_contato_arvore:
		velocity = global_position.direction_to(_arvore.global_position) * velocidade_avanco
		move_and_slide()
	else:
		_atacar_arvore(delta)


func _atacar_arvore(delta: float) -> void:
	_tempo_ate_ataque_arvore -= delta
	if _tempo_ate_ataque_arvore <= 0.0:
		_arvore.receber_dano(dano_arvore)
		_tempo_ate_ataque_arvore = intervalo_ataque_arvore


## Pisca o desenho e pulsa a linha de aviso até a hora de investir.
func _avisar() -> void:
	var aceso: bool = int(_tempo_no_estado / intervalo_piscar_aviso) % 2 == 0
	_visual.visible = aceso
	_linha_aviso.modulate.a = 1.0 if aceso else 0.6
	if _tempo_no_estado >= tempo_aviso:
		_mudar_estado(Estado.INVESTINDO)


func _investir() -> void:
	velocity = _direcao_investida * velocidade_investida
	move_and_slide()
	if _bateu_na_borda():
		Feedback.tremer(get_tree(), true)
		_mudar_estado(Estado.ATORDOADO)


func _mudar_estado(novo: Estado) -> void:
	_estado = novo
	_tempo_no_estado = 0.0
	velocity = Vector2.ZERO
	_visual.visible = true
	_visual.modulate = _cor_do_estado(novo)
	_linha_aviso.visible = novo == Estado.AVISANDO
	_alerta.visible = novo == Estado.AVISANDO
	_estrelas.emitting = novo == Estado.ATORDOADO
	if novo == Estado.AVISANDO:
		_mirar_no_heroi()
	elif novo == Estado.INVESTINDO:
		investiu.emit()
	elif novo == Estado.DERROTADO:
		_visual.pause()
		_fumaca_dano.emitting = true
	estado_alterado.emit(novo)


func _cor_do_estado(qual: Estado) -> Color:
	match qual:
		Estado.ATORDOADO:
			return COR_ATORDOADO
		Estado.DERROTADO:
			return COR_DERROTADO
	return Color.WHITE


## Trava a direção da investida no herói e desenha a linha de aviso nessa direção.
func _mirar_no_heroi() -> void:
	_direcao_investida = global_position.direction_to(_heroi.global_position)
	if _direcao_investida == Vector2.ZERO:
		_direcao_investida = Vector2.RIGHT
	_visual.flip_h = _direcao_investida.x < 0.0
	_linha_aviso.points = PackedVector2Array([Vector2.ZERO, _direcao_investida * COMPRIMENTO_LINHA_AVISO])


func _distancia_arvore() -> float:
	return global_position.distance_to(_arvore.global_position)


## Só conta como batida se estiver saindo da arena (entrando, vindo de fora, não conta).
func _bateu_na_borda() -> bool:
	var limites: Rect2 = area_arena.grow(-margem_borda)
	if limites.has_point(global_position):
		return false
	if _direcao_investida.dot(limites.get_center() - global_position) >= 0.0:
		return false
	global_position = global_position.clamp(limites.position, limites.end)
	return true


func _ferir_heroi_se_encostar() -> void:
	if _estado == Estado.ATORDOADO:
		return
	if global_position.distance_to(_heroi.global_position) <= raio_contato_heroi:
		var dano: int = dano_investida_heroi if _estado == Estado.INVESTINDO else dano_contato_heroi
		_heroi.receber_dano(dano)


func _contar_invocacao(delta: float) -> void:
	_tempo_ate_invocacao -= delta
	if _tempo_ate_invocacao > 0.0:
		return
	_tempo_ate_invocacao = intervalo_invocacao
	for i in lenhadores_por_invocacao:
		var lenhador: Node2D = CENA_LENHADOR.instantiate()
		lenhador.position = global_position + Vector2.from_angle(randf() * TAU) * distancia_invocacao
		get_parent().add_child(lenhador)


## Derrotada: chacoalha soltando fumaça por um instante e só então some e avisa que morreu.
func _desmontar(delta: float) -> void:
	_visual.offset = Vector2(randf_range(-TREMOR_DERROTA, TREMOR_DERROTA), randf_range(-TREMOR_DERROTA, TREMOR_DERROTA))
	_tempo_ate_fumaca -= delta
	if _tempo_ate_fumaca <= 0.0:
		_tempo_ate_fumaca = INTERVALO_FUMACA_DERROTA
		_soltar_fumaca(Vector2(randf_range(-40.0, 40.0), randf_range(-40.0, 20.0)), 1.5)
	if _tempo_no_estado >= TEMPO_DESMONTANDO:
		_sumir()


func _sumir() -> void:
	Feedback.tremer(get_tree(), true)
	_soltar_fumaca(Vector2.ZERO, 3.0)
	morreu.emit(global_position)
	queue_free()


func _soltar_fumaca(desvio: Vector2, escala: float) -> void:
	var fumaca: Node2D = CENA_FUMACA.instantiate()
	fumaca.scale = Vector2.ONE * escala
	get_parent().add_child(fumaca)
	fumaca.global_position = global_position + desvio
