class_name TelaHistoria
extends CanvasLayer
## Modo história: no início de cada onda, pausa o jogo e a Samaúma fala com o Sentinela numa caixa de diálogo.
## O texto aparece letra por letra. Clique, J, Espaço ou Enter completam a fala e depois avançam.
## Cada onda fala só uma vez por sessão, para não atrapalhar quem reinicia várias vezes.

## As falas de cada onda, na mesma ordem de Balanceamento.ONDAS. Cada item da lista é uma página.
const FALAS: Array[Array] = [
	[
		"Acorde, Sentinela. O chão está tremendo: são machados chegando à clareira.",
		"Eu sou a Samaúma, a mãe das árvores. Se eu cair, a floresta inteira cai comigo.",
		"Não deixe que me toquem.",
	],
	[
		"Eles voltaram, e trouxeram fogo.",
		"Bata nas chamas com o cajado antes que alcancem as minhas raízes.",
	],
	[
		"Escute esse ronco... são motosserras.",
		"Eles são ligeiros, mas caem fácil.",
	],
	[
		"Agora vêm todos de uma vez.",
		"Use o que a floresta dá: a fruta cura você, e a erva me cura.",
	],
	[
		"O chão treme de novo. É a máquina que come a mata.",
		"Quando ela investir, saia da frente. E bata enquanto ela estiver atordoada!",
	],
]
const TEXTO_VITORIA: String = "A máquina parou, e os homens foram embora.\nEnquanto houver um Sentinela, a floresta fica de pé."

const LETRAS_POR_SEGUNDO: float = 42.0
const LETRAS_POR_SOM: int = 2 ## toca o blip a cada tantas letras
## Tempo entre fechar o diálogo e o jogo voltar, para a tecla usada não virar dash ou ataque.
const ATRASO_AO_FECHAR: float = 0.1

static var _ondas_ja_vistas: Array[int] = []

@export var gerente_de_ondas: GerenteDeOndas

var _paginas: Array = []
var _pagina: int = 0
var _letras: float = 0.0
var _ultima_letra_com_som: int = 0

@onready var _texto: Label = $Caixa/Conteudo/Falas/Texto
@onready var _seta: TextureRect = $Caixa/Conteudo/Falas/Rodape/Seta


func _ready() -> void:
	hide()
	set_process(false)
	gerente_de_ondas.onda_iniciada.connect(_ao_iniciar_onda)


func _process(delta: float) -> void:
	if _pagina_completa():
		_seta.modulate.a = 0.4 + 0.6 * absf(sin(Time.get_ticks_msec() / 250.0))
		return
	_letras += LETRAS_POR_SEGUNDO * delta
	_texto.visible_characters = int(_letras)
	if int(_letras) >= _ultima_letra_com_som + LETRAS_POR_SOM:
		_ultima_letra_com_som = int(_letras)
		AudioManager.tocar("texto")


func _unhandled_input(evento: InputEvent) -> void:
	if not visible:
		return
	if evento.is_action_pressed("ui_accept") or evento.is_action_pressed("atacar"):
		get_viewport().set_input_as_handled()
		_avancar()


func _ao_iniciar_onda(numero: int) -> void:
	if GerenteDeOndas.eh_infinito() or numero > FALAS.size() or numero in _ondas_ja_vistas:
		return
	_ondas_ja_vistas.append(numero)
	_paginas = FALAS[numero - 1]
	_mostrar_pagina(0)
	show()
	set_process(true)
	get_tree().paused = true


func _mostrar_pagina(indice: int) -> void:
	_pagina = indice
	_letras = 0.0
	_ultima_letra_com_som = 0
	_texto.text = _paginas[indice]
	_texto.visible_characters = 0
	_seta.modulate.a = 0.0


func _pagina_completa() -> bool:
	return _letras >= _texto.text.length()


## Primeiro toque completa a fala; o seguinte passa para a próxima página ou fecha.
func _avancar() -> void:
	if not _pagina_completa():
		_letras = _texto.text.length()
		_texto.visible_characters = -1
		return
	AudioManager.tocar("historia_avancar")
	if _pagina + 1 < _paginas.size():
		_mostrar_pagina(_pagina + 1)
	else:
		_fechar()


func _fechar() -> void:
	hide()
	set_process(false)
	await get_tree().create_timer(ATRASO_AO_FECHAR, true).timeout
	get_tree().paused = false
