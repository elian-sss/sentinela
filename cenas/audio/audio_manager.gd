extends Node
## Autoload de áudio: toca efeitos e músicas com troca suave (fade).
## Liga-se sozinho aos signals das cenas quando os nós entram na árvore, sem mexer na lógica do jogo.
## A música só começa depois do primeiro clique em um botão (exigência do navegador).

const EFEITOS: Dictionary = {
	"golpe": preload("res://assets/audio/efeitos/golpe.ogg"),
	"dash": preload("res://assets/audio/efeitos/dash.ogg"),
	"dano_heroi": preload("res://assets/audio/efeitos/dano_heroi.ogg"),
	"dano_arvore": preload("res://assets/audio/efeitos/dano_arvore.ogg"),
	"inimigo_derrotado": preload("res://assets/audio/efeitos/inimigo_derrotado.ogg"),
	"item_fruta": preload("res://assets/audio/efeitos/item_fruta.ogg"),
	"item_erva": preload("res://assets/audio/efeitos/item_erva.ogg"),
	"escudo": preload("res://assets/audio/efeitos/escudo.ogg"),
	"onda_iniciada": preload("res://assets/audio/efeitos/onda_iniciada.ogg"),
	"motosserra": preload("res://assets/audio/efeitos/motosserra.ogg"),
	"escavadeira_investida": preload("res://assets/audio/efeitos/escavadeira_investida.ogg"),
	"vitoria": preload("res://assets/audio/efeitos/vitoria.ogg"),
	"derrota": preload("res://assets/audio/efeitos/derrota.ogg"),
	"clique": preload("res://assets/audio/efeitos/clique.ogg"),
	"pausa": preload("res://assets/audio/efeitos/pausa.ogg"),
}
const MUSICAS: Dictionary = {
	"menu": preload("res://assets/audio/musica/musica_menu.ogg"),
	"combate": preload("res://assets/audio/musica/musica_combate.ogg"),
	"chefe": preload("res://assets/audio/musica/musica_chefe.ogg"),
}

const VOLUME_MUSICA_DB: float = -6.0
const VOLUME_EFEITOS_DB: float = 0.0
const DURACAO_FADE: float = 1.0
const VOLUME_SILENCIO_DB: float = -40.0
const VOZES_DE_EFEITO: int = 12
const VARIACAO_PITCH: float = 0.08 ## ±8% nos sons que repetem muito
const COM_VARIACAO_DE_PITCH: Array[String] = ["golpe", "dano_heroi", "dano_arvore", "inimigo_derrotado"]
## Intervalo mínimo (s) entre dois toques do mesmo som, para não embolar quando muitos acontecem juntos.
const INTERVALO_MINIMO: Dictionary = {"dano_arvore": 0.25, "motosserra": 0.6, "inimigo_derrotado": 0.05}
const PITCH_MOTOR_CHEFE: float = 0.6
const BUS_MUSICA: String = "Musica"
const BUS_EFEITOS: String = "Efeitos"
const CENA_MENU: String = "res://cenas/telas/TelaInicial.tscn"
const CENA_PAUSA: String = "res://cenas/telas/TelaPausa.tscn"
const CENA_MOTOSSERRISTA: String = "res://cenas/inimigo/Motosserrista.tscn"

var _vozes: Array[AudioStreamPlayer] = []
var _proxima_voz: int = 0
var _ultimo_toque: Dictionary = {}
var _musica_ativa: AudioStreamPlayer
var _musica_reserva: AudioStreamPlayer
var _musica_atual: String = ""
var _audio_liberado: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_criar_bus(BUS_MUSICA, VOLUME_MUSICA_DB)
	_criar_bus(BUS_EFEITOS, VOLUME_EFEITOS_DB)
	for i in VOZES_DE_EFEITO:
		_vozes.append(_novo_player(BUS_EFEITOS))
	_musica_ativa = _novo_player(BUS_MUSICA)
	_musica_reserva = _novo_player(BUS_MUSICA)
	for musica: AudioStreamOggVorbis in MUSICAS.values():
		musica.loop = true
	get_tree().node_added.connect(_ao_adicionar_no)


# ---------------------------------------------------------------- API pública

func tocar(nome: String, pitch: float = 1.0) -> void:
	var agora: float = Time.get_ticks_msec() / 1000.0
	if agora - _ultimo_toque.get(nome, -INF) < INTERVALO_MINIMO.get(nome, 0.0):
		return
	_ultimo_toque[nome] = agora
	var voz: AudioStreamPlayer = _vozes[_proxima_voz]
	_proxima_voz = (_proxima_voz + 1) % _vozes.size()
	if nome in COM_VARIACAO_DE_PITCH:
		pitch *= 1.0 + randf_range(-VARIACAO_PITCH, VARIACAO_PITCH)
	voz.stream = EFEITOS[nome]
	voz.pitch_scale = pitch
	voz.play()


