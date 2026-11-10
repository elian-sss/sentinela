class_name Arvore
extends StaticBody2D
## A Samaúma, mãe das árvores, que o Sentinela protege. Se a vida chegar a zero, o jogo é perdido.
## O desenho muda com a saúde: copa cheia, copa rala e, por um fio, galhos secos à mostra.

signal vida_alterada(atual: int, maxima: int)
signal destruida
signal dano_recebido
signal curada(valor: int)
signal estado_alterado(estado: Estado)

enum Estado { SAUDAVEL, FERIDA, CRITICA }

## Fração de vida abaixo da qual a Samaúma passa a cada estado.
const LIMITE_FERIDA: float = 0.6
const LIMITE_CRITICA: float = 0.3
const TREMOR_AO_SER_ATINGIDA: float = 3.0 ## pixels que o desenho balança
const DURACAO_TREMOR: float = 0.18

var vida_maxima: int = Balanceamento.ARVORE_VIDA
var vida_atual: int = Balanceamento.ARVORE_VIDA:
	set = _definir_vida

var _estado: Estado = Estado.SAUDAVEL
var _tween_tremor: Tween

@onready var _visual: Sprite2D = $Visual
@onready var _folhas: CPUParticles2D = $Folhas
@onready var _cura: CPUParticles2D = $Cura
@onready var _posicao_visual: Vector2 = $Visual.position


func receber_dano(valor: int) -> void:
	var anterior: int = vida_atual
	vida_atual -= valor
	if vida_atual < anterior:
		_folhas.restart()
		_tremer()
		dano_recebido.emit()


func curar(valor: int) -> void:
	var anterior: int = vida_atual
	vida_atual += valor
	if vida_atual > anterior:
		_cura.restart()
		Feedback.numero(self, "+%d" % (vida_atual - anterior), Feedback.COR_CURA_ARVORE)
		curada.emit(vida_atual - anterior)


func esta_destruida() -> bool:
	return vida_atual <= 0


func estado() -> Estado:
	return _estado


func fracao_de_vida() -> float:
	return float(vida_atual) / vida_maxima


func _definir_vida(valor: int) -> void:
	var anterior: int = vida_atual
	vida_atual = clampi(valor, 0, vida_maxima)
	if vida_atual == anterior:
		return
	vida_alterada.emit(vida_atual, vida_maxima)
	_atualizar_estado()
	if vida_atual == 0:
		destruida.emit()


func _atualizar_estado() -> void:
	var novo: Estado = Estado.SAUDAVEL
	if fracao_de_vida() < LIMITE_CRITICA:
		novo = Estado.CRITICA
	elif fracao_de_vida() < LIMITE_FERIDA:
		novo = Estado.FERIDA
	if novo == _estado:
		return
	_estado = novo
	if is_node_ready():
		_visual.frame = novo
	estado_alterado.emit(novo)


## Balança o desenho de um lado para o outro quando leva uma pancada.
func _tremer() -> void:
	if _tween_tremor:
		_tween_tremor.kill()
	_tween_tremor = create_tween()
	for desvio: float in [TREMOR_AO_SER_ATINGIDA, -TREMOR_AO_SER_ATINGIDA, 0.0]:
		_tween_tremor.tween_property(_visual, "position:x", _posicao_visual.x + desvio, DURACAO_TREMOR / 3.0)
