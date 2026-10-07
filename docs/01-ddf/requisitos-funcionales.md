# Requisitos funcionales

Prioridades según [MoSCoW](index.md#convenciones). La clasificación inicial sigue la idea de
partida:

- Las funcionalidades **principales** son **Must**.
- Las de **apoyo** son **Should**.
- Las **deseadas** son **Could**.

Hay dos excepciones:

- La carga de datos (RF-11) se ha subido a **Must**, empezando con un conjunto pequeño de datos
  ([CA-02](cuestiones-abiertas.md#resueltas)).
- El *Hall of Fame* (RF-12 y RF-13) se ha subido a **Must**, porque guarda el recorrido del
  que depende [RN-16](reglas-negocio.md#rn-16).

## Resumen

| ID | Requisito | Módulo | Prioridad |
|----|-----------|--------|-----------|
| [RF-01](#rf-01) | Listar Pokémon | Catálogo | Should |
| [RF-02](#rf-02) | Consultar la ficha de un Pokémon | Catálogo | Should |
| [RF-03](#rf-03) | Añadir o quitar favoritos desde el catálogo | Catálogo | Should |
| [RF-04](#rf-04) | Gestionar la lista de favoritos | Favoritos | Must |
| [RF-05](#rf-05) | Seleccionar el juego objetivo | Reglas | Must |
| [RF-06](#rf-06) | Configurar las reglas duras | Reglas | Must |
| [RF-07](#rf-07) | Configurar las reglas blandas y sus pesos | Reglas | Must |
| [RF-08](#rf-08) | Generar equipos | Generación | Must |
| [RF-09](#rf-09) | Explicar el equipo generado | Generación | Should |
| [RF-10](#rf-10) | Mostrar el equipo incompleto con sugerencias | Generación | Must |
| [RF-11](#rf-11) | Cargar y actualizar los datos | Datos | Must |
| [RF-12](#rf-12) | Registrar un equipo en el Hall of Fame | Hall of Fame | Must |
| [RF-13](#rf-13) | Consultar el Hall of Fame | Hall of Fame | Must |
| [RF-14](#rf-14) | Cargar reglas definidas por el usuario | Reglas | Could |
| [RF-15](#rf-15) | Revisar los datos del juego objetivo | Reglas | Must |
| [RF-16](#rf-16) | Informar de las cargas bloqueadas | Datos | Must |
| [RF-17](#rf-17) | Mostrar imágenes de los Pokémon | Imágenes | Could |
| [RF-18](#rf-18) | Mostrar la portada de los juegos | Imágenes | Could |
| [RF-19](#rf-19) | Proteger el acceso a la aplicación | Seguridad | Could |
| [RF-20](#rf-20) | Consultar el progreso de las Pokédex | Pokédex | Must |
| [RF-21](#rf-21) | Marcar los Pokémon ya registrados | Pokédex | Must |
| [RF-22](#rf-22) | Ficha del Pokémon objetivo | Pokédex | Must |
| [RF-23](#rf-23) | Elegir otra forma de obtención | Pokédex | Must |
| [RF-24](#rf-24) | Revisar los registrados y los imposibles | Pokédex | Must |

## Catálogo

### RF-01 · Listar Pokémon { #rf-01 }

- **Prioridad**: Should
- **Descripción**: el usuario ve el listado de Pokémon disponibles en la aplicación, con el
  número de la Pokédex nacional, el nombre y el tipo o tipos de cada uno.
- **Criterios de aceptación**:
    - Se puede buscar por nombre.
    - Se puede filtrar por tipo.
    - Cada Pokémon indica si está en favoritos.
    - Las formas regionales aparecen como entradas propias e identificadas claramente
      (p. ej., «Vulpix» y «Vulpix de Alola») ([RN-05](reglas-negocio.md#rn-05)).

### RF-02 · Consultar la ficha de un Pokémon { #rf-02 }

- **Prioridad**: Should
- **Descripción**: desde el listado se accede a una ficha con los datos básicos del Pokémon.
- **Criterios de aceptación**: la ficha muestra al menos:
    - Número y nombre.
    - Tipo o tipos, los actuales. En la generación de equipos se usan los del juego objetivo
      ([RN-10](reglas-negocio.md#rn-10)).
    - Línea evolutiva completa.
    - Mecanismo de cada evolución.

### RF-03 · Añadir o quitar favoritos desde el catálogo { #rf-03 }

- **Prioridad**: Should
- **Descripción**: el usuario añade un Pokémon a favoritos, o lo quita, directamente desde el
  listado y desde la ficha. Lo que se añade es esa forma y esa evolución concretas: la evolución
  hasta la que se quiere llegar ([RN-05](reglas-negocio.md#rn-05),
  [RN-09](reglas-negocio.md#rn-09)).
- **Criterios de aceptación**: el cambio se refleja al momento en el listado, en la ficha y en
  la lista de favoritos.

## Favoritos

### RF-04 · Gestionar la lista de favoritos { #rf-04 }

- **Prioridad**: Must
- **Descripción**: el usuario consulta su lista de favoritos y puede quitar Pokémon de ella.
  Hay una única lista de favoritos, común a todos los juegos. A partir de ella se generan los
  equipos ([RN-02](reglas-negocio.md#rn-02)). Cada favorito es la evolución hasta la que se
  quiere llegar; sus preevoluciones van implícitas ([RN-09](reglas-negocio.md#rn-09)).
- **Criterios de aceptación**:
    - La lista se conserva entre sesiones.
    - Muestra cuántos favoritos hay.

## Juego objetivo y reglas

### RF-05 · Seleccionar el juego objetivo { #rf-05 }

- **Prioridad**: Must
- **Descripción**: el usuario elige el juego que quiere completar.
- **Criterios de aceptación**:
    - Solo se ofrecen los **juegos completos** ([CA-67](cuestiones-abiertas.md#resueltas)):
      juegos de la saga principal que permiten la crianza y tienen cargado todo lo que
      necesitan las reglas para operar:
        - Que permitan la crianza deja fuera los de la 1.ª generación (Rojo, Azul y
          Amarillo) ([forma de jugar](index.md#forma-de-jugar),
          [CA-29](cuestiones-abiertas.md#resueltas)).
        - Qué Pokémon (por forma) existen en el juego y pueden llegar a él
          ([RN-03](reglas-negocio.md#rn-03)).
        - Sus mecánicas, como el ciclo de día y noche ([RN-15](reglas-negocio.md#rn-15)).
        - Sus combates clave, cada uno con su equipo ([RN-17](reglas-negocio.md#rn-17)).
        - Sus iniciales ([RN-21](reglas-negocio.md#rn-21)).
    - Un juego que no está completo no se ofrece ni se puede revisar o generar, aunque se
      intente por su dirección. Sí se puede registrar en el *Hall of Fame*, porque forma parte
      del recorrido ([RF-12](#rf-12)).
    - Tampoco se ofrece un juego ya registrado en el *Hall of Fame*: cada juego se completa
      una sola vez ([CA-68](cuestiones-abiertas.md#resueltas)).
    - Cambiar de juego no modifica la lista de favoritos.

### RF-06 · Configurar las reglas duras { #rf-06 }

- **Prioridad**: Must
- **Descripción**: el usuario activa o desactiva las reglas duras opcionales del catálogo
  predefinido. Sus parámetros son fijos ([CA-10](cuestiones-abiertas.md#resueltas)).
- **Criterios de aceptación**:
    - Las [reglas estructurales](reglas-negocio.md#reglas-estructurales) siempre están
      activas.
    - Las reglas duras activables ([RN-07](reglas-negocio.md#rn-07),
      [RN-11](reglas-negocio.md#rn-11), [RN-12](reglas-negocio.md#rn-12),
      [RN-13](reglas-negocio.md#rn-13), [RN-14](reglas-negocio.md#rn-14),
      [RN-16](reglas-negocio.md#rn-16) y [RN-21](reglas-negocio.md#rn-21)) se pueden activar
      y desactivar. Por defecto están
      todas activas ([CA-41](cuestiones-abiertas.md#resueltas)).
    - La configuración se conserva entre sesiones.

### RF-07 · Configurar las reglas blandas y sus pesos { #rf-07 }

- **Prioridad**: Must
- **Descripción**: el usuario activa o desactiva las reglas blandas del catálogo predefinido
  ([RN-06](reglas-negocio.md#rn-06), [RN-15](reglas-negocio.md#rn-15),
  [RN-17](reglas-negocio.md#rn-17) y [RN-20](reglas-negocio.md#rn-20)) y asigna un peso a cada una
  ([RN-04](reglas-negocio.md#rn-04)).
- **Criterios de aceptación**:
    - Cada regla blanda muestra una descripción de lo que puntúa.
    - La configuración se conserva entre sesiones.
- **Nota**: los pesos son enteros de 0 a 10, con valores por defecto
  ([CA-05](cuestiones-abiertas.md#resueltas), [RN-04](reglas-negocio.md#rn-04)). Por defecto,
  todas las reglas blandas están activas ([CA-41](cuestiones-abiertas.md#resueltas)).

### RF-15 · Revisar los datos del juego objetivo { #rf-15 }

- **Prioridad**: Must
- **Descripción**: tras elegir el juego objetivo y antes de generar el equipo, la aplicación
  muestra los datos que no se han podido cargar de forma fiable y pide al usuario que los
  confirme ([RN-18](reglas-negocio.md#rn-18)).
- **Criterios de aceptación**:
    - Solo se muestran los datos inferidos o pendientes que intervienen en la generación: los
      del juego objetivo (p. ej., si tiene ciclo de día y noche, o sus combates clave) y los de
      los favoritos que no se han descartado ya con datos automáticos (p. ej., si pueden llegar
      al juego antes de completarlo). Con [RN-21](reglas-negocio.md#rn-21) activa, también los
      de los iniciales del juego ([CA-66](cuestiones-abiertas.md#resueltas)).
    - Los datos inferidos aparecen con la propuesta ya rellenada. El usuario la acepta o la
      corrige, y rellena los pendientes.
    - Las confirmaciones se guardan por juego y no se vuelven a pedir, salvo que una nueva carga
      de datos cambie el valor propuesto.
    - El usuario puede revisar y cambiar después lo que confirmó.
    - Se muestra un aviso: los datos confirmados son responsabilidad del usuario y, si son
      erróneos, el resultado puede ser inexacto.

## Generación de equipo

### RF-08 · Generar equipos { #rf-08 }

- **Prioridad**: Must
- **Descripción**: a partir de los favoritos, el juego objetivo y las reglas configuradas, la
  aplicación propone los equipos de 6 con mayor puntuación. Primero filtra los favoritos por la
  generación y por el juego, y después aplica el resto de reglas (ver el
  [proceso de generación](reglas-negocio.md#proceso-de-generacion)).
- **Criterios de aceptación**:
    - Con los mismos datos de entrada se obtienen siempre los mismos equipos, en el mismo orden.
    - Todos los equipos cumplen las reglas duras activas.
    - Solo se puede generar cuando están confirmados los datos del juego objetivo y de los
      favoritos que lo requieren ([RF-15](#rf-15)).
    - Si varios equipos empatan con la puntuación más alta, se prefieren los que tienen más
      miembros con dos tipos ([RN-19](reglas-negocio.md#rn-19)). Los que sigan empatados se
      muestran todos, agrupando los que solo se diferencian en miembros intercambiables
      ([RN-04](reglas-negocio.md#rn-04)).

### RF-09 · Explicar el equipo generado { #rf-09 }

- **Prioridad**: Should
- **Descripción**: junto al equipo se muestra su puntuación total y lo que aporta cada regla
  blanda, para que el usuario entienda por qué se ha elegido y ajuste los pesos.
- **Criterios de aceptación**:
    - La suma de las aportaciones de cada regla coincide con la puntuación total. Ambas se
      muestran como números enteros redondeados, repartidos para que sigan sumando el total
      ([CA-51](cuestiones-abiertas.md#resueltas)).
    - Se indica qué datos usados en la generación ha confirmado el usuario
      ([RN-18](reglas-negocio.md#rn-18)).

### RF-10 · Mostrar el equipo incompleto con sugerencias { #rf-10 }

- **Prioridad**: Must
- **Descripción**: si no se pueden reunir 6 favoritos que cumplan las reglas, la aplicación
  explica el motivo y muestra el equipo incompleto con el mayor número posible de favoritos.
  Para los huecos libres, sugiere Pokémon que no son favoritos y que encajan con las reglas
  activas ([RN-08](reglas-negocio.md#rn-08)).
- **Criterios de aceptación**:
    - El mensaje indica la causa y en qué filtro se ha descartado cada favorito. Por ejemplo:
      «de tus 9 favoritos, 3 no existen en la 3.ª generación, 2 no pueden llegar a Pokémon
      Rojo Fuego antes de la Pokédex Nacional y 1 se usó en Pokémon Verde Hoja».
    - Si una regla de presencia ([RN-13](reglas-negocio.md#rn-13),
      [RN-14](reglas-negocio.md#rn-14)) reserva un hueco, se indica qué regla es y sus
      sugerencias la cumplen.
    - Las sugerencias se muestran separadas del equipo y ordenadas por lo que aportarían a la
      puntuación; a igual aportación, primero las de dos tipos
      ([RN-19](reglas-negocio.md#rn-19)).
    - Las sugerencias que dependen de datos sin confirmar se marcan como «sin verificar»
      ([RN-18](reglas-negocio.md#rn-18)).
    - El usuario puede añadir una sugerencia a favoritos desde ahí, o elegirla para un hueco al
      seleccionar el equipo que registra en el *Hall of Fame* ([RF-12](#rf-12),
      [CA-53](cuestiones-abiertas.md#resueltas)).

## Datos

### RF-11 · Cargar y actualizar los datos { #rf-11 }

- **Prioridad**: Must
- **Descripción**: el administrador carga los datos de Pokémon, juegos y generaciones desde
  las fuentes externas (PokeAPI, Pokémon Showdown y WikiDex), y los vuelve a cargar para
  actualizarlos. La carga se ejecuta a mano desde la terminal, aparte de la aplicación
  ([CA-47](cuestiones-abiertas.md#resueltas)).
- **Alcance inicial**: las 386 especies de las generaciones 1 a 3 y sus 11 juegos, con los 5
  de la 3.ª generación como posibles juegos objetivo (al principio, solo Rojo Fuego y Verde
  Hoja están completos, [RF-05](#rf-05)), para validar el algoritmo antes de ampliarlo
  ([CA-11](cuestiones-abiertas.md#resueltas),
  [diseño de la carga](../02-ddt/carga-datos.md#alcance)).
- **Criterios de aceptación**:
    - Se cargan las generaciones, los juegos de cada generación y qué Pokémon (por forma)
      existen en cada juego ([RN-03](reglas-negocio.md#rn-03)).
    - Se cargan los datos que necesitan las reglas del catálogo: si cada Pokémon se puede criar,
      tipos y tabla de eficacias por generación, líneas evolutivas con el método de cada
      evolución en cada juego, movimientos que se aprenden subiendo de nivel y los combates
      clave de cada juego con sus Pokémon. El detalle está en el
      [DDT](../02-ddt/datos-requeridos.md).
    - Cada dato guarda su origen: automático, inferido o pendiente
      ([RN-18](reglas-negocio.md#rn-18)). Cuando un dato no se puede cargar con certeza, se
      propone un valor inferido si es posible (p. ej., que solo llegan los Pokémon de la
      Pokédex regional).
    - Repetir la carga no duplica datos ni borra las confirmaciones del usuario.
    - Se respetan los límites de uso de cada fuente.
    - Al terminar, se informa de qué se ha cargado y de los errores, si los hay. El informe
      dice también qué juegos no están completos y qué les falta: se cargan igualmente, pero
      no se pueden elegir como juego objetivo ([RF-05](#rf-05),
      [CA-67](cuestiones-abiertas.md#resueltas)).
    - Si la carga encuentra algo que la aplicación no sabe tratar, queda **bloqueada**: no
      cambia los datos y genera un informe para el arquitecto ([RF-16](#rf-16)). Bloquean la
      carga:
        - Un método de evolución sin catalogar ([CA-42](cuestiones-abiertas.md#resueltas)).
        - Una evolución que exige conocer un movimiento sin que estén cargados los movimientos
          que se aprenden por nivel ([CA-45](cuestiones-abiertas.md#resueltas)).
        - El equipo de un combate clave que no se encuentra en WikiDex.
    - Una carga bloqueada solo se resuelve con una nueva versión de la aplicación o de sus
      datos curados. Hasta entonces se sigue usando la base de datos anterior.

### RF-16 · Informar de las cargas bloqueadas { #rf-16 }

- **Prioridad**: Must
- **Descripción**: cuando la carga de datos queda bloqueada ([RF-11](#rf-11)), genera un
  informe para que el arquitecto revise el modelo y prepare la nueva versión que la
  desbloquea ([CA-47](cuestiones-abiertas.md#resueltas)).
- **Criterios de aceptación**:
    - La carga recoge **todos** los bloqueos antes de parar, para resolverlos de una vez.
    - De cada bloqueo, el informe dice qué es, dónde aparece (p. ej., «`spin`: Milcery →
      Alcremie en Espada y Escudo»), a qué reglas afecta, qué decisión hace falta y una
      plantilla para completarlo en los datos curados.
    - El informe incluye un resumen, la fecha y las versiones de los datos usados (commit de
      PokeAPI), para poder repetir la carga.
    - Se guarda en un formato para leer y en otro para procesar por programa.
    - La carga termina con un código de salida propio, distinto del de un error.
    - La carga nunca publica nada: los informes se registran en git después, a mano, según
      el protocolo de Operación.

## Hall of Fame

### RF-12 · Registrar un equipo en el Hall of Fame { #rf-12 }

- **Prioridad**: Must
- **Descripción**: el usuario registra el equipo con el que ha completado un juego. Los
  registros, en orden, forman el **recorrido** del usuario, que usa
  [RN-16](reglas-negocio.md#rn-16) para excluir Pokémon ya usados.
- **Criterios de aceptación**:
    - El registro incluye el juego, la fecha, notas opcionales y los Pokémon del equipo (hasta
      6). De cada Pokémon se guardan la forma concreta, el nombre y el tipo o tipos que tenía
      en ese juego ([RN-05](reglas-negocio.md#rn-05), [RN-10](reglas-negocio.md#rn-10)).
    - Queda claro qué registro es el último juego completado: se ordenan por fecha y, si dos
      coinciden, por orden de registro.
    - Se puede crear a partir de un equipo generado: en el resultado, un selector permite elegir
      uno de los equipos (una alternativa por posición y una sugerencia por hueco) y registrarlo
      para ese juego, o descartarlos sin registrar nada. Antes de registrarlo se comprueba que
      cumple las reglas activas ([CA-53](cuestiones-abiertas.md#resueltas)).
    - Cada juego se registra **una sola vez**: los juegos ya registrados no aparecen al
      registrar. Para volver a jugar uno hay que eliminar antes su registro
      ([CA-68](cuestiones-abiertas.md#resueltas)).

### RF-13 · Consultar el Hall of Fame { #rf-13 }

- **Prioridad**: Must
- **Descripción**: el usuario consulta los equipos registrados en su Hall of Fame, es decir,
  su recorrido.
- **Criterios de aceptación**:
    - Se puede filtrar por juego.
    - Cada registro muestra el equipo, el juego y la fecha.
    - Se puede corregir o eliminar un registro, porque cambia las exclusiones de
      [RN-16](reglas-negocio.md#rn-16).
    - Eliminar un registro borra también la Pokédex de ese juego ([RF-20](#rf-20)). La
      aplicación lo avisa y pide confirmación antes
      ([CA-68](cuestiones-abiertas.md#resueltas)).

## Reglas personalizadas

### RF-14 · Cargar reglas definidas por el usuario { #rf-14 }

- **Prioridad**: Could
- **Descripción**: el usuario proporciona a la aplicación su propio conjunto de reglas, además
  de las del catálogo predefinido.
- **Nota**: en la primera versión, las reglas son las del catálogo predefinido del DDF. Que el
  usuario defina reglas nuevas exige diseñar cómo se expresan; se abordará más adelante.

## Imágenes

Mejora de la interfaz prevista en [CA-52](cuestiones-abiertas.md#resueltas): la primera versión
identifica cada Pokémon por su número, su nombre y sus tipos, y cada juego por su nombre, y deja
las imágenes para más adelante. Ayudan a reconocerlos de un vistazo, pero no cambian ninguna
regla ni ningún cálculo. Qué imágenes, de dónde salen y en qué condiciones se usan está
decidido en [CA-54, CA-55 y CA-56](cuestiones-abiertas.md#resueltas).

### RF-17 · Mostrar imágenes de los Pokémon { #rf-17 }

- **Prioridad**: Could
- **Descripción**: cada Pokémon se muestra con su imagen, además de su número, su nombre y sus
  tipos, allí donde aparece en la aplicación.
- **Criterios de aceptación**:
    - Se ve la imagen en el catálogo ([RF-01](#rf-01)), la ficha y su línea evolutiva
      ([RF-02](#rf-02)), los favoritos ([RF-04](#rf-04)), las posiciones y las sugerencias del
      resultado ([RF-08](#rf-08), [RF-10](#rf-10)) y el equipo de cada registro del *Hall of
      Fame* ([RF-13](#rf-13)).
    - Cada forma tiene su propia imagen: Vulpix y Vulpix de Alola se distinguen
      ([RN-05](reglas-negocio.md#rn-05)).
    - La imagen acompaña al nombre, nunca lo sustituye: el nombre sigue siendo el texto que
      identifica al Pokémon, también para los lectores de pantalla.
    - Si un Pokémon no tiene imagen, o no se ha podido obtener, se muestra igual, sin imagen y
      sin errores.
    - La aplicación funciona sin conexión una vez cargados los datos: las imágenes se obtienen
      en la carga ([RF-11](#rf-11)), no cada vez que se abre una pantalla.
    - La aplicación indica de quién son las imágenes y de dónde salen
      ([CA-56](cuestiones-abiertas.md#resueltas)).
- **Nota**: se empieza con los *sprites* de PokeAPI, una imagen pequeña por forma, y se valora
  cómo queda ([CA-54](cuestiones-abiertas.md#resueltas)).

### RF-18 · Mostrar la portada de los juegos { #rf-18 }

- **Prioridad**: Could
- **Descripción**: cada juego se muestra con su portada, además de su nombre.
- **Criterios de aceptación**:
    - Se ve la portada al elegir el juego objetivo ([RF-05](#rf-05)), en la cabecera de la
      revisión de datos y del resultado, en el último juego completado del Inicio y en cada
      registro del *Hall of Fame* ([RF-13](#rf-13)), también de los juegos que no pueden ser
      juego objetivo (Rojo, Oro…).
    - El nombre del juego sigue visible: la portada lo acompaña.
    - Si un juego no tiene portada, se muestra igual, solo con su nombre.
    - Como las imágenes de los Pokémon, las portadas se obtienen en la carga y la aplicación
      funciona sin conexión.
    - Como las imágenes de los Pokémon, con el aviso de su titularidad y su procedencia.
- **Nota**: las portadas salen de WikiDex ([CA-55](cuestiones-abiertas.md#resueltas)), que las
  declara de uso legítimo solo en sus artículos: la aplicación las usa en privado y se pueden
  quitar cargando los datos sin portadas
  ([ADR-0011](../03-adr/0011-portadas-wikidex-uso-privado.md)).

## Seguridad

La aplicación es personal y de un solo usuario, y no tiene autenticación: en su ordenador no
hace falta. Si se usa desde fuera de él ([puesta en producción](../05-operacion/puesta-en-produccion.md)),
cualquiera que llegue a ella podría ver y cambiar los datos. Hoy se evita con un acceso privado
([ADR-0009](../03-adr/0009-despliegue-vm-gratuita-tailscale.md), *Propuesto*); esta mejora
protege la propia aplicación, de forma que no dependa solo de cómo se despliega.

### RF-19 · Proteger el acceso a la aplicación { #rf-19 }

- **Prioridad**: Could
- **Descripción**: solo el usuario de la aplicación puede usar la API y la web. Sigue siendo una
  aplicación de un solo usuario: no hay registro ni varias cuentas.
- **Criterios de aceptación**:
    - Sin identificarse no se puede ver ni cambiar nada: la web muestra una pantalla de acceso
      y la API rechaza las peticiones (`401`), salvo una comprobación de que está en marcha que
      no revela datos.
    - Las credenciales se configuran en el servidor, nunca en el código ni en git.
    - La sesión se mantiene en el navegador durante un tiempo razonable y se puede cerrar desde
      la web.
    - Fuera del ordenador del usuario, la comunicación va siempre cifrada (HTTPS).
    - Los intentos de acceso fallidos se limitan, para dificultar que se adivinen las
      credenciales.
    - La documentación interactiva de la API y su contrato OpenAPI solo se ven identificado.
    - En desarrollo y en los tests se puede desactivar con la configuración, sin cambiar el
      código.
- **Nota**: el mecanismo y las protecciones que lo acompañan se deciden en
  [CA-57](cuestiones-abiertas.md#abiertas) y [CA-58](cuestiones-abiertas.md#abiertas).

## Pokédex

Ayuda a completar la Pokédex de los juegos superados para conseguir su diploma. Es una función
independiente de la generación de equipos: solo comparte con ella el *Hall of Fame*
([CA-79](cuestiones-abiertas.md#resueltas)). Sus reglas son
[RN-22 a RN-26](reglas-negocio.md#reglas-de-la-pokedex).

### RF-20 · Consultar el progreso de las Pokédex { #rf-20 }

- **Prioridad**: Must
- **Descripción**: el usuario ve los juegos que ha superado, es decir, los registrados en el
  *Hall of Fame*, con el progreso de la Pokédex de cada uno
  ([RN-22](reglas-negocio.md#rn-22)).
- **Criterios de aceptación**:
    - Aparece cada juego registrado en el *Hall of Fame*, una vez
      ([CA-68](cuestiones-abiertas.md#resueltas)).
    - De cada uno se muestran el porcentaje completado, su estado (**no iniciada**, **en
      curso** o **completada**) y cuántos Pokémon están marcados como imposibles.
    - Al eliminar el registro del *Hall of Fame*, su Pokédex desaparece con sus datos
      ([RF-13](#rf-13)).

### RF-21 · Marcar los Pokémon ya registrados { #rf-21 }

- **Prioridad**: Must
- **Descripción**: la primera vez que el usuario abre la Pokédex de un juego, ve la lista de
  todos los Pokémon de esa Pokédex ([RN-22](reglas-negocio.md#rn-22)) y marca los que ya
  tiene registrados.
- **Criterios de aceptación**:
    - La lista sigue el orden de la Pokédex, con el número, el nombre y los tipos de cada
      Pokémon, y su imagen si la hay ([RF-17](#rf-17)).
    - Registrado significa capturado u obtenido, no solo visto
      ([CA-69](cuestiones-abiertas.md#resueltas)).
    - Se marca y desmarca libremente hasta confirmar. Al confirmar, se guarda y se pasa a la
      ficha del Pokémon objetivo ([RF-22](#rf-22)).
    - Solo se muestra la primera vez. Las correcciones posteriores se hacen en el detalle
      ([RF-24](#rf-24), [CA-77](cuestiones-abiertas.md#resueltas)).

### RF-22 · Ficha del Pokémon objetivo { #rf-22 }

- **Prioridad**: Must
- **Descripción**: la aplicación muestra la ficha del siguiente Pokémon que hay que registrar
  ([RN-23](reglas-negocio.md#rn-23)) con su forma de obtención más sencilla
  ([RN-24](reglas-negocio.md#rn-24)).
- **Criterios de aceptación**:
    - La ficha muestra el número, el nombre, los tipos y la imagen del Pokémon, y la forma de
      obtenerlo con su detalle: dónde y con qué probabilidad, desde qué juego o cómo
      evoluciona ([RN-24](reglas-negocio.md#rn-24) a [RN-26](reglas-negocio.md#rn-26)).
    - Si la forma es criarlo o evolucionarlo desde otro Pokémon que no está registrado, la
      ficha enlaza a la de ese Pokémon, en lugar de explicarlo en la misma
      ([CA-76](cuestiones-abiertas.md#resueltas)).
    - Acciones:
        - **Registrar**: lo marca como registrado y pasa al siguiente objetivo.
        - **Marcar como imposible de obtener**: lo marca como imposible y pasa al siguiente.
        - **Saltar de momento**: pasa al siguiente sin guardar nada. Al volver a entrar en la
          Pokédex de ese juego, vuelve a salir primero
          ([CA-77](cuestiones-abiertas.md#resueltas)).
        - **Otras formas de obtención** ([RF-23](#rf-23)).
    - Cuando no queda ningún Pokémon por registrar ni marcado como imposible, la aplicación lo
      dice en lugar de mostrar una ficha.

### RF-23 · Elegir otra forma de obtención { #rf-23 }

- **Prioridad**: Must
- **Descripción**: en la ficha, el usuario ve todas las formas de obtener el Pokémon, de la más
  sencilla a la menos ([RN-24](reglas-negocio.md#rn-24)), y elige la que prefiere.
- **Criterios de aceptación**:
    - Aparecen todas las formas posibles en el orden de RN-24, con la recomendada marcada.
    - La forma elegida se guarda para ese Pokémon en esa Pokédex. La ficha la muestra primero,
      marcada como «elegida por ti», y se puede volver a la recomendada
      ([CA-75](cuestiones-abiertas.md#resueltas)).
    - Sirve también para detectar errores: no debería haber una forma más sencilla que la
      recomendada; si la hay, es un fallo de los datos o de las reglas.

### RF-24 · Revisar los registrados y los imposibles { #rf-24 }

- **Prioridad**: Must
- **Descripción**: una pantalla de detalle de la Pokédex de un juego con dos listas: los
  Pokémon registrados y los imposibles de obtener.
- **Criterios de aceptación**:
    - Desde cualquiera de las dos listas se puede desmarcar un Pokémon, para corregir un
      registro erróneo o un imposible que sí se puede obtener
      ([CA-71](cuestiones-abiertas.md#resueltas)). Vuelve a poder ser objetivo.
    - Los imposibles automáticos ([RN-25](reglas-negocio.md#rn-25)) aparecen con su motivo y
      no se pueden desmarcar.
