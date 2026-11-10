class_name HUD
extends CanvasLayer
## Interface da partida: vida do herói, vida da árvore, onda atual e vida do chefe quando ele aparece.
## Atualiza só quando recebe os signals, sem consultar nada a cada frame.

@export var heroi: Heroi
@export var arvore: Arvore
@export var gerente_de_ondas: GerenteDeOndas
@export var duracao_aviso_onda: float = 2.0

@onready var _barra_heroi: ProgressBar = $PainelHeroi/BarraVida
@onready var _barra_arvore: ProgressBar = $PainelArvore/BarraVida
@onready var _painel_chefe: VBoxContainer = $PainelChefe
@onready var _barra_chefe: ProgressBar = $PainelChefe/BarraVida
@onready var _rotulo_onda: Label = $RotuloOnda
@onready var _aviso: Label = $Aviso
@onready var _timer_aviso: Timer = $TimerAviso


func _ready() -> void:
	heroi.vida_alterada.connect(_atualizar_barra.bind(_barra_heroi))
	arvore.vida_alterada.connect(_atualizar_barra.bind(_barra_arvore))
	gerente_de_ondas.onda_iniciada.connect(_ao_iniciar_onda)
	gerente_de_ondas.inimigo_nasceu.connect(_ao_nascer_inimigo)
	_timer_aviso.timeout.connect(_aviso.hide)
	_atualizar_barra(heroi.vida_atual, heroi.vida_maxima, _barra_heroi)
	_atualizar_barra(arvore.vida_atual, arvore.vida_maxima, _barra_arvore)


func atualizar_onda(atual: int, total: int) -> void:
	_rotulo_onda.text = "Onda %d/%d" % [atual, total]


func _atualizar_barra(atual: int, maxima: int, barra: ProgressBar) -> void:
	barra.max_value = maxima
	barra.value = atual


func _ao_iniciar_onda(numero: int) -> void:
	atualizar_onda(numero, gerente_de_ondas.total_de_ondas())
	_mostrar_aviso("Onda %d" % numero, duracao_aviso_onda)


## Mostra um texto grande no centro por alguns segundos.
func _mostrar_aviso(texto: String, duracao: float) -> void:
	_aviso.text = texto
	_aviso.show()
	_timer_aviso.start(duracao)


func _ao_nascer_inimigo(inimigo: Node2D) -> void:
	if not inimigo is Chefe:
		return
	var chefe: Chefe = inimigo
	chefe.vida_alterada.connect(_atualizar_barra.bind(_barra_chefe))
	chefe.morreu.connect(_ao_chefe_morrer)
	_atualizar_barra(chefe.vida_atual, chefe.vida_maxima, _barra_chefe)
	_painel_chefe.show()


func _ao_chefe_morrer(_posicao: Vector2) -> void:
	_painel_chefe.hide()
