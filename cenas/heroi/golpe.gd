class_name Golpe
extends Area2D
## Ataque do herói: um arco de energia do cajado. A hitbox causa dano só durante `duracao`;
## o desenho termina a animação e o nó some quando ela acaba.

## Os sprites são desenhados acima do centro da colisão, então o arco sobe junto para sair do tronco do herói.
## Só o desenho sobe; a hitbox continua no lugar.
const DESLOCAMENTO_VISUAL: Vector2 = Vector2(0, -12)

var dano: int = Balanceamento.HEROI_DANO_ATAQUE
var duracao: float = Balanceamento.HEROI_DURACAO_GOLPE
@export var forca_empurrao: float = 250.0

@onready var _visual: AnimatedSprite2D = $Visual


func _ready() -> void:
	body_entered.connect(_ao_tocar)
	area_entered.connect(_ao_tocar) # o fogo é uma área, não um corpo
	get_tree().create_timer(duracao, false).timeout.connect(_desligar_hitbox)
	_visual.global_position = global_position + DESLOCAMENTO_VISUAL
	_visual.animation_finished.connect(queue_free)
	_visual.play("golpe")


func _desligar_hitbox() -> void:
	set_deferred("monitoring", false)


func _ao_tocar(alvo: Node2D) -> void:
	if not alvo.is_in_group("inimigos"):
		return
	alvo.receber_dano(dano)
	if Feedback.EMPURRAR_INIMIGO_ATINGIDO and alvo.has_method("empurrar"):
		var direcao: Vector2 = get_parent().global_position.direction_to(alvo.global_position)
		alvo.empurrar(direcao * forca_empurrao)
