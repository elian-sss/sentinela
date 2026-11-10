class_name CameraTremor
extends Camera2D
## Câmera fixa da arena que treme um pouco quando o herói ou a árvore levam dano.
## Ancorada no canto superior esquerdo, mostra exatamente o mesmo que o jogo sem câmera.

@export var heroi: Heroi
@export var arvore: Arvore
@export var intensidade: float = 6.0 ## deslocamento máximo em pixels
@export var duracao: float = 0.2
@export var multiplicador_forte: float = 2.5 ## batidas grandes: chefe na borda e chefe derrotado

var _tempo_restante: float = 0.0
var _duracao_atual: float = 0.2
var _intensidade_atual: float = 0.0


func _ready() -> void:
	add_to_group("camera")
	if not Feedback.TREMER_CAMERA:
		return
	heroi.dano_recebido.connect(tremer)
	arvore.dano_recebido.connect(tremer)


func _process(delta: float) -> void:
	if _tempo_restante <= 0.0:
		return
	_tempo_restante = maxf(_tempo_restante - delta, 0.0)
	var forca: float = _intensidade_atual * _tempo_restante / _duracao_atual
	offset = Vector2(randf_range(-forca, forca), randf_range(-forca, forca))


func tremer() -> void:
	_iniciar(intensidade, duracao)


func tremer_forte() -> void:
	_iniciar(intensidade * multiplicador_forte, duracao * 2.0)


## Um tremor fraco não interrompe um forte que ainda está acontecendo.
func _iniciar(forca: float, tempo: float) -> void:
	if _tempo_restante > 0.0 and forca < _intensidade_atual:
		return
	_intensidade_atual = forca
	_duracao_atual = tempo
	_tempo_restante = tempo