## Troca de música com fade cruzado. Repetir a música atual não reinicia nada.
func tocar_musica(nome: String) -> void:
	if not _audio_liberado or nome == _musica_atual:
		return
	_musica_atual = nome
	var saindo: AudioStreamPlayer = _musica_ativa
	_musica_ativa = _musica_reserva
	_musica_reserva = saindo
	_musica_ativa.stream = MUSICAS[nome]
	_musica_ativa.volume_db = VOLUME_SILENCIO_DB
	_musica_ativa.play()
	_fade(_musica_ativa, 0.0)
	_fade(saindo, VOLUME_SILENCIO_DB, true)


func parar_musica() -> void:
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

func _ao_adicionar_no(no: Node) -> void:
	if no is Button:
		no.pressed.connect(_ao_clicar_botao)
	elif no is Heroi:
		no.atacou.connect(tocar.bind("golpe"))
		no.dash_iniciado.connect(tocar.bind("dash"))
		no.dano_recebido.connect(tocar.bind("dano_heroi"))
	elif no is Arvore:
		no.dano_recebido.connect(tocar.bind("dano_arvore"))
	elif no is Item:
		no.coletado.connect(_ao_coletar_item)
	elif no is GerenteDeOndas:
		no.onda_iniciada.connect(_ao_iniciar_onda.bind(no))
		no.onda_concluida.connect(_ao_concluir_onda.bind(no))
	elif no is GerenteDoJogo:
		no.vitoria.connect(_ao_terminar_partida.bind("vitoria"))
		no.derrota.connect(_ao_terminar_partida.bind("derrota").unbind(1))
	elif no.scene_file_path == CENA_PAUSA:
		no.visibility_changed.connect(_ao_mudar_pausa.bind(no))
	elif no.scene_file_path == CENA_MENU:
		tocar_musica("menu")
	if no.is_in_group("inimigos"):
		_ligar_inimigo(no)


func _ligar_inimigo(inimigo: Node) -> void:
	inimigo.morreu.connect(tocar.bind("inimigo_derrotado").unbind(1))
	if inimigo is Chefe:
		inimigo.investiu.connect(tocar.bind("escavadeira_investida"))
		tocar("motosserra", PITCH_MOTOR_CHEFE)
	elif inimigo.scene_file_path == CENA_MOTOSSERRISTA:
		tocar("motosserra")


func _ao_clicar_botao() -> void:
	tocar("clique")
	if _audio_liberado:
		return
	_audio_liberado = true
	if get_tree().current_scene and get_tree().current_scene.scene_file_path == CENA_MENU:
		tocar_musica("menu")


func _ao_coletar_item(tipo: Item.Tipo) -> void:
	match tipo:
		Item.Tipo.FRUTA:
			tocar("item_fruta")
		Item.Tipo.ERVA:
			tocar("item_erva")
		Item.Tipo.ESCUDO:
			tocar("escudo")


func _ao_iniciar_onda(numero: int, gerente: GerenteDeOndas) -> void:
	_audio_liberado = true
	tocar("onda_iniciada")
	tocar_musica("chefe" if numero == gerente.total_de_ondas() else "combate")


## Na pausa entre ondas volta o tema calmo. Depois da última onda quem decide é a vitória.
func _ao_concluir_onda(numero: int, gerente: GerenteDeOndas) -> void:
	if numero < gerente.total_de_ondas():
		tocar_musica("menu")


func _ao_terminar_partida(efeito: String) -> void:
	parar_musica()
	tocar(efeito)


func _ao_mudar_pausa(tela: CanvasLayer) -> void:
	if tela.visible:
		tocar("pausa")


# ---------------------------------------------------------------- internos

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


func _fade(player: AudioStreamPlayer, volume_final_db: float, parar_no_fim: bool = false) -> void:
	var tween: Tween = create_tween()
	tween.tween_property(player, "volume_db", volume_final_db, DURACAO_FADE)
	if parar_no_fim:
		tween.tween_callback(player.stop)


func _alternar_bus(nome: String) -> void:
	var indice: int = AudioServer.get_bus_index(nome)
	AudioServer.set_bus_mute(indice, not AudioServer.is_bus_mute(indice))
