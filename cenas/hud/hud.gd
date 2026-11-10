class_name HUD
extends CanvasLayer
## Interface da partida: vida do Sentinela e da Samaúma, dash e power-ups ativos, onda atual,
## inimigos restantes, vida e estado do chefe, avisos de onda e alertas de perigo.

const NOMES_INIMIGOS: Dictionary = {
	"lenhador": "lenhadores",
	"motosserrista": "motosserristas",
	"fogo": "fogo",
	"chefe": "a escavadeira",
}
const TEXTOS_DO_CHEFE: Dictionary = {
	Chefe.Estado.AVISANDO: "Cuidado: investida!",
	Chefe.Estado.ATORDOADO: "Atordoada! Dano ×3",
	Chefe.Estado.DERROTADO: "Derrotada!",
}
const PIP_CHEIA: Texture2D = preload("res://assets/interface/pip_onda_cheia.png")
const PIP_VAZIA: Texture2D = preload("res://assets/interface/pip_onda_vazia.png")
const EFEITOS_DO_HEROI: Array[String] = ["escudo", "velocidade", "forca"]
const LIMITE_PERIGO: float = 0.3 ## fração de vida abaixo da qual a tela e os avisos pulsam
const VINHETA_MAXIMA: float = 0.55
const VINHETA_DANO: float = 0.5 ## clarão vermelho quando o herói leva dano
const TEMPO_DAS_DICAS: float = 12.0 ## segundos com as teclas na tela, só na primeira partida

## As dicas de controle aparecem só na primeira partida de cada sessão.
static var _dicas_ja_mostradas: bool = false

@export var heroi: Heroi
@export var arvore: Arvore
@export var gerente_de_ondas: GerenteDeOndas
@export var duracao_aviso_onda: float = 2.2

var _tween_aviso: Tween
var _clarao_dano: float = 0.0
var _tempo: float = 0.0

@onready var _vinheta: TextureRect = $VinhetaPerigo
@onready var _barra_heroi: BarraVida = $PainelHeroi/Barra
@onready var _valor_heroi: Label = $PainelHeroi/Valor
@onready var _barra_dash: BarraVida = $PainelHeroi/Estados/Dash/Barra
@onready var _estados: HBoxContainer = $PainelHeroi/Estados
@onready var _barra_arvore: BarraVida = $PainelArvore/Barra
@onready var _valor_arvore: Label = $PainelArvore/Valor
@onready var _perigo_arvore: Label = $PainelArvore/Perigo
@onready var _rotulo_onda: Label = $PainelOnda/RotuloOnda
@onready var _pips: HBoxContainer = $PainelOnda/Pips
@onready var _rotulo_restam: Label = $PainelOnda/RotuloRestam
@onready var _aviso: Control = $Aviso
@onready var _aviso_titulo: Label = $Aviso/Titulo
@onready var _aviso_subtitulo: Label = $Aviso/Subtitulo
@onready var _painel_chefe: Control = $PainelChefe
@onready var _barra_chefe: BarraVida = $PainelChefe/Barra
@onready var _estado_chefe: Label = $PainelChefe/Estado
@onready var _dicas: Control = $Dicas


func _ready() -> void:
	heroi.vida_alterada.connect(_ao_alterar_vida_heroi)
	heroi.dano_recebido.connect(func() -> void: _clarao_dano = 1.0)
	arvore.vida_alterada.connect(_ao_alterar_vida_arvore)
	gerente_de_ondas.onda_iniciada.connect(_ao_iniciar_onda)
	gerente_de_ondas.onda_concluida.connect(_ao_concluir_onda)
	gerente_de_ondas.restantes_alterado.connect(_ao_alterar_restantes)
	gerente_de_ondas.inimigo_nasceu.connect(_ao_nascer_inimigo)
	_barra_heroi.definir(heroi.vida_atual, heroi.vida_maxima, true)
	_barra_arvore.definir(arvore.vida_atual, arvore.vida_maxima, true)
	_valor_heroi.text = str(heroi.vida_atual)
	_valor_arvore.text = str(arvore.vida_atual)
	_aviso.hide()
	_montar_pips()
	_preparar_dicas()


func _process(delta: float) -> void:
	_tempo += delta
	_atualizar_estados_do_heroi()
	_atualizar_perigo(delta)


# ---------------------------------------------------------------- vida e estados

func _ao_alterar_vida_heroi(atual: int, maxima: int) -> void:
	_barra_heroi.definir(atual, maxima)
	_valor_heroi.text = str(atual)


func _ao_alterar_vida_arvore(atual: int, maxima: int) -> void:
	_barra_arvore.definir(atual, maxima)
	_valor_arvore.text = str(atual)


## Barrinhas do dash e dos power-ups ativos (escudo, velocidade e força).
func _atualizar_estados_do_heroi() -> void:
	_barra_dash.definir(heroi.fracao_dash(), 1.0, true)
	for nome: String in EFEITOS_DO_HEROI:
		var indicador: Control = _estados.get_node(nome.capitalize())
		var resto: float = heroi.fracao_do_efeito(nome)
		indicador.visible = resto > 0.0
		if resto > 0.0:
			(indicador.get_node("Barra") as BarraVida).definir(resto, 1.0, true)


