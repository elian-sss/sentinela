class_name BarraVida
extends Control
## Barra em pixel art desenhada por código: moldura escura, preenchimento com luz em cima e sombra embaixo,
## um "fantasma" claro que mostra o quanto acabou de ser perdido e um clarão quando leva dano.
## Serve para vida (herói, Samaúma, chefe) e, sem fantasma nem marcas, para os tempos de dash e power-ups.

const PIXEL: float = 2.0 ## tamanho de um pixel de arte na tela
const COR_MOLDURA: Color = Color(0.07, 0.085, 0.063)
const COR_FUNDO: Color = Color(0.16, 0.12, 0.09)
const COR_FANTASMA: Color = Color(1.0, 0.93, 0.7)
const COR_LISTRA: Color = Color(0.1, 0.1, 0.1, 0.45)
const VELOCIDADE_VALOR: float = 4.0 ## frações de barra por segundo
const VELOCIDADE_FANTASMA: float = 0.5
const ESPERA_FANTASMA: float = 0.35 ## segundos parado antes de o fantasma começar a descer
const DURACAO_CLARAO: float = 0.25
const LIMITE_CRITICO: float = 0.3 ## abaixo dessa fração a barra pulsa

@export var cor: Color = Color(0.93, 0.43, 0.14)
@export var da_direita: bool = false ## enche da direita para a esquerda
@export var listras: bool = false ## faixas de alerta por cima do preenchimento (chefe)
@export var com_fantasma: bool = true
@export var com_marcas: bool = true ## risquinhos a cada 25%
@export var pulsar_no_critico: bool = true

var _alvo: float = 1.0
var _valor: float = 1.0
var _fantasma: float = 1.0
var _espera: float = 0.0
var _clarao: float = 0.0
var _tempo: float = 0.0


## Define o valor mostrado. Com `imediato`, pula a animação (use ao criar a barra).
func definir(atual: float, maximo: float, imediato: bool = false) -> void:
	var novo: float = clampf(atual / maximo, 0.0, 1.0) if maximo > 0.0 else 0.0
	if novo < _alvo and not imediato:
		_espera = ESPERA_FANTASMA
		_clarao = DURACAO_CLARAO
	_alvo = novo
	if imediato:
		_valor = novo
		_fantasma = novo
	queue_redraw()


func fracao() -> float:
	return _alvo


func _process(delta: float) -> void:
	_tempo += delta
	var parado: bool = is_equal_approx(_valor, _alvo) and _fantasma <= _valor and _clarao <= 0.0
	if parado and not (pulsar_no_critico and _alvo < LIMITE_CRITICO and _alvo > 0.0):
		return
	_valor = move_toward(_valor, _alvo, VELOCIDADE_VALOR * delta)
	_espera = maxf(_espera - delta, 0.0)
	if _espera <= 0.0:
		_fantasma = move_toward(_fantasma, _valor, VELOCIDADE_FANTASMA * delta)
	_fantasma = maxf(_fantasma, _valor)
	_clarao = maxf(_clarao - delta, 0.0)
	queue_redraw()


func _draw() -> void:
	var total := Rect2(Vector2.ZERO, size)
	draw_rect(total, COR_MOLDURA)
	draw_rect(total.grow(-PIXEL), COR_FUNDO)
	var area: Rect2 = total.grow(-PIXEL * 2.0)
	if com_fantasma and _fantasma > _valor:
		draw_rect(_trecho(area, _fantasma), COR_FANTASMA)
	if _valor > 0.0:
		_desenhar_preenchimento(area)
	if com_marcas:
		for i in range(1, 4):
			var x: float = area.position.x + snappedf(area.size.x * i / 4.0, PIXEL)
			draw_rect(Rect2(x, area.position.y, PIXEL, area.size.y), Color(0, 0, 0, 0.3))


func _desenhar_preenchimento(area: Rect2) -> void:
	var cheio: Rect2 = _trecho(area, _valor)
	var base: Color = cor
	if pulsar_no_critico and _alvo < LIMITE_CRITICO:
		base = cor.lerp(Color.WHITE, 0.25 + 0.25 * sin(_tempo * 10.0))
	draw_rect(cheio, base)
	draw_rect(Rect2(cheio.position, Vector2(cheio.size.x, PIXEL)), base.lightened(0.4))
	draw_rect(Rect2(cheio.position.x, cheio.end.y - PIXEL, cheio.size.x, PIXEL), base.darkened(0.35))
	if listras:
		_desenhar_listras(cheio)
	if _clarao > 0.0:
		draw_rect(cheio, Color(1, 1, 1, _clarao / DURACAO_CLARAO * 0.8))


## Faixas diagonais em degraus de pixel, só dentro do trecho preenchido.
func _desenhar_listras(cheio: Rect2) -> void:
	var linhas: int = int(cheio.size.y / PIXEL)
	for linha in linhas:
		var x: float = cheio.position.x + fposmod(-linha * PIXEL, PIXEL * 8.0)
		while x < cheio.end.x:
			var largura: float = minf(PIXEL * 4.0, cheio.end.x - x)
			draw_rect(Rect2(x, cheio.position.y + linha * PIXEL, largura, PIXEL), COR_LISTRA)
			x += PIXEL * 8.0


func _trecho(area: Rect2, parte: float) -> Rect2:
	var largura: float = snappedf(area.size.x * parte, PIXEL)
	if parte > 0.0:
		largura = maxf(largura, PIXEL)
	var x: float = area.end.x - largura if da_direita else area.position.x
	return Rect2(x, area.position.y, largura, area.size.y)
