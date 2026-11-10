class_name Item
extends Area2D
## Item que cai dos inimigos. A fruta cura o herói, a erva cura a árvore de longe,
## o escudo deixa o herói imune a dano por alguns segundos, e os power-ups de velocidade
## e força deixam o herói mais rápido ou com golpe mais forte por alguns segundos.
## Some depois de um tempo no chão, piscando no fim.

signal coletado(tipo: Tipo)

enum Tipo { FRUTA, ERVA, ESCUDO, VELOCIDADE, FORCA }

const TEXTURAS: Dictionary = {
	Tipo.FRUTA: preload("res://assets/personagens/item_fruta.png"),
	Tipo.ERVA: preload("res://assets/personagens/item_erva.png"),
	Tipo.ESCUDO: preload("res://assets/personagens/item_escudo.png"),
	Tipo.VELOCIDADE: preload("res://assets/personagens/item_velocidade.png"),
	Tipo.FORCA: preload("res://assets/personagens/item_forca.png"),
}
## Cor do brilho e das faíscas de cada item, a mesma que identifica o item.
const CORES_BRILHO: Dictionary = {
	Tipo.FRUTA: Color(1.0, 0.3, 0.3),
	Tipo.ERVA: Color(0.5, 1.0, 0.4),
	Tipo.ESCUDO: Color(0.45, 0.8, 1.0),
	Tipo.VELOCIDADE: Color(1.0, 0.85, 0.25),
	Tipo.FORCA: Color(0.8, 0.45, 1.0),
}
const ALTURA_FLUTUAR: float = 5.0 ## pixels que o item sobe e desce no ar
const VELOCIDADE_FLUTUAR: float = 3.0
const BRILHO_MINIMO: float = 0.45 ## o brilho pulsa entre este alfa e 1
const ESCALA_BRILHO: float = 0.9

@export var tipo: Tipo = Tipo.FRUTA
var cura_fruta: int = Balanceamento.ITEM_CURA_FRUTA
var cura_erva: int = Balanceamento.ITEM_CURA_ERVA
var duracao_escudo: float = Balanceamento.ITEM_DURACAO_ESCUDO
var duracao_velocidade: float = Balanceamento.ITEM_DURACAO_VELOCIDADE
var duracao_forca: float = Balanceamento.ITEM_DURACAO_FORCA
var tempo_no_chao: float = Balanceamento.ITEM_TEMPO_NO_CHAO
@export var tempo_piscando: float = 3.0
@export var intervalo_piscar: float = 0.15

var _tempo_restante: float = 0.0

var _altura_base: float = 0.0

@onready var _visual: Sprite2D = $Flutuante/Visual
@onready var _flutuante: Node2D = $Flutuante
@onready var _brilho: Sprite2D = $Flutuante/Brilho
@onready var _faiscas: CPUParticles2D = $Flutuante/Faiscas
@onready var _sombra: Sprite2D = $Sombra


func _ready() -> void:
	_tempo_restante = tempo_no_chao
	_visual.texture = TEXTURAS[tipo]
	_brilho.modulate = CORES_BRILHO[tipo]
	_faiscas.color = CORES_BRILHO[tipo]
	_altura_base = _flutuante.position.y
	body_entered.connect(_ao_tocar_corpo)


func _process(delta: float) -> void:
	_tempo_restante -= delta
	_animar_flutuacao()
	if _tempo_restante <= 0.0:
		queue_free()
	elif _tempo_restante <= tempo_piscando:
		var aparece: bool = int(_tempo_restante / intervalo_piscar) % 2 == 0
		_flutuante.visible = aparece
		_sombra.visible = aparece


## Sobe e desce no ar com o brilho pulsando. A sombra no chão encolhe quando o item sobe.
func _animar_flutuacao() -> void:
	var onda: float = sin(_tempo_restante * VELOCIDADE_FLUTUAR)
	_flutuante.position.y = _altura_base + onda * ALTURA_FLUTUAR
	_sombra.scale = Vector2.ONE * (0.85 + onda * 0.15)
	_brilho.modulate.a = lerpf(BRILHO_MINIMO, 1.0, (sin(_tempo_restante * VELOCIDADE_FLUTUAR * 2.0) + 1.0) / 2.0)
	_brilho.scale = Vector2.ONE * ESCALA_BRILHO


func _ao_tocar_corpo(corpo: Node2D) -> void:
	if corpo is Heroi:
		_aplicar_efeito(corpo)
		coletado.emit(tipo)
		queue_free()


func _aplicar_efeito(heroi: Heroi) -> void:
	match tipo:
		Tipo.FRUTA:
			heroi.curar(cura_fruta)
		Tipo.ERVA:
			var arvore: Arvore = get_tree().get_first_node_in_group("arvore")
			arvore.curar(cura_erva)
		Tipo.ESCUDO:
			heroi.ativar_escudo(duracao_escudo)
		Tipo.VELOCIDADE:
			heroi.ativar_velocidade(duracao_velocidade)
		Tipo.FORCA:
			heroi.ativar_forca(duracao_forca)
