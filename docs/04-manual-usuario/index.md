# Manual de usuario

Guía de uso de la aplicación, por cada forma de usarla. Cada interfaz (la CLI de carga, la API y
la web) se documenta aquí en el mismo PR que la introduce o la cambia
([documentación del código](../02-ddt/estructura-codigo.md#documentacion-del-codigo)).

| Interfaz | Quién la usa | Guía | Estado |
|----------|--------------|------|--------|
| CLI de carga de datos | Administrador | [Cargar y actualizar los datos](cargar-datos.md) | Disponible |
| API | Integraciones y la propia web | [Usar la API](api.md) | Disponible |
| Web | Usuario | [Usar la web](web.md) | Parcial: Inicio, catálogo, ficha y favoritos |

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

!!! note "Pendiente"
    La guía de la web se completa a medida que se añaden sus pantallas
    ([plan de la web](../02-ddt/plan-web.md#fases)).
