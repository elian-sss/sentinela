extends HBoxContainer
## Botões de ligar/desligar música e efeitos, usados no menu inicial e na pausa.
## O ícone mostra o estado: riscado quando está desligado.

const ICONES: Dictionary = {
	"musica_ligado": preload("res://assets/interface/icone_musica_ligado.png"),
	"musica_desligado": preload("res://assets/interface/icone_musica_desligado.png"),
	"efeitos_ligado": preload("res://assets/interface/icone_efeitos_ligado.png"),
	"efeitos_desligado": preload("res://assets/interface/icone_efeitos_desligado.png"),
}

@onready var _botao_musica: Button = $BotaoMusica
@onready var _botao_efeitos: Button = $BotaoEfeitos


func _ready() -> void:
	_botao_musica.pressed.connect(_alternar_musica)
	_botao_efeitos.pressed.connect(_alternar_efeitos)
	_atualizar_icones()


func _alternar_musica() -> void:
	AudioManager.alternar_musica()
	_atualizar_icones()


func _alternar_efeitos() -> void:
	AudioManager.alternar_efeitos()
	_atualizar_icones()


func _atualizar_icones() -> void:
	var musica: bool = AudioManager.musica_ligada()
	var efeitos: bool = AudioManager.efeitos_ligados()
	_botao_musica.icon = ICONES["musica_ligado" if musica else "musica_desligado"]
	_botao_efeitos.icon = ICONES["efeitos_ligado" if efeitos else "efeitos_desligado"]
	_botao_musica.tooltip_text = "Música: " + ("ligada" if musica else "desligada")
	_botao_efeitos.tooltip_text = "Efeitos: " + ("ligados" if efeitos else "desligados")
