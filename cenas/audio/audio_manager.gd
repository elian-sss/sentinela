extends Node
## Autoload de áudio: toca efeitos e músicas com troca suave (fade).
## Liga-se sozinho aos signals das cenas (os nós que já estão na árvore e os que entram depois),
## sem mexer na lógica do jogo. No navegador, o Godot só libera o som na primeira interação do jogador;
## até lá a música do menu fica em silêncio e começa sozinha no primeiro clique ou tecla.
## Os arquivos são gerados por tools/gerar_audio.py. Um som que não existir é ignorado, sem erro.

const PASTA_EFEITOS: String = "res://assets/audio/efeitos/"
const PASTA_MUSICAS: String = "res://assets/audio/musica/musica_"
const NOMES_DOS_EFEITOS: Array[String] = [
	"golpe", "golpe_acerto", "dash", "dano_heroi", "vida_baixa", "dano_arvore", "arvore_critica",
	"arvore_curada", "inimigo_derrotado", "item_caiu", "item_fruta", "item_erva", "escudo",
	"power_velocidade", "power_forca", "onda_iniciada", "onda_concluida", "fogo_nasce", "fogo_apagado",
	"motosserra", "escavadeira_investida", "chefe_aviso", "chefe_atordoado", "chefe_derrotado",
	"vitoria", "recorde", "derrota", "clique", "botao_foco", "pausa", "historia_avancar", "texto",
]
const NOMES_DAS_MUSICAS: Array[String] = ["menu", "calmaria", "combate", "chefe", "vitoria"]

const VOLUME_MUSICA_DB: float = -6.0
const VOLUME_EFEITOS_DB: float = 0.0
const DURACAO_FADE: float = 1.0
const VOLUME_SILENCIO_DB: float = -40.0
const VOZES_DE_EFEITO: int = 12
const VARIACAO_PITCH: float = 0.08 ## ±8% nos sons que repetem muito
const COM_VARIACAO_DE_PITCH: Array[String] = [
	"golpe", "golpe_acerto", "dano_heroi", "dano_arvore", "inimigo_derrotado", "texto",
]
## Intervalo mínimo (s) entre dois toques do mesmo som, para não embolar quando muitos acontecem juntos.
const INTERVALO_MINIMO: Dictionary = {
	"dano_arvore": 0.25, "motosserra": 0.6, "inimigo_derrotado": 0.05, "golpe_acerto": 0.04,
	"item_caiu": 0.1, "vida_baixa": 2.5, "texto": 0.045, "botao_foco": 0.05, "fogo_nasce": 0.3,
}
## Volume (dB) dos sons que precisam ficar mais discretos que os outros.
const VOLUME_DO_EFEITO: Dictionary = {"texto": -10.0, "botao_foco": -8.0, "item_caiu": -4.0, "golpe": -3.0}
const PITCH_MOTOR_CHEFE: float = 0.6
const FRACAO_VIDA_BAIXA: float = 0.3 ## abaixo disso, levar dano toca o aviso de vida baixa
const ESPERA_MUSICA_DA_VITORIA: float = 2.3 ## a música da vitória entra depois da fanfarra
const BUS_MUSICA: String = "Musica"
const BUS_EFEITOS: String = "Efeitos"
const CENA_MENU: String = "res://cenas/telas/TelaInicial.tscn"
const CENA_PAUSA: String = "res://cenas/telas/TelaPausa.tscn"
const CENA_MOTOSSERRISTA: String = "res://cenas/inimigo/Motosserrista.tscn"

var _efeitos: Dictionary = {}
var _musicas: Dictionary = {}
var _vozes: Array[AudioStreamPlayer] = []
var _proxima_voz: int = 0
var _ultimo_toque: Dictionary = {}
var _musica_ativa: AudioStreamPlayer
var _musica_reserva: AudioStreamPlayer
var _musica_atual: String = ""
var _pedido_de_musica: int = 0 ## muda a cada troca; cancela uma música agendada que ficou velha
var _fades: Dictionary = {} ## player -> Tween do fade em andamento


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_criar_bus(BUS_MUSICA, VOLUME_MUSICA_DB)
	_criar_bus(BUS_EFEITOS, VOLUME_EFEITOS_DB)
	for i in VOZES_DE_EFEITO:
		_vozes.append(_novo_player(BUS_EFEITOS))
	_musica_ativa = _novo_player(BUS_MUSICA)
	_musica_reserva = _novo_player(BUS_MUSICA)
	_carregar_sons()
	get_tree().node_added.connect(_ao_adicionar_no)
	_ligar_nos_existentes(get_tree().root)


# ---------------------------------------------------------------- API pública

