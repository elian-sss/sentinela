class_name CopaTransparente
extends Area2D
## Deixa a árvore (o Sprite2D pai) semitransparente enquanto um personagem está atrás da copa,
## para o jogador nunca perder de vista o herói e os inimigos.
## A área da copa é calculada sozinha a partir do tamanho do sprite: basta pôr este nó como filho.

const ALFA_TRANSPARENTE: float = 0.4
const FRACAO_COPA: float = 0.75 ## parte de cima do sprite que conta como copa
const VELOCIDADE_FADE: float = 5.0 ## quanto do alfa muda por segundo
const CAMADAS_PERSONAGENS: int = 1 | 2 ## herói e inimigos na camada 1, chefe na 2

var _sprite: Sprite2D
var _base_local: float


func _ready() -> void:
	_sprite = get_parent()
	collision_layer = 0
	collision_mask = CAMADAS_PERSONAGENS
	monitorable = false
	var area_sprite: Rect2 = _sprite.get_rect()
	var forma := RectangleShape2D.new()
	forma.size = Vector2(area_sprite.size.x, area_sprite.size.y * FRACAO_COPA)
	var colisao := CollisionShape2D.new()
	colisao.shape = forma
	colisao.position = area_sprite.position + forma.size / 2.0
	add_child(colisao)
	_base_local = area_sprite.end.y


func _process(delta: float) -> void:
	var alvo: float = ALFA_TRANSPARENTE if _tem_alguem_atras() else 1.0
	_sprite.modulate.a = move_toward(_sprite.modulate.a, alvo, VELOCIDADE_FADE * delta)


## Só conta quem está acima da base da árvore, porque quem está abaixo já aparece na frente dela.
func _tem_alguem_atras() -> bool:
	var base_y: float = _sprite.to_global(Vector2(0.0, _base_local)).y
	for corpo: Node2D in get_overlapping_bodies():
		if corpo is CharacterBody2D and corpo.global_position.y < base_y:
			return true
	return false
