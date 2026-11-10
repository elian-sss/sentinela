class_name Recorde
## Maior onda alcançada no modo infinito, salva em user:// (no navegador, fica no IndexedDB).

const CAMINHO: String = "user://recorde.cfg"


static func carregar() -> int:
	var arquivo := ConfigFile.new()
	if arquivo.load(CAMINHO) != OK:
		return 0
	return arquivo.get_value("infinito", "onda", 0)


## Salva se for maior que o recorde atual. Devolve true quando é um novo recorde.
static func registrar(onda: int) -> bool:
	if onda <= carregar():
		return false
	var arquivo := ConfigFile.new()
	arquivo.set_value("infinito", "onda", onda)
	arquivo.save(CAMINHO)
	return true
