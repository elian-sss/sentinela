class_name Feedback
extends RefCounted
## Efeitos de "sensação" do jogo. Nenhum deles muda as regras.
## Para desligar todos, mude ATIVO para false. Para desligar só um, troque a constante dele por false.

const ATIVO: bool = true
const PISCAR_INIMIGO_ATINGIDO: bool = ATIVO
const EMPURRAR_INIMIGO_ATINGIDO: bool = ATIVO
const TREMER_CAMERA: bool = ATIVO
const PISCAR_BARRA_ARVORE: bool = ATIVO

const DURACAO_PISCAR_BRANCO: float = 0.1
const BRILHO_PISCAR: Color = Color(3, 3, 3) ## acima de 1 clareia o sprite até quase branco


## Clareia o visual por um instante e volta ao normal. O tween morre junto com o nó.
## Usa self_modulate para não brigar com o modulate (tons de power-up e do chefe atordoado).
static func piscar_branco(no: Node, visual: CanvasItem) -> void:
	if not PISCAR_INIMIGO_ATINGIDO:
		return
	visual.self_modulate = BRILHO_PISCAR
	var tween: Tween = no.create_tween()
	tween.tween_interval(DURACAO_PISCAR_BRANCO)
	tween.tween_callback(func() -> void: visual.self_modulate = Color.WHITE)
