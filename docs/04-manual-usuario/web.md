# Usar la web

La web es la forma de usar la aplicación: desde ella eliges tus favoritos y tus reglas,
generas el equipo para un juego y registras tu *Hall of Fame*.


## Antes de empezar

- Haber cargado los datos al menos una vez ([cargar los datos](cargar-datos.md)).
- Tener Node 24 y las dependencias de Python (`uv sync`)
  ([entorno de desarrollo](../05-operacion/entorno-desarrollo-macos.md)).

## Abrir la web

La primera vez, y cada vez que actualices la aplicación, compila la web desde la raíz del
proyecto:

```bash
cd web && npm ci && npm run build && cd ..
```

Después, arranca la aplicación:

```bash
uv run uvicorn api.main:app
```

Abre `http://127.0.0.1:8000` en el navegador. Para pararla, `Ctrl+C`.

!!! tip "Mientras desarrollas"
    Para ver los cambios del código al momento, arranca la API con `--reload` y la web con
    `cd web && npm run dev` en otra terminal, y abre `http://localhost:5173`
    ([detalle](../05-operacion/web.md#arrancar-en-desarrollo)).

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

## Configurar las reglas

En **Reglas** decides qué reglas se aplican al generar y cuánto pesa cada una
([RF-06](../01-ddf/requisitos-funcionales.md#rf-06),
[RF-07](../01-ddf/requisitos-funcionales.md#rf-07)). Están agrupadas por clase, cada una con su
identificador (`RN-XX`) y lo que hace. El enlace **reglas de negocio** lleva al documento que
las explica en detalle.

| Clase | Qué hacen | Qué puedes cambiar |
|-------|-----------|--------------------|
| **Reglas duras** | Filtros: un Pokémon o un equipo que no las cumple se descarta. | Las configurables tienen un interruptor **Activa**; las estructurales (como RN-01, «El equipo tiene 6 Pokémon») están siempre activas. |
| **Reglas de presencia** | Obligan a incluir un tipo de miembro: Dragonite o un Dragón (RN-13) y una evolución de Eevee (RN-14). | El interruptor **Activa**. |
| **Reglas blandas** | Puntúan el equipo; la puntuación de cada una se multiplica por su **peso**. | El interruptor y el **Peso**, de 0 a 10. Junto al peso se ve su valor por defecto. |
| **Mecanismos** | Cómo funciona el generador. | Nada: son informativos. |

Los cambios se guardan al momento, valen para todos los juegos y se conservan entre sesiones.
El próximo resultado ya se genera con ellos, y la revisión de datos puede pedir datos nuevos: por
ejemplo, al activar RN-17, los combates clave del juego. Si la API rechaza un cambio, el
mensaje aparece junto a la regla.

## Empezar un juego nuevo

### Elegir el juego

En **Nuevo juego** aparecen los juegos que puedes elegir: los de la saga principal con datos
cargados que permiten la crianza ([RF-05](../01-ddf/requisitos-funcionales.md#rf-05)). Pulsa
uno para revisar sus datos. Cambiar de juego no cambia tus favoritos.

### Revisar los datos

Algunos datos no se han podido cargar con certeza
([RN-18](../01-ddf/reglas-negocio.md#rn-18)). Antes de generar el equipo tienes que
confirmarlos, pero solo los que intervienen con tus favoritos y tus reglas actuales. Aparecen
en tres grupos:

| Grupo | Qué se pregunta | Respuesta |
|-------|-----------------|-----------|
| **Mecánicas del juego** | Si el juego tiene una mecánica, como el ciclo de día y noche. | Sí o No. |
| **Combates clave** | El equipo de un líder o rival, en orden. | La lista de sus Pokémon. |
| **Favoritos** | Si un favorito se puede tener en el juego o si puede llegar a él y evolucionar hasta esa forma antes de completarlo. | Sí o No. |

Cada dato muestra la **propuesta** de la carga, si la hay, y su estado:

| Estado | Significa |
|--------|-----------|
| **Pendiente** | Todavía no lo has confirmado. |
| **Confirmado** | Ya lo confirmaste; no se vuelve a pedir. Puedes cambiar la respuesta cuando quieras. |
| **Desactualizado** | Lo confirmaste, pero una carga posterior propone otro valor: vuelve a confirmarlo. |

Formas de confirmar:

- **Aceptar todas las propuestas**: confirma de una vez todo lo que tiene propuesta. Lo que
  no la tiene se queda pendiente.
- **Sí** o **No** en cada dato: confirma la propuesta o la corrige. El botón de la respuesta
  confirmada aparece resaltado.
- **En un combate clave**: **Confirmar el equipo propuesto**, o **Corregir el equipo** (o
  **Indicar el equipo**, si no hay propuesta). Al corregirlo, quita Pokémon con **Quitar** y
  añádelos al final escribiendo parte del nombre en el buscador y pulsando **Añadir**; el equipo
  tiene hasta 6 en el orden en que los añades. **Guardar el equipo** lo confirma. Si la API lo
  rechaza (por ejemplo, porque un Pokémon no existe en la generación del juego), el mensaje
  aparece debajo y puedes corregirlo.

Por ejemplo, si Raichu es favorito, en Rojo Fuego se propone que **No** puede llegar antes de
completar el juego, porque de su huevo nace Pichu y Pichu no aparece en la Pokédex de Kanto. Si
lo confirmas, Raichu no entrará en el equipo.

Cuando todo está confirmado, aparece **Generar el equipo**. Las confirmaciones se guardan por
juego: la próxima vez solo se piden los datos nuevos, por ejemplo, los de un favorito que
acabas de añadir.

!!! warning "Aviso"
    Los datos que confirmas se usan tal cual. Si confirmas uno erróneo, el equipo propuesto
    puede ser inexacto ([responsabilidad sobre los datos confirmados](index.md#responsabilidad-sobre-los-datos-confirmados)).

### Ver el resultado

Al abrir el resultado se generan los equipos con tus favoritos, tus reglas y los datos que
confirmaste. No se guarda nada: es un cálculo, y con los mismos datos da siempre el mismo
resultado. **Volver a generar** lo repite. Si falta algún dato por confirmar (por ejemplo,
porque acabas de añadir un favorito), te lleva a la revisión.

| Apartado | Qué muestra |
|----------|-------------|
| **Estado** | Si el equipo está **completo** (6 favoritos) o **incompleto** y por qué, y su **puntuación**. Si varios equipos empatan en cabeza, cuántos son. |
| **Equipo recomendado** u **Opción N** | Sus posiciones, con el número, el nombre y los tipos en el juego. Una posición como «Cloyster o Lapras» significa que cualquiera de los dos da la misma puntuación: es un grupo de equipos y eliges uno de cada posición. |
| **Puntuación por regla** | Cada regla blanda activa con su peso, cuánto la cumple el equipo (en %), lo que aporta al total y qué miembros cuentan en contra. Las aportaciones suman el total ([RF-09](../01-ddf/requisitos-funcionales.md#rf-09)). |
| **Huecos** | Si el equipo es incompleto: los huecos reservados por una regla de presencia y los libres, cada uno con sus **sugerencias**, de mejor a peor, con lo que aportarían (`+3`). Se ven las 5 primeras; **Ver N sugerencias más** muestra el resto. |
| **Favoritos descartados** | Cuántos favoritos se han descartado y por qué, agrupados por motivo. Si lo decidió un dato que confirmaste, enlaza a la revisión. |
| **Reglas de presencia** | Cómo se aplica cada una (RN-13, RN-14): si se cumple con tus favoritos, si se le reserva un hueco o si no se puede cumplir en el juego, y qué Pokémon la cumplen. |
| **Datos que confirmaste** | Los datos confirmados que se han usado, con un enlace para cambiarlos. |

Las sugerencias no son favoritos. Las marcadas **Sin verificar** dependen de datos que no has
confirmado ([RN-18](../01-ddf/reglas-negocio.md#rn-18)). Con la **estrella** de una sugerencia
la añades a favoritos y el resultado se vuelve a generar con ella (si trae datos nuevos que
confirmar, primero pasas por la revisión). Con varios huecos libres, cada sugerencia encaja con
el equipo, pero no necesariamente con las demás.

!!! note "Puntuaciones redondeadas"
    Las puntuaciones se muestran como enteros. Dos equipos con el mismo número no tienen por
    qué estar empatados: el orden se decide con los valores exactos.

### Elegir el equipo y registrarlo

Debajo de los equipos, **Elegir el equipo** te deja quedarte con uno y registrarlo en tu
*Hall of Fame* como el equipo con el que vas a completar el juego
([RF-12](../01-ddf/requisitos-funcionales.md#rf-12)):

1. Si hay varias **opciones**, elige una.
2. En cada **posición** con alternativas (por ejemplo, «Cloyster o Lapras»), elige un Pokémon.
3. Si el equipo es incompleto, elige una **sugerencia para cada hueco**. No puedes elegir dos
   veces el mismo Pokémon. **Equipo elegido** muestra cómo queda.
4. Revisa la **fecha** (hoy, por defecto) y añade **notas** si quieres.
5. Pulsa **Comprobar y registrar**.

La aplicación comprueba el equipo con tus reglas. Es necesario porque dos sugerencias pueden
encajar cada una con el equipo, pero no entre sí (por ejemplo, si comparten tipo). Si tiene
algún problema, lo explica y **no se registra**: cambia la elección y vuelve a probar. Los
Pokémon con datos sin confirmar se indican, pero no impiden registrarlo.

Al registrarlo, el equipo cuenta para tu recorrido desde ese momento: el resultado se vuelve a
generar sin sus líneas evolutivas ([RN-16](../01-ddf/reglas-negocio.md#rn-16)). Si después
quieres cambiar la fecha o el equipo, hazlo en el [*Hall of Fame*](#hall-of-fame).

Si no te convence ninguno, **Descartar los equipos** no registra nada.

## Hall of Fame

Tu **recorrido**: los juegos que has completado y su equipo, ordenados por fecha y, si dos
coinciden, por orden de registro ([RF-12](../01-ddf/requisitos-funcionales.md#rf-12),
[RF-13](../01-ddf/requisitos-funcionales.md#rf-13)). El **último juego completado** aparece
señalado. Cada miembro muestra los tipos que tenía en ese juego.

El recorrido decide qué Pokémon se excluyen al generar
([RN-16](../01-ddf/reglas-negocio.md#rn-16)): las líneas evolutivas del último juego completado
y las de los juegos de la misma generación que el que vas a jugar. Por eso, registrar, corregir
o eliminar un registro cambia los equipos que se generan a partir de ese momento.

| Acción | Cómo |
|--------|------|
| **Filtrar por juego** | Elige el juego en **Juego**. El filtro se guarda en la dirección de la página. |
| **Registrar un equipo** | Además de hacerlo desde el resultado, puedes registrar a mano cualquier juego cargado, también los que no pueden ser juego objetivo (como Rojo u Oro). Elige el juego, la fecha y, si quieres, notas, y añade de 1 a 6 Pokémon con el buscador, en orden. **Guardar** lo registra. |
| **Corregir** | Cambia el juego, la fecha, las notas o el equipo. Si cambias la fecha, el recorrido se reordena. |
| **Eliminar** | Pide confirmación: **Sí, eliminar** borra el registro y su equipo. |

Si la API rechaza un registro (por ejemplo, un Pokémon que no existía en la generación de ese
juego), el mensaje aparece en el formulario y puedes corregirlo.

## Avisos

| Aviso | Qué significa | Qué hacer |
|-------|---------------|-----------|
| **No hay datos cargados** | La API funciona, pero todavía no se han cargado los datos de los juegos. | Ejecuta la carga con `uv run python -m ingest` ([cargar los datos](cargar-datos.md)) y reinicia la API. |
| **La API no responde** | La web no puede comunicarse con la API (solo pasa mientras desarrollas, con la web aparte). | Arráncala con `uv run uvicorn api.main:app --reload` y recarga la página. |

Cuando una parte de una pantalla no se puede mostrar por otro motivo, el mensaje de error
aparece en su lugar y el resto de la pantalla sigue funcionando.
