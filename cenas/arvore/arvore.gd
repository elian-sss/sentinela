class_name Arvore
extends StaticBody2D
## Árvore sagrada que o herói protege. Se a vida chegar a zero, o jogo é perdido.

signal vida_alterada(atual: int, maxima: int)
signal destruida

@export var vida_maxima: int = 300
@export var vida_atual: int = 300:
	set = _definir_vida


func receber_dano(valor: int) -> void:
	vida_atual -= valor


func curar(valor: int) -> void:
	vida_atual += valor


func esta_destruida() -> bool:
	return vida_atual <= 0


func _definir_vida(valor: int) -> void:
	var anterior: int = vida_atual
	vida_atual = clampi(valor, 0, vida_maxima)
	if vida_atual == anterior:
		return
	vida_alterada.emit(vida_atual, vida_maxima)
	if vida_atual == 0:
		destruida.emit()
