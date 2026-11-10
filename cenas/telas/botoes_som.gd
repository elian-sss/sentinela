extends HBoxContainer
## Botões de ligar/desligar música e efeitos, usados no menu inicial e na pausa.

@onready var _botao_musica: Button = $BotaoMusica
@onready var _botao_efeitos: Button = $BotaoEfeitos


func _ready() -> void:
	_botao_musica.pressed.connect(_alternar_musica)
	_botao_efeitos.pressed.connect(_alternar_efeitos)
	_atualizar_textos()


func _alternar_musica() -> void:
	AudioManager.alternar_musica()
	_atualizar_textos()


func _alternar_efeitos() -> void:
	AudioManager.alternar_efeitos()
	_atualizar_textos()


func _atualizar_textos() -> void:
	_botao_musica.text = "Música: " + ("ligada" if AudioManager.musica_ligada() else "desligada")
	_botao_efeitos.text = "Efeitos: " + ("ligados" if AudioManager.efeitos_ligados() else "desligados")
