# Usar la web

La web es la forma de usar la aplicación: desde ella eliges tus favoritos y tus reglas,
generas el equipo para un juego y registras tu *Hall of Fame*.


## Antes de empezar

- Haber cargado los datos al menos una vez ([cargar los datos](cargar-datos.md)).
- Tener Node 24 y las dependencias de Python (`uv sync`)
  ([entorno de desarrollo](../05-operacion/entorno-desarrollo-macos.md)).

## Abrir la web

La forma más sencilla, la primera vez y cada vez que actualices la aplicación, es un solo
comando desde la raíz del proyecto:

```bash
scripts/start.sh
```

Hace, por orden:

1. Una copia de seguridad de tus datos (`data/user.sqlite`) en `data/backups/`, con la fecha y
   la hora en el nombre.
2. Instala las dependencias de Python (`uv sync`).
3. Carga los datos ([cargar los datos](cargar-datos.md)). Acepta sus opciones, como
   `--offline` o `--no-covers`: `scripts/start.sh --offline`.
4. Instala las dependencias de la web y la compila (`npm ci` y `npm run build`).
5. Arranca la aplicación en `http://127.0.0.1:8000`.

Si un paso falla, se detiene, dice cuál ha sido y no arranca la aplicación; si falla la carga,
se conservan los datos anteriores. `PTB_PORT` cambia el puerto: `PTB_PORT=8080 scripts/start.sh`.

También puedes hacer los pasos a mano. Compila la web desde la raíz del proyecto:

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
**Nuevo juego**, **Hall of Fame** y **Pokédex**. La sección en la que estás aparece subrayada. El nombre
de la aplicación, a la izquierda, vuelve al Inicio.

Cada pantalla tiene su propia dirección, así que puedes recargar la página, volver atrás con
el navegador o guardar un enlace.

### Imágenes de los Pokémon

Cada Pokémon se muestra con su imagen junto al nombre: en el catálogo, la ficha y su línea
evolutiva, los favoritos, el resultado (las posiciones y las sugerencias), el selector del
equipo y el *Hall of Fame*. Cada forma tiene la suya: Vulpix y Vulpix de Alola se distinguen.
En las listas es su *sprite*, recortado para que se vea bien a tamaño pequeño; en la cabecera de
la ficha, su ilustración oficial, más grande.

- La imagen **acompaña** al nombre, no lo sustituye: el nombre sigue siendo lo que identifica al
  Pokémon, también para los lectores de pantalla.
- Si un Pokémon no tiene imagen (la carga no pudo descargarla) o no se puede cargar, se muestra
  igual, solo con su nombre.
