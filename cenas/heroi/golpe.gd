class_name Golpe
extends Area2D
## Hitbox temporária do ataque do herói. Causa dano aos inimigos que tocar e some.

@export var dano: int = 10
@export var duracao: float = 0.1
@export var forca_empurrao: float = 250.0


func _ready() -> void:
	body_entered.connect(_ao_tocar)
	area_entered.connect(_ao_tocar) # o fogo é uma área, não um corpo
	get_tree().create_timer(duracao, false).timeout.connect(queue_free)


func _ao_tocar(alvo: Node2D) -> void:
	if not alvo.is_in_group("inimigos"):
		return
	alvo.receber_dano(dano)
	if Feedback.EMPURRAR_INIMIGO_ATINGIDO and alvo.has_method("empurrar"):
		var direcao: Vector2 = get_parent().global_position.direction_to(alvo.global_position)
		alvo.empurrar(direcao * forca_empurrao)