func tocar(nome: String, pitch: float = 1.0) -> void:
	if not _efeitos.has(nome):
		return
	var agora: float = Time.get_ticks_msec() / 1000.0
	if agora - _ultimo_toque.get(nome, -INF) < INTERVALO_MINIMO.get(nome, 0.0):
		return
	_ultimo_toque[nome] = agora
	var voz: AudioStreamPlayer = _vozes[_proxima_voz]
	_proxima_voz = (_proxima_voz + 1) % _vozes.size()
	if nome in COM_VARIACAO_DE_PITCH:
		pitch *= 1.0 + randf_range(-VARIACAO_PITCH, VARIACAO_PITCH)
	voz.stream = _efeitos[nome]
	voz.pitch_scale = pitch
	voz.volume_db = VOLUME_DO_EFEITO.get(nome, 0.0)
	voz.play()


## Troca de música com fade cruzado. Repetir a música atual não reinicia nada.
func tocar_musica(nome: String) -> void:
	_pedido_de_musica += 1
	if nome == _musica_atual or not _musicas.has(nome):
		return
	_musica_atual = nome
	var saindo: AudioStreamPlayer = _musica_ativa
	_musica_ativa = _musica_reserva
	_musica_reserva = saindo
	_musica_ativa.stream = _musicas[nome]
	_musica_ativa.volume_db = VOLUME_SILENCIO_DB
	_musica_ativa.play()
	_fade(_musica_ativa, 0.0)
	_fade(saindo, VOLUME_SILENCIO_DB, true)


func parar_musica() -> void:
	_pedido_de_musica += 1
	_musica_atual = ""
	_fade(_musica_ativa, VOLUME_SILENCIO_DB, true)


func alternar_musica() -> void:
	_alternar_bus(BUS_MUSICA)


func alternar_efeitos() -> void:
	_alternar_bus(BUS_EFEITOS)


func musica_ligada() -> bool:
	return not AudioServer.is_bus_mute(AudioServer.get_bus_index(BUS_MUSICA))


func efeitos_ligados() -> bool:
	return not AudioServer.is_bus_mute(AudioServer.get_bus_index(BUS_EFEITOS))


# ---------------------------------------------------------------- ligação com as cenas

## Na primeira abertura do jogo, a cena principal entra na árvore antes deste Autoload ficar pronto.
func _ligar_nos_existentes(no: Node) -> void:
	for filho in no.get_children():
		if filho != self:
			_ao_adicionar_no(filho)
			_ligar_nos_existentes(filho)


func _ao_adicionar_no(no: Node) -> void:
	if no is Button:
		_ligar_botao(no)
	elif no is Heroi:
		_ligar_heroi(no)
	elif no is Golpe:
		no.acertou.connect(tocar.bind("golpe_acerto").unbind(1))
	elif no is Arvore:
		_ligar_arvore(no)
	elif no is Item:
		no.coletado.connect(_ao_coletar_item)
		tocar("item_caiu")
	elif no is GerenteDeOndas:
		no.onda_iniciada.connect(_ao_iniciar_onda.bind(no))
		no.onda_concluida.connect(_ao_concluir_onda.bind(no))
	elif no is GerenteDoJogo:
		no.vitoria.connect(_ao_vencer)
		no.derrota.connect(_ao_perder.unbind(1))
	elif no.scene_file_path == CENA_PAUSA:
		no.visibility_changed.connect(_ao_mudar_pausa.bind(no))
	elif no.scene_file_path == CENA_MENU:
		tocar_musica("menu")
	if no.is_in_group("inimigos"):
		_ligar_inimigo(no)


func _ligar_botao(botao: Button) -> void:
	botao.pressed.connect(tocar.bind("clique"))
	botao.mouse_entered.connect(tocar.bind("botao_foco"))
	botao.focus_entered.connect(tocar.bind("botao_foco"))


func _ligar_heroi(heroi: Heroi) -> void:
	heroi.atacou.connect(tocar.bind("golpe"))
	heroi.dash_iniciado.connect(tocar.bind("dash"))
	heroi.dano_recebido.connect(_ao_ferir_heroi.bind(heroi))


func _ligar_arvore(arvore: Arvore) -> void:
	arvore.dano_recebido.connect(tocar.bind("dano_arvore"))
	arvore.curada.connect(tocar.bind("arvore_curada").unbind(1))
	arvore.estado_alterado.connect(_ao_mudar_estado_da_arvore)


