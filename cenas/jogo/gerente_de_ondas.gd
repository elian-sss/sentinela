class_name GerenteDeOndas
extends Node
## Controla as ondas: faz os inimigos nascerem fora da tela, detecta o fim de cada onda e a vitória.

signal onda_iniciada(numero: int)
signal onda_concluida(numero: int)
signal vitoria

## Uma entrada por onda: quantos inimigos de cada tipo e o intervalo (s) entre um nascimento e outro.
## Numa onda com tipos misturados, a ordem de nascimento é sorteada.
const ONDAS: Array[Dictionary] = [
	{"inimigos": {"lenhador": 5}, "intervalo": 1.5},
	{"inimigos": {"lenhador": 8}, "intervalo": 1.2},
	{"inimigos": {"motosserrista": 10}, "intervalo": 1.0},
	{"inimigos": {"lenhador": 8, "motosserrista": 8}, "intervalo": 0.8},
	{"inimigos": {"lenhador": 1}, "intervalo": 1.0}, # vira o chefe quando ele existir
]
const CENAS_INIMIGO: Dictionary = {
	"lenhador": preload("res://cenas/inimigo/Inimigo.tscn"),
	"motosserrista": preload("res://cenas/inimigo/Motosserrista.tscn"),
}

@export var pausa_entre_ondas: float = 3.0
@export var margem_fora_da_tela: float = 40.0

var _onda_atual: int = 0
var _fila_nascimento: Array[String] = []
var _vivos: int = 0

@onready var _timer_nascimento: Timer = $TimerNascimento
@onready var _timer_pausa: Timer = $TimerPausa


func _ready() -> void:
	_timer_nascimento.timeout.connect(_fazer_nascer_inimigo)
	_timer_pausa.timeout.connect(_iniciar_proxima_onda)
	_iniciar_proxima_onda.call_deferred()


func total_de_ondas() -> int:
	return ONDAS.size()


func onda_atual() -> int:
	return _onda_atual


func _iniciar_proxima_onda() -> void:
	_onda_atual += 1
	var onda: Dictionary = ONDAS[_onda_atual - 1]
	_montar_fila_nascimento(onda["inimigos"])
	onda_iniciada.emit(_onda_atual)
	_timer_nascimento.start(onda["intervalo"])
	_fazer_nascer_inimigo()


## Transforma {"lenhador": 2, "motosserrista": 1} numa fila embaralhada de tipos.
func _montar_fila_nascimento(quantidades: Dictionary) -> void:
	_fila_nascimento.clear()
	for tipo: String in quantidades:
		for i in quantidades[tipo]:
			_fila_nascimento.append(tipo)
	_fila_nascimento.shuffle()


func _fazer_nascer_inimigo() -> void:
	var cena: PackedScene = CENAS_INIMIGO[_fila_nascimento.pop_back()]
	var inimigo: Node2D = cena.instantiate()
	inimigo.position = _posicao_fora_da_tela()
	inimigo.morreu.connect(_ao_inimigo_morrer)
	get_parent().add_child(inimigo)
	_vivos += 1
	if _fila_nascimento.is_empty():
		_timer_nascimento.stop()


## Sorteia um ponto numa das quatro bordas, um pouco além do limite visível.
func _posicao_fora_da_tela() -> Vector2:
	var area: Rect2 = get_viewport().get_visible_rect().grow(margem_fora_da_tela)
	var x: float = randf_range(area.position.x, area.end.x)
	var y: float = randf_range(area.position.y, area.end.y)
	match randi() % 4:
		0:
			return Vector2(x, area.position.y)
		1:
			return Vector2(x, area.end.y)
		2:
			return Vector2(area.position.x, y)
		_:
			return Vector2(area.end.x, y)


func _ao_inimigo_morrer(_posicao: Vector2) -> void:
	_vivos -= 1
	if _vivos == 0 and _fila_nascimento.is_empty():
		_concluir_onda()


func _concluir_onda() -> void:
	onda_concluida.emit(_onda_atual)
	if _onda_atual == ONDAS.size():
		vitoria.emit()
	else:
		_timer_pausa.start(pausa_entre_ondas)
