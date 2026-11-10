class_name TelaFimDePartida
extends CanvasLayer
## Tela de vitória ou derrota mostrada sobre o jogo, que fica pausado.
## Mostra o desfecho, os números da partida e, na derrota, uma dica para a próxima tentativa.
## "Jogar de novo" (botão ou tecla R) reinicia a partida na hora.

const CENA_MENU: String = "res://cenas/telas/TelaInicial.tscn"
const COR_VITORIA: Color = Color(0.98, 0.855, 0.47)
const COR_DERROTA: Color = Color(1.0, 0.45, 0.35)
const TEXTOS_DE_DERROTA: Dictionary = {
	GerenteDoJogo.Motivo.ARVORE_CAIU: ["A Samaúma caiu", "Sem a mãe das árvores, a floresta ficou em silêncio."],
	GerenteDoJogo.Motivo.HEROI_CAIU: ["O Sentinela caiu", "Sem guardião, a clareira ficou aberta para as máquinas."],
}
const DICAS: Array[String] = [
	"Use o dash (Espaço) para escapar quando estiver cercado.",
	"A erva cura a Samaúma mesmo de longe. Pegue sempre que cair.",
	"Fogo perto das raízes machuca a Samaúma. Apague primeiro.",
	"A escavadeira leva o triplo de dano enquanto está atordoada.",
	"Motosserristas são frágeis: dois golpes resolvem.",
	"Com pouca vida, os inimigos soltam mais frutas.",
	"Depois de levar dano você fica um instante invencível. Aproveite para sair do aperto.",
]

@export var gerente_do_jogo: GerenteDoJogo

@onready var _painel: Control = $Centro/Painel
@onready var _titulo: Label = $Centro/Painel/Caixa/Titulo
@onready var _texto: Label = $Centro/Painel/Caixa/Texto
@onready var _numeros: Label = $Centro/Painel/Caixa/Numeros
@onready var _dica: Label = $Centro/Painel/Caixa/Dica
@onready var _botao_de_novo: Button = $Centro/Painel/Caixa/Botoes/BotaoJogarDeNovo
@onready var _botao_menu: Button = $Centro/Painel/Caixa/Botoes/BotaoMenu


func _ready() -> void:
	hide()
	gerente_do_jogo.derrota.connect(_ao_perder)
	gerente_do_jogo.vitoria.connect(_ao_vencer)
	_botao_de_novo.pressed.connect(_reiniciar)
	_botao_menu.pressed.connect(_ir_para_menu)


func _unhandled_input(evento: InputEvent) -> void:
	if visible and evento.is_action_pressed("reiniciar"):
		_reiniciar()


func _ao_perder(onda: int) -> void:
	var textos: Array = TEXTOS_DE_DERROTA[gerente_do_jogo.motivo_da_derrota]
	var titulo: String = textos[0]
	var texto: String = textos[1]
	if GerenteDeOndas.eh_infinito() and Recorde.registrar(onda):
		titulo = "Novo recorde!"
		texto = "Você resistiu até a onda %d." % onda
		AudioManager.tocar("recorde")
	_dica.text = "Dica: " + DICAS.pick_random()
	_dica.show()
	_mostrar(titulo, texto, COR_VITORIA if titulo == "Novo recorde!" else COR_DERROTA, onda)


func _ao_vencer() -> void:
	_dica.hide()
	_mostrar("Vitória!", TelaHistoria.TEXTO_VITORIA, COR_VITORIA, gerente_do_jogo.gerente_de_ondas.onda_atual())


func _mostrar(titulo: String, texto: String, cor: Color, onda: int) -> void:
	_titulo.text = titulo
	_titulo.add_theme_color_override("font_color", cor)
	_texto.text = texto
	_numeros.text = _resumo_da_partida(onda)
	show()
	get_tree().paused = true
	_painel.pivot_offset = _painel.size / 2.0
	_painel.scale = Vector2.ONE * 0.85
	_painel.modulate.a = 0.0
	var tween: Tween = create_tween().set_parallel()
	tween.tween_property(_painel, "modulate:a", 1.0, 0.2)
	tween.tween_property(_painel, "scale", Vector2.ONE, 0.25).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	_botao_de_novo.grab_focus()


## Ex.: "Onda 4/5   •   Tempo 2:37   •   32 derrotados   •   Samaúma 64%"
func _resumo_da_partida(onda: int) -> String:
	var ondas: GerenteDeOndas = gerente_do_jogo.gerente_de_ondas
	var segundos: int = int(gerente_do_jogo.tempo_de_partida)
	var partes: Array[String] = []
	if GerenteDeOndas.eh_infinito():
		partes.append("Onda %d" % onda)
		partes.append("Recorde %d" % Recorde.carregar())
	else:
		partes.append("Onda %d/%d" % [onda, ondas.total_de_ondas()])
	partes.append("Tempo %d:%02d" % [floori(segundos / 60.0), segundos % 60])
	partes.append("%d derrotados" % ondas.inimigos_derrotados())
	partes.append("Samaúma %d%%" % roundi(gerente_do_jogo.arvore.fracao_de_vida() * 100.0))
	return "   •   ".join(partes)


func _reiniciar() -> void:
	Transicao.recarregar()


func _ir_para_menu() -> void:
	Transicao.ir_para(CENA_MENU)
