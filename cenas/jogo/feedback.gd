class_name Feedback
extends RefCounted
## Efeitos de "sensação" do jogo. Nenhum deles muda as regras.
## Para desligar todos, mude ATIVO para false. Para desligar só um, troque a constante dele por false.

const ATIVO: bool = true
const PISCAR_INIMIGO_ATINGIDO: bool = ATIVO
const EMPURRAR_INIMIGO_ATINGIDO: bool = ATIVO
const TREMER_CAMERA: bool = ATIVO
const PISCAR_BARRA_ARVORE: bool = ATIVO
const NUMEROS_FLUTUANTES: bool = ATIVO
const RASTRO_DO_DASH: bool = ATIVO
const FAISCAS_DE_IMPACTO: bool = ATIVO

const DURACAO_PISCAR: float = 0.1
const BRILHO_PISCAR: Color = Color(3, 3, 3) ## acima de 1 clareia o sprite até quase branco
const BRILHO_DANO_HEROI: Color = Color(3, 0.7, 0.6) ## o herói pisca avermelhado quando leva dano
const ALTURA_NUMERO: float = 44.0 ## quanto acima do personagem o número nasce

const COR_DANO: Color = Color(1.0, 0.96, 0.82)
const COR_DANO_FORTE: Color = Color(1.0, 0.82, 0.25)
const COR_CURA_HEROI: Color = Color(1.0, 0.5, 0.45)
const COR_CURA_ARVORE: Color = Color(0.62, 1.0, 0.5)

const CENA_NUMERO: PackedScene = preload("res://cenas/efeitos/NumeroFlutuante.tscn")
const CENA_IMPACTO: PackedScene = preload("res://cenas/efeitos/Impacto.tscn")


## Clareia o visual por um instante e volta ao normal. O tween morre junto com o nó.
## Usa self_modulate para não brigar com o modulate (tons de power-up e do chefe atordoado).
static func piscar_branco(no: Node, visual: CanvasItem, brilho: Color = BRILHO_PISCAR) -> void:
	if not PISCAR_INIMIGO_ATINGIDO:
		return
	visual.self_modulate = brilho
	var tween: Tween = no.create_tween()
	tween.tween_interval(DURACAO_PISCAR)
	tween.tween_callback(func() -> void: visual.self_modulate = Color.WHITE)


## Número que sobe acima de `no` e some (dano ou cura).
static func numero(no: Node2D, texto: String, cor: Color, grande: bool = false) -> void:
	if not NUMEROS_FLUTUANTES or not no.is_inside_tree():
		return
	var flutuante: NumeroFlutuante = CENA_NUMERO.instantiate()
	flutuante.position = no.global_position + Vector2(randf_range(-10.0, 10.0), -ALTURA_NUMERO)
	no.get_parent().add_child(flutuante)
	flutuante.configurar(texto, cor, grande)


## Faíscas no ponto onde o golpe acertou, espalhando na direção do golpe.
static func impacto(alvo: Node2D, direcao: Vector2) -> void:
	if not FAISCAS_DE_IMPACTO or not alvo.is_inside_tree():
		return
	var faiscas: CPUParticles2D = CENA_IMPACTO.instantiate()
	faiscas.position = alvo.global_position + Vector2(0, -12)
	faiscas.rotation = direcao.angle()
	alvo.get_parent().add_child(faiscas)


## Pede para a câmera tremer. `forte` é para batidas grandes (chefe na borda, chefe derrotado).
static func tremer(arvore_de_cena: SceneTree, forte: bool = false) -> void:
	if TREMER_CAMERA:
		arvore_de_cena.call_group("camera", "tremer_forte" if forte else "tremer")
