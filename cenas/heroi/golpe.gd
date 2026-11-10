class_name Golpe
extends Area2D
## Hitbox temporária do ataque do herói. Causa dano aos inimigos que tocar e some.

@export var dano: int = 10
@export var duracao: float = 0.1


func _ready() -> void:
	body_entered.connect(_ao_tocar_corpo)
	get_tree().create_timer(duracao).timeout.connect(queue_free)


func _ao_tocar_corpo(corpo: Node2D) -> void:
	if corpo.is_in_group("inimigos"):
		corpo.receber_dano(dano)
