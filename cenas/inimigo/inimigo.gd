extends CharacterBody2D
## Inimigo base: anda em linha reta até a árvore e a ataca periodicamente.
## Os números de cada tipo vêm de Balanceamento.INIMIGOS[tipo]. Variantes (ex.: Motosserrista.tscn)
## herdam esta cena e só mudam o `tipo` e a cor.

signal morreu(posicao: Vector2)

const CENA_FUMACA: PackedScene = preload("res://cenas/efeitos/Fumaca.tscn")
const CENA_ITEM: PackedScene = preload("res://cenas/item/Item.tscn")

@export var tipo: String = "lenhador" ## chave em Balanceamento.INIMIGOS
@export var atrito_empurrao: float = 1500.0 ## quão rápido o empurrão perde força (px/s²)

var vida: int = 0:
	set = _definir_vida
var velocidade: float = 0.0
var dano: int = 0
var intervalo_ataque: float = 0.0
var alcance_ataque: float = 0.0
var dano_heroi: int = 0
var raio_dano_heroi: float = 0.0
var intervalo_dano_heroi: float = 0.0
var chance_item: float = Balanceamento.DROP_CHANCE_BASE
var bonus_chance_por_dano_arvore: float = Balanceamento.DROP_BONUS_POR_DANO_ARVORE
var chance_item_maxima: float = Balanceamento.DROP_CHANCE_MAXIMA

var _arvore: Arvore
var _dano_causado_arvore: int = 0
var _heroi: Heroi
var _tempo_ate_ataque: float = 0.0
var _tempo_ate_dano_heroi: float = 0.0
var _empurrao: Vector2 = Vector2.ZERO

@onready var _visual: AnimatedSprite2D = $Visual


func _ready() -> void:
	_aplicar_balanceamento()
	_arvore = get_tree().get_first_node_in_group("arvore")
	_heroi = get_tree().get_first_node_in_group("heroi")
	_tempo_ate_ataque = intervalo_ataque


func _physics_process(delta: float) -> void:
	_atacar_heroi_se_perto(delta)

	if _empurrao != Vector2.ZERO:
		_ser_empurrado(delta)
		return

	if _arvore == null or _arvore.esta_destruida():
		velocity = Vector2.ZERO
		return

	_visual.flip_h = _arvore.global_position.x < global_position.x
	if global_position.distance_to(_arvore.global_position) > alcance_ataque:
		velocity = global_position.direction_to(_arvore.global_position) * velocidade
		move_and_slide()
		_visual.play("andando")
	else:
		velocity = Vector2.ZERO
		_atacar_arvore(delta)
		_visual.play("atacando")


## Copia os números do tipo (vida, velocidade, danos...) para as variáveis de mesmo nome.
func _aplicar_balanceamento() -> void:
	var valores: Dictionary = Balanceamento.INIMIGOS[tipo]
	for nome: String in valores:
		set(nome, valores[nome])


func receber_dano(valor: int) -> void:
	Feedback.numero(self, str(valor), Feedback.COR_DANO)
	Feedback.piscar_branco(self, _visual)
	vida -= valor


func empurrar(impulso: Vector2) -> void:
	_empurrao = impulso


## Enquanto o empurrão dura, o inimigo só desliza e não anda nem ataca a árvore.
func _ser_empurrado(delta: float) -> void:
	velocity = _empurrao
	move_and_slide()
	_empurrao = _empurrao.move_toward(Vector2.ZERO, atrito_empurrao * delta)


func _atacar_arvore(delta: float) -> void:
	_tempo_ate_ataque -= delta
	if _tempo_ate_ataque <= 0.0:
		_arvore.receber_dano(dano)
		_dano_causado_arvore += dano
		_tempo_ate_ataque = intervalo_ataque


## Enquanto o herói estiver dentro do raio, causa dano a cada intervalo.
func _atacar_heroi_se_perto(delta: float) -> void:
	_tempo_ate_dano_heroi = maxf(_tempo_ate_dano_heroi - delta, 0.0)
	if _heroi == null or _tempo_ate_dano_heroi > 0.0:
		return
	if global_position.distance_to(_heroi.global_position) <= raio_dano_heroi:
		_heroi.receber_dano(dano_heroi)
		_tempo_ate_dano_heroi = intervalo_dano_heroi


func _definir_vida(valor: int) -> void:
	vida = maxi(valor, 0)
	if vida == 0 and is_inside_tree() and not is_queued_for_deletion():
		morreu.emit(global_position)
		_soltar_fumaca()
		_talvez_soltar_item()
		queue_free()


func _soltar_fumaca() -> void:
	var fumaca: Node2D = CENA_FUMACA.instantiate()
	get_parent().add_child(fumaca)
	fumaca.global_position = global_position


## Quem já bateu mais na árvore tem mais chance de soltar item, até o limite.
## Com o herói ferido, a chance sobe mais um pouco (além do limite).
func _chance_de_item() -> float:
	var chance: float = minf(chance_item + _dano_causado_arvore * bonus_chance_por_dano_arvore, chance_item_maxima)
	return chance + _falta_de_vida_do_heroi() * Balanceamento.DROP_BONUS_CHANCE_VIDA_BAIXA


## 0 com a vida cheia, 1 com a vida zerada.
func _falta_de_vida_do_heroi() -> float:
	if _heroi == null:
		return 0.0
	return 1.0 - float(_heroi.vida_atual) / _heroi.vida_maxima


func _talvez_soltar_item() -> void:
	if randf() >= _chance_de_item():
		return
	var item: Item = CENA_ITEM.instantiate()
	item.tipo = _sortear_tipo_item()
	item.position = global_position
	# Adiado: o inimigo costuma morrer dentro de um callback de física, onde não dá para criar áreas.
	get_parent().add_child.call_deferred(item)


## Sorteio por peso, com os pesos de Balanceamento.DROP_PESO_*. A fruta pesa mais com o herói ferido.
func _sortear_tipo_item() -> Item.Tipo:
	var multiplicador_fruta: float = lerpf(1.0, Balanceamento.DROP_MULTIPLICADOR_FRUTA_VIDA_BAIXA, _falta_de_vida_do_heroi())
	var pesos: Dictionary = {
		Item.Tipo.FRUTA: Balanceamento.DROP_PESO_FRUTA * multiplicador_fruta,
		Item.Tipo.ERVA: Balanceamento.DROP_PESO_ERVA,
		Item.Tipo.ESCUDO: Balanceamento.DROP_PESO_ESCUDO,
		Item.Tipo.VELOCIDADE: Balanceamento.DROP_PESO_VELOCIDADE,
		Item.Tipo.FORCA: Balanceamento.DROP_PESO_FORCA,
	}
	var sorteio: float = randf() * pesos.values().reduce(func(soma: float, peso: float) -> float: return soma + peso, 0.0)
	for tipo_item: Item.Tipo in pesos:
		sorteio -= pesos[tipo_item]
		if sorteio < 0.0:
			return tipo_item
	return Item.Tipo.FRUTA
