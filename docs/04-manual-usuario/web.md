# Usar la web

La web es la forma de usar la aplicación: desde ella eliges tus favoritos y tus reglas,
generas el equipo para un juego y registras tu *Hall of Fame*.

!!! note "Disponible por ahora"
    **Inicio**, **Catálogo**, la **ficha** de cada Pokémon y **Favoritos**. El resto de
    pantallas (reglas, nuevo juego y *Hall of Fame*) se añadirán en las siguientes versiones;
    mientras tanto, muestran «Esta pantalla todavía no está disponible». Lo que todavía no hace la web
    se puede hacer con la [API](api.md).

## Antes de empezar

- Haber cargado los datos al menos una vez ([cargar los datos](cargar-datos.md)).
- Tener instaladas las dependencias de la web (`cd web && npm ci`;
  [detalle](../05-operacion/web.md#instalar)).

## Abrir la web

Por ahora, la web y la API se arrancan por separado, cada una en su terminal, desde la raíz
del proyecto:

```bash
uv run uvicorn api.main:app --reload
```

```bash
cd web && npm run dev
```

Abre `http://localhost:5173` en el navegador. Para pararlas, `Ctrl+C` en cada terminal.

## Navegar

La barra de arriba lleva a cada sección: **Catálogo**, **Favoritos**, **Reglas**,
**Nuevo juego** y **Hall of Fame**. La sección en la que estás aparece subrayada. El nombre
de la aplicación, a la izquierda, vuelve al Inicio.

Cada pantalla tiene su propia dirección, así que puedes recargar la página, volver atrás con
el navegador o guardar un enlace.

## Inicio

Resume tu situación:

| Apartado | Qué muestra |
|----------|-------------|
| **Nuevo juego** | El acceso para elegir un juego, revisar sus datos y generar el equipo. |
| **Favoritos** | Cuántos favoritos tienes, con un enlace a la lista. Si no tienes ninguno, un enlace al catálogo para añadirlos. |
| **Último juego completado** | El último juego de tu *Hall of Fame*, con su fecha y su equipo. |
| **Datos** | La versión de la aplicación, cuándo se cargaron los datos, cuántos juegos hay cargados (pasa el ratón por encima para ver cuáles) y el *commit* de PokeAPI usado. |

Si acabas de volver a cargar los datos y la fecha de **Datos** no cambia, reinicia la API: sigue
trabajando con la carga anterior hasta que la reinicies.

## Elegir tus favoritos

Tus favoritos son los Pokémon con los que se generan los equipos. Hay una sola lista, común a
todos los juegos.

!!! tip "Añade la evolución a la que quieres llegar"
    Cada favorito es la evolución hasta la que quieres llegar
    ([RN-09](../01-ddf/reglas-negocio.md#rn-09)): añade Butterfree, no Caterpie. Sus
    preevoluciones van incluidas mientras llegas a ella, y sus evoluciones posteriores no se
    proponen salvo que también sean favoritas.

La **estrella** junto a cada Pokémon lo añade a favoritos (☆) o lo quita (★). Está en el
catálogo, en la ficha y en la lista de favoritos, y el cambio se ve enseguida en las tres.

### Catálogo

Todos los Pokémon de los datos cargados, en orden de la Pokédex Nacional, con su número, su
nombre y sus tipos actuales. Las formas regionales, como Vulpix de Alola, aparecen como
entradas propias y se añaden a favoritos por separado.

| Filtro | Qué hace |
|--------|----------|
| **Buscar por nombre** | Deja los que contienen el texto en su nombre, sin distinguir mayúsculas ni tildes. |
| **Tipo** | Deja los que tienen ese tipo. |
| **Favoritos** | **Solo favoritos** o **Sin los favoritos**. |

Los filtros se combinan y se guardan en la dirección de la página: al volver atrás o recargar,
siguen ahí. **Quitar los filtros** vuelve a la lista completa. Pulsa el nombre de un Pokémon para
ver su ficha.

!!! note "Tipos actuales"
    El catálogo y la ficha muestran los tipos de la última generación cargada. Al generar el
    equipo se usan los que tenía en el juego elegido.

### Ficha

El número, el nombre, los tipos, la estrella, la generación en la que apareció y si es
legendario o singular. Debajo, su **línea evolutiva** por etapas, con el Pokémon de la ficha
resaltado y, en cada evolución, cómo se consigue:

| Ejemplo | Significa |
|---------|-----------|
| Nivel 25 | Al llegar al nivel 25. |
| Piedra Trueno | Usando ese objeto. |
| Intercambio llevando Revestimiento metálico | Al intercambiarlo mientras lleva ese objeto. |
| Amistad alta, de día | Al subir de nivel con mucha amistad, de día. |
| Nivel 7, al azar (50 %) | Al nivel 7; la evolución que sale depende del azar. |
| Nivel 30 o Intercambio | Cualquiera de los dos métodos. |

Es el método del juego más reciente cargado que tiene esa evolución. Si la web no conoce un
método, un objeto o una condición, lo muestra con su nombre en inglés de PokeAPI (por ejemplo,
`ice-stone`). Pulsa cualquier Pokémon de la línea para ir a su ficha.

### Favoritos

Tu lista, en orden de la Pokédex Nacional, con cuántos tienes. Pulsa la estrella de uno para
quitarlo.

## Avisos

| Aviso | Qué significa | Qué hacer |
|-------|---------------|-----------|
| **No hay datos cargados** | La API funciona, pero todavía no se han cargado los datos de los juegos. | Ejecuta la carga con `uv run python -m ingest` ([cargar los datos](cargar-datos.md)) y reinicia la API. |
| **La API no responde** | La web no puede comunicarse con la API. | Arráncala con `uv run uvicorn api.main:app --reload` y recarga la página. |

Cuando una parte de una pantalla no se puede mostrar por otro motivo, el mensaje de error
aparece en su lugar y el resto de la pantalla sigue funcionando.
