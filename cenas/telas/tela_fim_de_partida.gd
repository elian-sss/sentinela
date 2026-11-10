class_name TelaFimDePartida
extends CanvasLayer
## Tela de vitória ou derrota mostrada sobre o jogo, que fica pausado.
## "Jogar de novo" (botão ou tecla R) reinicia a partida na hora.

@export var gerente_do_jogo: GerenteDoJogo

@onready var _titulo: Label = $Centro/Caixa/Titulo
@onready var _texto: Label = $Centro/Caixa/Texto
@onready var _botao: Button = $Centro/Caixa/BotaoJogarDeNovo


func _ready() -> void:
	hide()
	gerente_do_jogo.derrota.connect(_ao_perder)
	gerente_do_jogo.vitoria.connect(_ao_vencer)
	_botao.pressed.connect(_reiniciar)


func _unhandled_input(evento: InputEvent) -> void:
	if visible and evento.is_action_pressed("reiniciar"):
		_reiniciar()


func _ao_perder(onda: int) -> void:
	_mostrar("Derrota", "Você caiu na onda %d." % onda)


func _ao_vencer() -> void:
	_mostrar("Vitória!", "A árvore sagrada está a salvo.")


func _mostrar(titulo: String, texto: String) -> void:
	_titulo.text = titulo
	_texto.text = texto
	show()
	get_tree().paused = true
	_botao.grab_focus()


func _reiniciar() -> void:
	get_tree().paused = false
	get_tree().reload_current_scene()
