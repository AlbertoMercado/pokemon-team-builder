# Extracto del volcado CSV de PokeAPI para los tests

**Qué es**: un extracto real de los CSV de PokeAPI del commit fijado
(`bc92d3b6029ef1abe9e7ad424c400b338f3c11fe`), con la misma estructura de carpetas que la caché
de la ingesta (`<commit>/<fichero>.csv`).

**Por qué existe**: los tests de la ingesta nunca usan la red
([estrategia de pruebas](../../../../docs/02-ddt/arquitectura.md#estrategia-de-pruebas)). Con
datos reales, los tests comprueban las transformaciones con los mismos casos que la carga
completa, pero en milisegundos.

**Qué contiene**: los ficheros pequeños completos (generaciones, versiones, tipos, eficacias,
Pokédex, métodos y condiciones de aparición…) y los grandes filtrados a unas 70 especies
elegidas por sus casos especiales. Las apariciones, además, solo de los 11 juegos cargados, y los
lugares, solo los de esas apariciones:

| Especies | Caso |
|----------|------|
| Bulbasaur, Ivysaur, Venusaur | Subir de nivel |
| Pichu, Pikachu, Raichu | Bebé, amistad, objeto y filas de Raichu de Alola (forma no cargada) |
| Cleffa, Clefairy, Clefable | Tipo Normal hasta la 5.ª generación |
| Zubat, Golbat, Crobat | Crobat es una evolución de la 2.ª generación: no llega a Rojo Fuego |
| Slowpoke, Slowbro, Slowking | Intercambio con objeto y filas de formas de Galar |
| Magnemite, Magneton | Solo Eléctrico en la 1.ª generación |
| Gastly, Haunter, Gengar | Intercambio |
| Happiny, Chansey, Blissey | Happiny es de la 4.ª generación: no se carga y Chansey queda como base |
| Ditto | Grupo huevo `ditto` |
| Eevee y sus evoluciones hasta la 2.ª generación | Piedras, amistad y hora del día |
| Mewtwo | Legendario |
| Azurill, Marill, Azumarill | Bebé de incienso de la 3.ª generación |
| Wynaut, Wobbuffet | El otro bebé de incienso de la 3.ª generación |
| Tyrogue y sus evoluciones | Comparación de estadísticas |
| Wurmple y sus evoluciones | Evolución aleatoria |
| Nincada, Ninjask, Shedinja | Muda (`shed`) |
| Feebas, Milotic | Belleza y, en generaciones posteriores, intercambio con objeto |
| Deoxys | Forma por defecto `deoxys-normal`; sus otras formas no se cargan. Estático en la Isla Origen |
| Ekans, Sandshrew | Salvaje en Rojo Fuego; Sandshrew no aparece (exclusivo de Verde Hoja) |
| Voltorb, Electrode | Varios Voltorb estáticos en la Central de Energía de Amarillo: la probabilidad unida se limita al 100 % |
| Lapras | Regalo y surf en Rojo Fuego |
| Omanyte, Kabuto, Aerodactyl | Fósiles: regalos con la condición del fósil |
| Snorlax, Zapdos | Poké Flauta y estático |
| Mew | De evento: sin apariciones |
| Hoothoot | Solo de noche en Oro: una aparición por momento del día |
| Togepi | Huevo de regalo |
| Raikou, Entei, Suicune | Errantes; en Rojo Fuego, según el inicial |
| Lugia | Estático en la Roca Ombligo, a la que solo se llega con un objeto de evento |
| Celebi, Jirachi | Singulares de evento, con métodos de spin-offs |

**Cómo se regenera** (por ejemplo, al cambiar el commit fijado o la lista de especies):

1. Ejecutar una carga real para tener el volcado completo en la caché:
   `uv run python -m ingest --data-dir /tmp/datos`.
2. Generar el extracto:
   `uv run python tests/ingest/fixtures/pokeapi/extract_pokeapi.py /tmp/datos/cache/pokeapi/<commit>`.
3. Si cambia el commit, actualizar también `COMMIT` en `extract_pokeapi.py` y en los tests.
