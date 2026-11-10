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


## Deixa o visual branco por um instante e volta à cor original. O tween morre junto com o nó.
static func piscar_branco(no: Node, visual: ColorRect, cor_original: Color) -> void:
	if not PISCAR_INIMIGO_ATINGIDO:
		return
	visual.color = Color.WHITE
	var tween: Tween = no.create_tween()
	tween.tween_interval(DURACAO_PISCAR_BRANCO)
	tween.tween_callback(func() -> void: visual.color = cor_original)