## Borda vermelha pulsando com o herói por um fio, clarão quando ele leva dano
## e o aviso piscando quando a Samaúma está em perigo.
func _atualizar_perigo(delta: float) -> void:
	_clarao_dano = maxf(_clarao_dano - delta * 2.5, 0.0)
	var vida: float = float(heroi.vida_atual) / heroi.vida_maxima
	var pulso: float = 0.0
	if vida < LIMITE_PERIGO and vida > 0.0:
		pulso = VINHETA_MAXIMA * (0.6 + 0.4 * sin(_tempo * 6.0))
	_vinheta.modulate.a = maxf(pulso, _clarao_dano * VINHETA_DANO)
	var arvore_em_perigo: bool = arvore.fracao_de_vida() < LIMITE_PERIGO and not arvore.esta_destruida()
	_perigo_arvore.visible = arvore_em_perigo and fmod(_tempo, 0.8) < 0.55


# ---------------------------------------------------------------- ondas

func _ao_iniciar_onda(numero: int) -> void:
	if GerenteDeOndas.eh_infinito():
		_rotulo_onda.text = "Onda %d" % numero
	else:
		_rotulo_onda.text = "Onda %d/%d" % [numero, gerente_de_ondas.total_de_ondas()]
	_atualizar_pips(numero)
	_mostrar_aviso("Onda %d" % numero, _descrever_onda(numero))


func _ao_concluir_onda(numero: int) -> void:
	if not gerente_de_ondas.eh_ultima_onda(numero):
		_mostrar_aviso("Onda vencida!", "A Samaúma recupera as forças")


func _ao_alterar_restantes(quantidade: int) -> void:
	_rotulo_restam.text = "Restam %d" % quantidade if quantidade > 0 else ""


## Ex.: {"lenhador": 6, "fogo": 2} vira "Lenhadores e fogo".
func _descrever_onda(numero: int) -> String:
	var nomes: Array[String] = []
	var inimigos: Dictionary = gerente_de_ondas.inimigos_da_onda(numero)
	for tipo: String in ["chefe", "lenhador", "motosserrista", "fogo"]:
		if inimigos.has(tipo):
			nomes.append(NOMES_INIMIGOS[tipo])
	var texto: String = nomes[0]
	if nomes.size() > 1:
		texto = ", ".join(nomes.slice(0, -1)) + " e " + nomes[-1]
	return texto[0].to_upper() + texto.substr(1)


## No modo história, uma folhinha por onda. No infinito, o recorde a bater.
func _montar_pips() -> void:
	if GerenteDeOndas.eh_infinito():
		_pips.hide()
		return
	for i in gerente_de_ondas.total_de_ondas():
		var pip := TextureRect.new()
		pip.texture = PIP_VAZIA
		_pips.add_child(pip)


func _atualizar_pips(onda: int) -> void:
	for i in _pips.get_child_count():
		(_pips.get_child(i) as TextureRect).texture = PIP_CHEIA if i < onda else PIP_VAZIA


## Texto grande no centro: entra crescendo, fica um pouco e some.
func _mostrar_aviso(titulo: String, subtitulo: String) -> void:
	_aviso_titulo.text = titulo
	_aviso_subtitulo.text = subtitulo
	if _tween_aviso:
		_tween_aviso.kill()
	_aviso.show()
	_aviso.modulate.a = 0.0
	_aviso.scale = Vector2.ONE * 1.3
	_tween_aviso = create_tween()
	_tween_aviso.tween_property(_aviso, "modulate:a", 1.0, 0.2)
	_tween_aviso.parallel().tween_property(_aviso, "scale", Vector2.ONE, 0.25).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	_tween_aviso.tween_interval(duracao_aviso_onda)
	_tween_aviso.tween_property(_aviso, "modulate:a", 0.0, 0.4)
	_tween_aviso.tween_callback(_aviso.hide)


# ---------------------------------------------------------------- chefe

func _ao_nascer_inimigo(inimigo: Node2D) -> void:
	if not inimigo is Chefe:
		return
	var chefe: Chefe = inimigo
	chefe.vida_alterada.connect(_barra_chefe.definir)
	chefe.estado_alterado.connect(_ao_mudar_estado_do_chefe)
	chefe.morreu.connect(_ao_chefe_morrer)
	_barra_chefe.definir(chefe.vida_atual, chefe.vida_maxima, true)
	_estado_chefe.text = ""
	_painel_chefe.show()


func _ao_mudar_estado_do_chefe(estado: Chefe.Estado) -> void:
	_estado_chefe.text = TEXTOS_DO_CHEFE.get(estado, "")


func _ao_chefe_morrer(_posicao: Vector2) -> void:
	_painel_chefe.hide()


# ---------------------------------------------------------------- dicas de controle

func _preparar_dicas() -> void:
	if _dicas_ja_mostradas:
		_dicas.hide()
		return
	_dicas_ja_mostradas = true
	# O tween não anda com o jogo pausado, então as dicas só aparecem depois da fala da Samaúma.
	_dicas.modulate.a = 0.0
	var tween: Tween = create_tween()
	tween.tween_interval(0.5)
	tween.tween_property(_dicas, "modulate:a", 1.0, 0.5)
	tween.tween_interval(TEMPO_DAS_DICAS)
	tween.tween_property(_dicas, "modulate:a", 0.0, 1.0)
	tween.tween_callback(_dicas.hide)
