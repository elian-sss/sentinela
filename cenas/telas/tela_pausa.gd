extends CanvasLayer
## Pausa com Esc. Só abre se o jogo não estiver pausado por outro motivo (ex.: diálogo ou tela de vitória/derrota).

const CENA_MENU: String = "res://cenas/telas/TelaInicial.tscn"

@onready var _botao_continuar: Button = $Centro/Painel/Caixa/BotaoContinuar
@onready var _botao_reiniciar: Button = $Centro/Painel/Caixa/BotaoReiniciar
@onready var _botao_menu: Button = $Centro/Painel/Caixa/BotaoMenu


func _ready() -> void:
	hide()
	_botao_continuar.pressed.connect(_continuar)
	_botao_reiniciar.pressed.connect(_reiniciar)
	_botao_menu.pressed.connect(_ir_para_menu)


func _unhandled_input(evento: InputEvent) -> void:
	if not evento.is_action_pressed("pausar"):
		return
	if visible:
		_continuar()
	elif not get_tree().paused:
		_pausar()
	get_viewport().set_input_as_handled()


func _pausar() -> void:
	show()
	get_tree().paused = true
	_botao_continuar.grab_focus()


func _continuar() -> void:
	hide()
	get_tree().paused = false


func _reiniciar() -> void:
	Transicao.recarregar()


func _ir_para_menu() -> void:
	Transicao.ir_para(CENA_MENU)
