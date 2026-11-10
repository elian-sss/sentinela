class_name CicloDoDia
extends CanvasModulate
## Muda a luz da clareira a cada onda: manhã, dia, tarde, pôr do sol e noite, quando chega a escavadeira.
## No modo infinito o ciclo se repete a cada 5 ondas. Só tinge o mundo; a HUD fica em outra camada.

const LUZES: Array[Color] = [
	Color(1.0, 0.97, 0.88), # manhã
	Color(1.0, 1.0, 1.0), # dia
	Color(1.0, 0.92, 0.78), # tarde
	Color(1.0, 0.78, 0.62), # pôr do sol
	Color(0.66, 0.73, 1.0), # noite
]
const DURACAO_TRANSICAO: float = 2.5

@export var gerente_de_ondas: GerenteDeOndas


func _ready() -> void:
	color = LUZES[0]
	gerente_de_ondas.onda_iniciada.connect(_ao_iniciar_onda)


func _ao_iniciar_onda(numero: int) -> void:
	var luz: Color = LUZES[(numero - 1) % LUZES.size()]
	create_tween().tween_property(self, "color", luz, DURACAO_TRANSICAO)
