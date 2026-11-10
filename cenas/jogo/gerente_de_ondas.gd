class_name GerenteDeOndas
extends Node
## Controla as ondas: faz os inimigos nascerem fora da tela, detecta o fim de cada onda e a vitória.

signal onda_iniciada(numero: int)
signal onda_concluida(numero: int)
signal vitoria
signal inimigo_nasceu(inimigo: Node2D)
signal restantes_alterado(quantidade: int)

## As ondas estão em Balanceamento.ONDAS. Numa onda com tipos misturados, a ordem de nascimento é sorteada.
## O fogo ignora a posição fora da tela e escolhe sozinho um ponto perto da árvore.
const CENAS_INIMIGO: Dictionary = {
	"lenhador": preload("res://cenas/inimigo/Inimigo.tscn"),
	"motosserrista": preload("res://cenas/inimigo/Motosserrista.tscn"),
	"fogo": preload("res://cenas/fogo/Fogo.tscn"),
	"chefe": preload("res://cenas/chefe/Chefe.tscn"),
}

enum Modo { HISTORIA, INFINITO }

## Escolhido na tela inicial. É static para continuar valendo quando a partida é reiniciada.
static var modo: Modo = Modo.HISTORIA

var pausa_entre_ondas: float = Balanceamento.PAUSA_ENTRE_ONDAS
@export var margem_fora_da_tela: float = 40.0

var _onda_atual: int = 0
var _fila_nascimento: Array[String] = []
var _vivos: int = 0
var _derrotados: int = 0

@onready var _timer_nascimento: Timer = $TimerNascimento
@onready var _timer_pausa: Timer = $TimerPausa


func _ready() -> void:
	_timer_nascimento.timeout.connect(_fazer_nascer_inimigo)
	_timer_pausa.timeout.connect(_iniciar_proxima_onda)
	_iniciar_proxima_onda.call_deferred()


static func eh_infinito() -> bool:
	return modo == Modo.INFINITO


func total_de_ondas() -> int:
	return Balanceamento.ONDAS.size()


func onda_atual() -> int:
	return _onda_atual


## Só existe última onda no modo história.
func eh_ultima_onda(numero: int) -> bool:
	return not eh_infinito() and numero == total_de_ondas()


func eh_onda_do_chefe(numero: int) -> bool:
	return _dados_da_onda(numero)["inimigos"].has("chefe")


## Quantos inimigos de cada tipo a onda tem, ex.: {"lenhador": 6, "fogo": 2}.
func inimigos_da_onda(numero: int) -> Dictionary:
	return _dados_da_onda(numero)["inimigos"]


## Inimigos da onda atual que ainda faltam derrotar (os vivos e os que ainda vão nascer).
func inimigos_restantes() -> int:
	return _vivos + _fila_nascimento.size()


## Total de inimigos derrotados na partida (os lenhadores chamados pelo chefe não contam).
func inimigos_derrotados() -> int:
	return _derrotados


func _iniciar_proxima_onda() -> void:
	_onda_atual += 1
	var onda: Dictionary = _dados_da_onda(_onda_atual)
	_montar_fila_nascimento(onda["inimigos"])
	onda_iniciada.emit(_onda_atual)
	restantes_alterado.emit(inimigos_restantes())
	_timer_nascimento.start(onda["intervalo"])
	_fazer_nascer_inimigo()


## No modo infinito, a onda N reusa a onda base da mesma posição no ciclo,
## com mais inimigos e nascimentos mais rápidos a cada ciclo.
func _dados_da_onda(numero: int) -> Dictionary:
	var total: int = total_de_ondas()
	var base: Dictionary = Balanceamento.ONDAS[(numero - 1) % total]
	@warning_ignore("integer_division")
	var ciclo: int = (numero - 1) / total
	if ciclo == 0:
		return base
	var multiplicador: float = 1.0 + ciclo * Balanceamento.INFINITO_AUMENTO_QUANTIDADE_POR_CICLO
	var inimigos: Dictionary = {}
	for tipo: String in base["inimigos"]:
		var quantidade: int = base["inimigos"][tipo]
		inimigos[tipo] = quantidade if tipo == "chefe" else ceili(quantidade * multiplicador)
	if inimigos.has("chefe"):
		inimigos["lenhador"] = inimigos.get("lenhador", 0) + ciclo * Balanceamento.INFINITO_ESCOLTA_CHEFE_POR_CICLO
	var reducao: float = 1.0 - ciclo * Balanceamento.INFINITO_REDUCAO_INTERVALO_POR_CICLO
	var intervalo: float = maxf(base["intervalo"] * reducao, Balanceamento.INFINITO_INTERVALO_MINIMO)
	return {"inimigos": inimigos, "intervalo": intervalo}


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
	inimigo_nasceu.emit(inimigo)
	restantes_alterado.emit(inimigos_restantes())
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
	_derrotados += 1
	restantes_alterado.emit(inimigos_restantes())
	if _vivos == 0 and _fila_nascimento.is_empty():
		_concluir_onda()


func _concluir_onda() -> void:
	onda_concluida.emit(_onda_atual)
	if eh_ultima_onda(_onda_atual):
		vitoria.emit()
	else:
		_timer_pausa.start(pausa_entre_ondas)
