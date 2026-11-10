extends Control
## Tela inicial: a clareira da Samaúma ao fundo, o logo, os dois modos de jogo, "Como jogar" e "Créditos".
## O clique num modo também serve como o gesto que o navegador exige para liberar o áudio.

const CENA_ARENA: String = "res://cenas/arena/Arena.tscn"
const BALANCO_LOGO: float = 4.0 ## pixels que o logo sobe e desce
const DURACAO_BALANCO: float = 2.4

@onready var _logo: TextureRect = $Interface/Logo
@onready var _botao_historia: Button = $Interface/Menu/BotaoHistoria
@onready var _botao_infinito: Button = $Interface/Menu/BotaoInfinito
@onready var _rotulo_recorde: Label = $Interface/Menu/RotuloRecorde
@onready var _botao_como_jogar: Button = $Interface/Menu/BotaoComoJogar
@onready var _botao_creditos: Button = $Interface/Menu/BotaoCreditos
@onready var _como_jogar: Control = $Interface/ComoJogar
@onready var _creditos: Control = $Interface/Creditos
@onready var _voltar_como_jogar: Button = $Interface/ComoJogar/Centro/Painel/Caixa/BotaoVoltar
@onready var _voltar_creditos: Button = $Interface/Creditos/Centro/Painel/Caixa/BotaoVoltar


func _ready() -> void:
	_botao_historia.pressed.connect(_jogar.bind(GerenteDeOndas.Modo.HISTORIA))
	_botao_infinito.pressed.connect(_jogar.bind(GerenteDeOndas.Modo.INFINITO))
	_botao_como_jogar.pressed.connect(_abrir.bind(_como_jogar, _voltar_como_jogar))
	_botao_creditos.pressed.connect(_abrir.bind(_creditos, _voltar_creditos))
	_voltar_como_jogar.pressed.connect(_fechar.bind(_como_jogar, _botao_como_jogar))
	_voltar_creditos.pressed.connect(_fechar.bind(_creditos, _botao_creditos))
	_mostrar_recorde()
	_balancar_logo()
	_botao_historia.grab_focus()


## Esc fecha o painel que estiver aberto.
func _unhandled_input(evento: InputEvent) -> void:
	if not evento.is_action_pressed("pausar"):
		return
	if _como_jogar.visible:
		_fechar(_como_jogar, _botao_como_jogar)
	elif _creditos.visible:
		_fechar(_creditos, _botao_creditos)


func _mostrar_recorde() -> void:
	var recorde: int = Recorde.carregar()
	_rotulo_recorde.visible = recorde > 0
	_rotulo_recorde.text = "Recorde: onda %d" % recorde


func _balancar_logo() -> void:
	var base: float = _logo.position.y
	var tween: Tween = create_tween().set_loops().set_trans(Tween.TRANS_SINE)
	tween.tween_property(_logo, "position:y", base - BALANCO_LOGO, DURACAO_BALANCO)
	tween.tween_property(_logo, "position:y", base + BALANCO_LOGO, DURACAO_BALANCO)


func _jogar(modo: GerenteDeOndas.Modo) -> void:
	GerenteDeOndas.modo = modo
	Transicao.ir_para(CENA_ARENA)


func _abrir(painel: Control, botao_voltar: Button) -> void:
	painel.show()
	botao_voltar.grab_focus()


func _fechar(painel: Control, botao_de_origem: Button) -> void:
	painel.hide()
	botao_de_origem.grab_focus()
