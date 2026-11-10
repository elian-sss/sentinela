extends CharacterBody2D
## Inimigo base (lenhador): anda em linha reta até a árvore e a ataca periodicamente.
## Variantes (ex.: Motosserrista.tscn) herdam esta cena e só mudam os valores no Inspector.

signal morreu(posicao: Vector2)

const CENA_FUMACA: PackedScene = preload("res://cenas/efeitos/Fumaca.tscn")
const CENA_ITEM: PackedScene = preload("res://cenas/item/Item.tscn")

@export var vida: int = 30:
	set = _definir_vida
@export var velocidade: float = 60.0
@export var dano: int = 5
@export var intervalo_ataque: float = 1.0
@export var alcance_ataque: float = 56.0
@export var dano_heroi: int = 10
@export var raio_dano_heroi: float = 40.0
@export var intervalo_dano_heroi: float = 1.0
@export var chance_item: float = 0.15
@export var bonus_chance_por_dano_arvore: float = 0.005
@export var chance_item_maxima: float = 0.4
@export var atrito_empurrao: float = 1500.0 ## quão rápido o empurrão perde força (px/s²)
@export var chance_escudo: float = 0.2 ## entre os itens que caem, fração que é escudo
@export var chance_erva: float = 0.5 ## entre os que não são escudo, fração que é erva

var _arvore: Arvore
var _dano_causado_arvore: int = 0
var _heroi: Heroi
var _tempo_ate_ataque: float = 0.0
var _tempo_ate_dano_heroi: float = 0.0
var _empurrao: Vector2 = Vector2.ZERO
var _cor_original: Color

@onready var _visual: ColorRect = $Visual


func _ready() -> void:
	_arvore = get_tree().get_first_node_in_group("arvore")
	_heroi = get_tree().get_first_node_in_group("heroi")
	_cor_original = _visual.color
	_tempo_ate_ataque = intervalo_ataque


func _physics_process(delta: float) -> void:
	_atacar_heroi_se_perto(delta)

	if _empurrao != Vector2.ZERO:
		_ser_empurrado(delta)
		return

	if _arvore == null or _arvore.esta_destruida():
		velocity = Vector2.ZERO
		return

	if global_position.distance_to(_arvore.global_position) > alcance_ataque:
		velocity = global_position.direction_to(_arvore.global_position) * velocidade
		move_and_slide()
	else:
		velocity = Vector2.ZERO
		_atacar_arvore(delta)


func receber_dano(valor: int) -> void:
	vida -= valor
	Feedback.piscar_branco(self, _visual, _cor_original)


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
func _chance_de_item() -> float:
	return minf(chance_item + _dano_causado_arvore * bonus_chance_por_dano_arvore, chance_item_maxima)


func _talvez_soltar_item() -> void:
	if randf() >= _chance_de_item():
		return
	var item: Item = CENA_ITEM.instantiate()
	item.tipo = _sortear_tipo_item()
	item.position = global_position
	# Adiado: o inimigo costuma morrer dentro de um callback de física, onde não dá para criar áreas.
	get_parent().add_child.call_deferred(item)


func _sortear_tipo_item() -> Item.Tipo:
	if randf() < chance_escudo:
		return Item.Tipo.ESCUDO
	return Item.Tipo.ERVA if randf() < chance_erva else Item.Tipo.FRUTA
