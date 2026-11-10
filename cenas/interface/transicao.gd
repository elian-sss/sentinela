extends CanvasLayer
## Autoload "Transicao": escurece a tela, troca de cena e clareia de novo.
## Fica por cima de tudo e funciona mesmo com o jogo pausado.

const DURACAO: float = 0.25
const DURACAO_REINICIO: float = 0.1 ## o reinício da partida precisa ser quase imediato
const COR: Color = Color(0.03, 0.05, 0.035)

var _cortina: ColorRect
var _trocando: bool = false


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	_cortina = ColorRect.new()
	_cortina.color = COR
	_cortina.modulate.a = 0.0
	_cortina.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cortina.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_cortina)


func ir_para(caminho: String) -> void:
	_trocar(func() -> void: get_tree().change_scene_to_file(caminho), DURACAO)


func recarregar() -> void:
	_trocar(get_tree().reload_current_scene, DURACAO_REINICIO)


func _trocar(troca: Callable, duracao: float) -> void:
	if _trocando:
		return
	_trocando = true
	_cortina.mouse_filter = Control.MOUSE_FILTER_STOP
	await _fade(1.0, duracao)
	get_tree().paused = false
	troca.call()
	await get_tree().process_frame
	await _fade(0.0, duracao)
	_cortina.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_trocando = false


func _fade(alfa: float, duracao: float) -> void:
	var tween: Tween = create_tween()
	tween.tween_property(_cortina, "modulate:a", alfa, duracao)
	await tween.finished
