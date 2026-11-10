class_name CameraTremor
extends Camera2D
## Câmera fixa da arena que treme um pouco quando o herói ou a árvore levam dano.
## Ancorada no canto superior esquerdo, mostra exatamente o mesmo que o jogo sem câmera.

@export var heroi: Heroi
@export var arvore: Arvore
@export var intensidade: float = 6.0 ## deslocamento máximo em pixels
@export var duracao: float = 0.2

var _tempo_restante: float = 0.0


func _ready() -> void:
	if not Feedback.TREMER_CAMERA:
		return
	heroi.dano_recebido.connect(tremer)
	arvore.dano_recebido.connect(tremer)


func _process(delta: float) -> void:
	if _tempo_restante <= 0.0:
		return
	_tempo_restante = maxf(_tempo_restante - delta, 0.0)
	var forca: float = intensidade * _tempo_restante / duracao
	offset = Vector2(randf_range(-forca, forca), randf_range(-forca, forca))


func tremer() -> void:
	_tempo_restante = duracao
