class_name NumeroFlutuante
extends Node2D
## Número que sobe e some: dano nos inimigos e cura no herói e na Samaúma.

const SUBIDA: float = 30.0 ## pixels
const DURACAO: float = 0.75
const TAMANHO_NORMAL: int = 16
const TAMANHO_GRANDE: int = 24

@onready var _rotulo: Label = $Rotulo


func configurar(texto: String, cor: Color, grande: bool = false) -> void:
	if not is_node_ready():
		await ready
	_rotulo.text = texto
	_rotulo.add_theme_color_override("font_color", cor)
	_rotulo.add_theme_font_size_override("font_size", TAMANHO_GRANDE if grande else TAMANHO_NORMAL)


func _ready() -> void:
	var tween: Tween = create_tween().set_parallel()
	tween.tween_property(self, "position:y", position.y - SUBIDA, DURACAO).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tween.tween_property(self, "modulate:a", 0.0, DURACAO * 0.4).set_delay(DURACAO * 0.6)
	tween.chain().tween_callback(queue_free)
