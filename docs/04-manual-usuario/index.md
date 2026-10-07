# Manual de usuario

Guía de uso de la aplicación, por cada forma de usarla. Cada interfaz (la CLI de carga, la API y
la web) se documenta aquí en el mismo PR que la introduce o la cambia
([cómo se documenta](../02-ddt/documentacion.md)).

| Interfaz | Quién la usa | Guía |
|----------|--------------|------|
| CLI de carga de datos | Administrador | [Cargar y actualizar los datos](cargar-datos.md) |
| API | Integraciones y la propia web | [Usar la API](api.md) |
| Web | Usuario | [Usar la web](web.md) |

## Responsabilidad sobre los datos confirmados

Algunos datos de los juegos no se pueden cargar de forma fiable desde las fuentes, por ejemplo,
qué Pokémon pueden llegar a un juego antes de completarlo. Al elegir el juego objetivo, la
aplicación los muestra con una propuesta y pide que los confirmes o corrijas antes de generar
el equipo.

!!! warning "Aviso"
    Los datos que confirmas se usan tal cual. Si confirmas un dato erróneo, el equipo propuesto
    puede ser inexacto. No es un error del algoritmo, sino de los datos de entrada.

Las sugerencias para completar un equipo incompleto pueden depender de datos que no has
confirmado. En ese caso aparecen marcadas como «sin verificar».

## Imágenes y portadas: de quién son y cómo se usan

Las imágenes de los Pokémon y las portadas de los juegos son de Nintendo, Creatures, GAME FREAK y
The Pokémon Company ([CA-56](../01-ddf/cuestiones-abiertas.md#resueltas)). La
[carga de datos](cargar-datos.md) las descarga a tu ordenador y la aplicación las sirve desde
ahí, sin volver a pedirlas fuera ni redistribuirlas.

!!! warning "Portadas: solo para tu uso privado"
    Las portadas salen de WikiDex, que las declara de uso legítimo solo en sus artículos
    ([ADR-0011](../03-adr/0011-portadas-wikidex-uso-privado.md)). No publiques ni compartas la
    aplicación con ellas. Si no las quieres, carga los datos con `--no-covers`: la aplicación
    muestra solo los nombres de los juegos.