- Las imágenes las descarga la [carga de datos](cargar-datos.md) a tu ordenador y las sirve la
  propia aplicación, así que funcionan sin conexión
  ([de quién son](index.md#imagenes-y-portadas-de-quien-son-y-como-se-usan)).

### Portadas de los juegos

Cada juego se muestra con su portada junto al nombre: en las tarjetas de **Nuevo juego**, en la
cabecera de la revisión de datos y del resultado, en el último juego completado del **Inicio** y
en cada registro del **Hall of Fame**, también de los juegos que no pueden ser juego objetivo,
como Rojo ([RF-18](../01-ddf/requisitos-funcionales.md#rf-18)).

- Como las imágenes de los Pokémon, la portada **acompaña** al nombre del juego, se ajusta a un
  tamaño fijo sin deformarse y, si un juego no la tiene, se muestra solo con su nombre.
- Son **solo para tu uso privado** y se pueden quitar con `--no-covers`
  ([de quién son y cómo se usan](index.md#imagenes-y-portadas-de-quien-son-y-como-se-usan)).

### Aviso de titularidad

Al pie de cada pantalla está el aviso de la titularidad y la procedencia de las imágenes, las
portadas y los datos, con un enlace a la página de cada portada en WikiDex. Si no hay ninguna
portada cargada, no dice nada de ellas.

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
catálogo, en la ficha y en la lista de favoritos, y el cambio se ve enseguida en las tres. En las
listas queda siempre a la derecha de cada fila; en el móvil, el número y el nombre van arriba y
los tipos debajo.

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
| **Reglas de presencia** | Obligan a incluir un tipo de miembro: Dragonite o un Dragón (RN-13), una evolución de Eevee (RN-14) y un inicial del juego (RN-21). Si ningún favorito cumple RN-13 o RN-14, se reserva un hueco con sugerencias; si ningún inicial es favorito, RN-21 elige uno del juego. | El interruptor **Activa**. |
| **Reglas blandas** | Puntúan el equipo; la puntuación de cada una se multiplica por su **peso**. | El interruptor y el **Peso**, de 0 a 10. Junto al peso se ve su valor por defecto. |
| **Mecanismos** | Cómo funciona el generador. | Nada: son informativos. |

Los cambios se guardan al momento, valen para todos los juegos y se conservan entre sesiones.
El próximo resultado ya se genera con ellos, y la revisión de datos puede pedir datos nuevos: por
ejemplo, al activar RN-17, los combates clave del juego. Si la API rechaza un cambio, el
mensaje aparece junto a la regla.

## Empezar un juego nuevo

### Elegir el juego

En **Nuevo juego** aparecen los juegos que puedes elegir: los juegos completos, que permiten la
crianza y tienen todos los datos que necesitan las reglas
([RF-05](../01-ddf/requisitos-funcionales.md#rf-05)), salvo los que ya están en tu *Hall of
Fame*, porque cada juego se completa una sola vez
([CA-68](../01-ddf/cuestiones-abiertas.md#resueltas)). Hoy son Rojo Fuego y Verde Hoja; Rubí,
Zafiro y Esmeralda no aparecen hasta tener sus combates clave, aunque sí puedes registrarlos en
el **Hall of Fame**. Pulsa uno para revisar sus datos. Cambiar de juego no cambia tus favoritos.

### Revisar los datos

Algunos datos no se han podido cargar con certeza
([RN-18](../01-ddf/reglas-negocio.md#rn-18)). Antes de generar el equipo tienes que
confirmarlos, pero solo los que intervienen con tus favoritos y tus reglas actuales. Aparecen
en tres grupos:

| Grupo | Qué se pregunta | Respuesta |
|-------|-----------------|-----------|
| **Mecánicas del juego** | Si el juego tiene una mecánica, como el ciclo de día y noche. | Sí o No. |
| **Combates clave** | El equipo de un líder o rival, en orden. | La lista de sus Pokémon. |
| **Favoritos e iniciales del juego** | Si un favorito se puede tener en el juego o si puede llegar a él y evolucionar hasta esa forma antes de completarlo. Con RN-21 activa, lo mismo de los iniciales del juego, aunque no sean favoritos, porque la regla puede elegir uno. | Sí o No. |

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
  aparece debajo y puedes corregirlo. Si se conoce de dónde sale el equipo, **Fuente: WikiDex**
  enlaza a la versión de su página que usó la carga, para que lo compruebes.

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
| **Equipo recomendado** u **Opción N** | Sus posiciones, con el número, el nombre y los tipos en el juego. Una posición como «Cloyster o Lapras» significa que cualquiera de los dos da la misma puntuación: es un grupo de equipos y eliges uno de cada posición. Si el inicial no está en tus favoritos, su posición dice «No es favorito: lo elige RN-21». |
| **Puntuación por regla** | Cada regla blanda activa con su peso, cuánto la cumple el equipo (en %), lo que aporta al total y qué miembros cuentan en contra. Las aportaciones suman el total ([RF-09](../01-ddf/requisitos-funcionales.md#rf-09)). |
| **Huecos** | Si el equipo es incompleto: los huecos reservados por una regla de presencia y los libres, cada uno con sus **sugerencias**, de mejor a peor, con lo que aportarían (`+3`). Se ven las 5 primeras; **Ver N sugerencias más** muestra el resto. |
| **Favoritos descartados** | Cuántos favoritos se han descartado y por qué, agrupados por motivo. Si lo decidió un dato que confirmaste, enlaza a la revisión. |
| **Reglas de presencia** | Cómo se aplica cada una (RN-13, RN-14, RN-21): si se cumple con tus favoritos o con un Pokémon del juego que no es favorito, si se le reserva un hueco o si no se puede cumplir en el juego, y qué Pokémon la cumplen. |
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

Al registrarlo, el juego queda **completado**: cada juego se registra una sola vez, así que deja
de aparecer en **Nuevo juego** y el resultado ya no se vuelve a generar
([CA-68](../01-ddf/cuestiones-abiertas.md#resueltas)). Su equipo cuenta para tu recorrido desde
ese momento ([RN-16](../01-ddf/reglas-negocio.md#rn-16)). Si después quieres cambiar la fecha o
el equipo, hazlo en el [*Hall of Fame*](#hall-of-fame); para volver a jugar ese juego, elimina
antes su registro.

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
| **Registrar un equipo** | Además de hacerlo desde el resultado, puedes registrar a mano cualquier juego cargado, también los que no pueden ser juego objetivo (como Rojo, Oro o Rubí). Cada juego se registra una sola vez: los que ya están en tu *Hall of Fame* no aparecen. Elige el juego, la fecha y, si quieres, notas, y añade de 1 a 6 Pokémon con el buscador, en orden. **Guardar** lo registra. |
| **Corregir** | Cambia el juego, la fecha, las notas o el equipo. Si cambias la fecha, el recorrido se reordena. Si cambias el juego, se borra la [Pokédex](#pokedex) del anterior: si ya la habías empezado, el formulario te avisa antes de guardar. |
| **Eliminar** | Pide confirmación: **Sí, eliminar** borra el registro, su equipo y la [Pokédex](#pokedex) de ese juego. Si ya la habías empezado, la confirmación dice cuántos Pokémon tenía registrados. |

Si la API rechaza un registro (por ejemplo, un Pokémon que no existía en la generación de ese
juego), el mensaje aparece en el formulario y puedes corregirlo.

## Pokédex

Cada juego que has superado, es decir, que está en tu [Hall of Fame](#hall-of-fame), tiene su
Pokédex, para completarla y conseguir el diploma
([RF-20](../01-ddf/requisitos-funcionales.md#rf-20) a
[RF-24](../01-ddf/requisitos-funcionales.md#rf-24)). **Pokédex** muestra esos juegos con su
progreso: el porcentaje de registrados, cuántos llevas, si está **no iniciada**, **en curso** o
**completada**, y cuántos son imposibles de obtener. Los imposibles cuentan en el total, así que
el 100 % solo llega con la Pokédex completa
([RN-22](../01-ddf/reglas-negocio.md#rn-22)).

### La primera vez: los que ya tienes

Al abrir la Pokédex de un juego por primera vez, aparece la lista de todos sus Pokémon, en el
orden de su Pokédex. Marca los que ya tienes registrados (capturados u obtenidos, no solo
vistos); **Buscar por nombre** filtra la lista. **Confirmar** los guarda. Esta lista solo
aparece una vez: después, los errores se corrigen en el [detalle](#el-detalle-registrados-e-imposibles).

### El siguiente Pokémon

Después, la Pokédex te propone el **siguiente Pokémon que registrar**: el primero, en el orden
de la Pokédex, que no tienes ni es imposible de obtener
([RN-23](../01-ddf/reglas-negocio.md#rn-23)). Su ficha dice la forma más sencilla de
obtenerlo ([RN-24](../01-ddf/reglas-negocio.md#rn-24) a
[RN-26](../01-ddf/reglas-negocio.md#rn-26)), por ejemplo:

- **Evolucionar Ivysaur: Nivel 32**, si es una fase posterior.
- **Criarlo desde tu Pikachu**, si ya tienes una fase posterior de su línea (desde la
  2.ª generación).
- **Transferirlo desde Verde Hoja**, si lo tienes registrado en la Pokédex de otro juego superado
  o se obtiene en otro juego compatible.
- **Regalo en Ciudad Azulona**, **Aparece salvaje en la Ruta 29 (noche): 50 %** o
  **Pokémon errante si elegiste a Squirtle**, si se obtiene en el propio juego.
- **Pokémon obtenido por evento**.

Si la forma parte de un Pokémon que no tienes (evolucionarlo o criarlo), **Cómo obtener…** lleva
a la ficha de ese Pokémon.

| Acción | Qué hace |
|--------|----------|
| **Registrado** | Lo marca como registrado y pasa al siguiente. |
| **Imposible de obtener** | Lo marca como imposible: cuenta aparte y no vuelve a proponerse. |
| **Otras formas de obtenerlo** | Muestra todas, de la más sencilla a la menos. **Elegir esta** guarda la que prefieres (por ejemplo, si ya no tienes el Pokémon del juego desde el que se propone transferirlo): desde entonces la ficha la muestra primero, como **Elegida por ti**. **Volver a la recomendada** lo deshace. |
| **Saltar de momento** | Pasa al siguiente sin guardar nada. Al volver a entrar en la Pokédex, el siguiente vuelve a ser el primero que te falta. |

Si no se conoce ninguna forma de obtenerlo en ese juego, la ficha lo dice: márcalo como
imposible si no puedes conseguirlo. Los que solo se obtienen en spin-offs, como los discos de
Colosseum, son imposibles por sí solos ([RN-25](../01-ddf/reglas-negocio.md#rn-25)).

### El detalle: registrados e imposibles

**Ver los registrados y los imposibles** lista los Pokémon que has registrado y los que son
imposibles de obtener. **Desmarcar** corrige un error: el Pokémon vuelve a quedar pendiente.
Los que solo se obtienen en spin-offs no se pueden desmarcar. Cada nombre lleva a su ficha.

## Avisos

| Aviso | Qué significa | Qué hacer |
|-------|---------------|-----------|
| **Hay que cargar los datos** | La API funciona, pero todavía no se han cargado los datos de los juegos, o se cargaron con una versión anterior de la aplicación. | Ejecuta la carga con `uv run python -m ingest` ([cargar los datos](cargar-datos.md)) y reinicia la API. |
| **La API no responde** | La web no puede comunicarse con la API (solo pasa mientras desarrollas, con la web aparte). | Arráncala con `uv run uvicorn api.main:app --reload` y recarga la página. |

Cuando una parte de una pantalla no se puede mostrar por otro motivo, el mensaje de error
aparece en su lugar y el resto de la pantalla sigue funcionando.
