extends Control
## Tela inicial: título, "Jogar" e "Como jogar".
## O clique em "Jogar" também serve como o gesto que o navegador exige para liberar o áudio.

const CENA_ARENA: String = "res://cenas/arena/Arena.tscn"

@onready var _menu: VBoxContainer = $Centro/Menu
@onready var _como_jogar: VBoxContainer = $Centro/ComoJogar
@onready var _botao_jogar: Button = $Centro/Menu/BotaoJogar
@onready var _botao_como_jogar: Button = $Centro/Menu/BotaoComoJogar
@onready var _botao_voltar: Button = $Centro/ComoJogar/BotaoVoltar


func _ready() -> void:
	_botao_jogar.pressed.connect(_jogar)
	_botao_como_jogar.pressed.connect(_mostrar_como_jogar)
	_botao_voltar.pressed.connect(_voltar_ao_menu)
	_botao_jogar.grab_focus()


func _jogar() -> void:
	get_tree().change_scene_to_file(CENA_ARENA)


func _mostrar_como_jogar() -> void:
	_menu.hide()
	_como_jogar.show()
	_botao_voltar.grab_focus()


func _voltar_ao_menu() -> void:
	_como_jogar.hide()
	_menu.show()
	_botao_jogar.grab_focus()