func _ligar_inimigo(inimigo: Node) -> void:
	if inimigo is Fogo:
		tocar("fogo_nasce")
		inimigo.morreu.connect(tocar.bind("fogo_apagado").unbind(1))
	elif inimigo is Chefe:
		inimigo.investiu.connect(tocar.bind("escavadeira_investida"))
		inimigo.estado_alterado.connect(_ao_mudar_estado_do_chefe)
		tocar("motosserra", PITCH_MOTOR_CHEFE)
	else:
		inimigo.morreu.connect(tocar.bind("inimigo_derrotado").unbind(1))
		if inimigo.scene_file_path == CENA_MOTOSSERRISTA:
			tocar("motosserra")


func _ao_ferir_heroi(heroi: Heroi) -> void:
	tocar("dano_heroi")
	if heroi.vida_atual > 0 and heroi.vida_atual < heroi.vida_maxima * FRACAO_VIDA_BAIXA:
		tocar("vida_baixa")


func _ao_mudar_estado_da_arvore(estado: Arvore.Estado) -> void:
	if estado == Arvore.Estado.CRITICA:
		tocar("arvore_critica")


func _ao_mudar_estado_do_chefe(estado: Chefe.Estado) -> void:
	match estado:
		Chefe.Estado.AVISANDO:
			tocar("chefe_aviso")
		Chefe.Estado.ATORDOADO:
			tocar("chefe_atordoado")
		Chefe.Estado.DERROTADO:
			tocar("chefe_derrotado")


func _ao_coletar_item(tipo: Item.Tipo) -> void:
	match tipo:
		Item.Tipo.FRUTA:
			tocar("item_fruta")
		Item.Tipo.ERVA:
			tocar("item_erva")
		Item.Tipo.ESCUDO:
			tocar("escudo")
		Item.Tipo.VELOCIDADE:
			tocar("power_velocidade")
		Item.Tipo.FORCA:
			tocar("power_forca")


func _ao_iniciar_onda(numero: int, gerente: GerenteDeOndas) -> void:
	tocar("onda_iniciada")
	tocar_musica("chefe" if gerente.eh_onda_do_chefe(numero) else "combate")


## Na pausa entre ondas entra o tema calmo. Depois da última onda quem decide é a vitória.
func _ao_concluir_onda(numero: int, gerente: GerenteDeOndas) -> void:
	if not gerente.eh_ultima_onda(numero):
		tocar("onda_concluida")
		tocar_musica("calmaria")


## Fanfarra e, logo depois, a música da vitória (se o jogador não tiver saído da tela antes).
func _ao_vencer() -> void:
	parar_musica()
	tocar("vitoria")
	var pedido: int = _pedido_de_musica
	await get_tree().create_timer(ESPERA_MUSICA_DA_VITORIA, true).timeout
	if pedido == _pedido_de_musica:
		tocar_musica("vitoria")


func _ao_perder() -> void:
	parar_musica()
	tocar("derrota")


func _ao_mudar_pausa(tela: CanvasLayer) -> void:
	if tela.visible:
		tocar("pausa")


# ---------------------------------------------------------------- internos

func _carregar_sons() -> void:
	for nome: String in NOMES_DOS_EFEITOS:
		var caminho: String = PASTA_EFEITOS + nome + ".ogg"
		if ResourceLoader.exists(caminho):
			_efeitos[nome] = load(caminho)
	for nome: String in NOMES_DAS_MUSICAS:
		var caminho: String = PASTA_MUSICAS + nome + ".ogg"
		if ResourceLoader.exists(caminho):
			var musica: AudioStreamOggVorbis = load(caminho)
			musica.loop = true
			_musicas[nome] = musica


func _criar_bus(nome: String, volume_db: float) -> void:
	if AudioServer.get_bus_index(nome) != -1:
		return
	AudioServer.add_bus()
	var indice: int = AudioServer.bus_count - 1
	AudioServer.set_bus_name(indice, nome)
	AudioServer.set_bus_volume_db(indice, volume_db)
	AudioServer.set_bus_send(indice, "Master")


func _novo_player(bus: String) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.bus = bus
	add_child(player)
	return player


## Cada player tem um fade por vez: o novo cancela o anterior, para um fade antigo não calar a música nova.
func _fade(player: AudioStreamPlayer, volume_final_db: float, parar_no_fim: bool = false) -> void:
	if _fades.has(player):
		(_fades[player] as Tween).kill()
	var tween: Tween = create_tween()
	_fades[player] = tween
	tween.tween_property(player, "volume_db", volume_final_db, DURACAO_FADE)
	if parar_no_fim:
		tween.tween_callback(player.stop)


func _alternar_bus(nome: String) -> void:
	var indice: int = AudioServer.get_bus_index(nome)
	AudioServer.set_bus_mute(indice, not AudioServer.is_bus_mute(indice))
