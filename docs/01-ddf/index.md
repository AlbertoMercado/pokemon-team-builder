# Documento de Diseño Funcional (DDF)

Describe **qué** hace la aplicación, sin entrar en **cómo** se implementa (eso corresponde al
[DDT](../02-ddt/index.md)). Es la fuente de verdad de los requisitos funcionales (**RF-XX**) y de
las reglas de negocio (**RN-XX**).

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 0.1 | 2026-10-02 | Versión inicial: alcance, requisitos RF-01 a RF-14 y reglas RN-01 a RN-10. |
| 0.2 | 2026-10-03 | Forma de jugar (crianza y transferencia). Catálogo de reglas de la primera versión (RN-11 a RN-17). El *Hall of Fame* pasa a Must por el recorrido (RN-16). RN-08 y RN-10 se amplían. |
| 0.3 | 2026-10-03 | Confirmación de los datos sin verificar por el usuario (RN-18, RF-15). Desempate por Pokémon con dos tipos (RN-19). |
| 0.4 | 2026-10-04 | Alcance de la primera carga: generaciones 1 a 3 y juegos objetivo de la 3.ª (CA-11). Evoluciones aleatorias y Shedinja como tediosas en RN-15 (CA-35). Penalización propia de las evoluciones aleatorias (RN-20, CA-37). Etapa que nace del huevo con bebés de incienso (CA-36). |
| 0.5 | 2026-10-04 | Nueva cuestión CA-38: variantes del equipo del rival según el inicial (RN-17). |
| 0.6 | 2026-10-04 | CA-38 resuelta: del rival solo cuentan los Pokémon comunes a todas las variantes. CA-39: en Kanto, Giovanni solo cuenta como líder de gimnasio (RN-17). |
| 0.7 | 2026-10-04 | CA-40: las sugerencias de RN-08 pasan los mismos filtros por candidato que los favoritos. CA-41: todas las reglas activables están activas por defecto. |
| 0.8 | 2026-10-04 | Casos de RN-15, RN-17 y RN-20 que el DDF no cubría (CA-42 a CA-46): los métodos de evolución sin catalogar detienen la carga y los cataloga el usuario (RF-16, nuevo); el sexo y el objeto equipado no son tediosos; con varios métodos cuenta el más fácil; sin movimientos por nivel o sin combates clave la carga se detiene. La carga se lanza desde la aplicación (RF-11). |
| 0.9 | 2026-10-04 | CA-47: la carga sigue siendo una tarea manual del administrador. Si queda bloqueada, genera un informe para el arquitecto, que la resuelve con una nueva versión (RF-11; RF-16 pasa a ser «Informar de las cargas bloqueadas»). |
| 0.10 | 2026-10-04 | CA-48: si RN-13 y RN-14 no caben juntas, RN-13 tiene prioridad y RN-14 reserva un hueco. CA-49: solo se agrupan los empates si todas sus combinaciones son válidas. CA-50: se dan todas las sugerencias, ordenadas (RN-04, RN-08). |
| 0.11 | 2026-10-04 | CA-51: las puntuaciones se muestran como enteros redondeados que siguen sumando el total (RF-09). |

## Propósito

Ayudar a elegir un equipo de 6 Pokémon con el que completar un juego concreto. El usuario
indica qué Pokémon le gustan y con qué criterios quiere elegir, y la aplicación propone el
equipo que mejor cumple esos criterios.

## Forma de jugar

La aplicación está pensada para una forma de jugar concreta, de la que parten las
[reglas de negocio](reglas-negocio.md):

1. Se elige el juego objetivo, se confirman los datos que no se han podido cargar de forma
   fiable ([RF-15](requisitos-funcionales.md#rf-15)) y se genera el equipo.
2. Los 6 Pokémon se **crían en otro juego**, en su etapa inicial y a nivel 1 (o al más bajo que
   permita el juego de crianza).
3. Se **transfieren** al juego objetivo y se recogen en el primer PC o en el primer momento en
   que el juego permite acceder a las cajas.
4. El juego se completa con ese equipo, que evoluciona dentro del juego objetivo.

    Por eso solo pueden ser juego objetivo los juegos que permiten la crianza: quedan fuera
    los de la 1.ª generación ([CA-29](cuestiones-abiertas.md#resueltas)).
5. El equipo se registra en el *Hall of Fame*. Los juegos completados forman el **recorrido**,
   que determina qué Pokémon no se pueden repetir en los siguientes juegos.

Consecuencias:

- No importa dónde se atrapa cada Pokémon, sino que la etapa que nace del huevo pueda llegar
  al juego objetivo y evolucionar antes de completarlo ([RN-03](reglas-negocio.md#rn-03)).
- Solo valen Pokémon que se pueden obtener por crianza ([RN-11](reglas-negocio.md#rn-11)).
- Las evoluciones se hacen en el juego objetivo, con sus métodos
  ([RN-10](reglas-negocio.md#rn-10), [RN-15](reglas-negocio.md#rn-15)).

## Alcance

**Dentro del alcance**:

- Mantener una lista de Pokémon favoritos, que son los candidatos a formar el equipo.
- Configurar el juego objetivo y las reglas de elección.
- Generar un equipo de 6 a partir de los favoritos, el juego y las reglas. Si no es posible,
  mostrar un equipo incompleto con sugerencias para completarlo.
- Consultar el catálogo de Pokémon y la ficha básica de cada uno.
- Cargar y actualizar los datos de los Pokémon desde fuentes externas.
- Registrar los equipos con los que se ha completado un juego (*Hall of Fame*).

**Fuera del alcance** (por ahora):

- Combate competitivo: equipos para formatos de Showdown, EV/IV, objetos o estrategias.
- Varios usuarios, cuentas o autenticación: la aplicación es personal y de un solo usuario.
- Juegos que no sean de la saga principal (spin-offs, Pokémon GO, TCG…).

**Fuera del alcance de este documento**:

- Cómo se implementa la búsqueda del mejor equipo y qué datos se guardan de cada Pokémon y
  juego. Se tratan en el [DDT](../02-ddt/index.md).

## Actores

| Actor | Descripción |
|-------|-------------|
| Usuario | Persona que usa la aplicación: gestiona favoritos y reglas, genera equipos y registra su *Hall of Fame*. |
| Administrador | El mismo usuario cuando carga o actualiza los datos. Se separa porque es una tarea técnica y poco frecuente. |

## Visión general

```mermaid
flowchart LR
    subgraph must ["Imprescindible (Must)"]
        DAT[Carga de datos]
        FAV[Favoritos]
        REG[Juego objetivo<br/>y reglas]
        GEN[Generación<br/>de equipo]
        HOF[Hall of Fame<br/>y recorrido]
    end
    subgraph should ["Apoyo (Should)"]
        CAT[Catálogo y ficha<br/>de Pokémon]
    end
    subgraph could ["Deseable (Could)"]
        PER[Reglas<br/>personalizadas]
    end
    DAT --> CAT
    CAT -- añadir / quitar --> FAV
    FAV --> GEN
    REG --> GEN
    PER -.-> REG
    GEN -- equipo usado --> HOF
    HOF -- Pokémon ya usados --> GEN
```

## Glosario

Especie
:   Pokémon identificado por su número de la Pokédex nacional (p. ej., Bulbasaur, #0001).

Forma
:   Variante de una especie con datos propios: formas regionales (Vulpix de Alola), megaevoluciones,
    etc. Solo las formas regionales cuentan como Pokémon distintos ([RN-05](reglas-negocio.md#rn-05)).

Forma regional
:   Variante de una especie propia de una región (Alola, Galar, Hisui, Paldea), con otro tipo y
    otras estadísticas. A todos los efectos es un Pokémon distinto
    ([RN-05](reglas-negocio.md#rn-05)).

Línea evolutiva
:   Conjunto de especies relacionadas por evolución (Bulbasaur → Ivysaur → Venusaur).

Mecanismo de evolución
:   Condición para evolucionar: subir de nivel, usar una piedra, intercambio, amistad, etc.
    Puede cambiar de un juego a otro ([RN-10](reglas-negocio.md#rn-10)).

Evolución tediosa
:   Evolución que exige algo más que subir de nivel, usar un objeto o tener amistad:
    intercambio, belleza, un lugar concreto, la hora del día, etc. Penaliza, pero no descarta
    ([RN-15](reglas-negocio.md#rn-15)).

Tipo primario
:   Primer tipo de un Pokémon con dos tipos, o su único tipo. Por ejemplo, Dragonite es
    Dragón/Volador: su tipo primario es Dragón ([RN-13](reglas-negocio.md#rn-13)).

Legendario y singular
:   Pokémon especiales según la clasificación oficial, como Mewtwo (legendario) o Mew
    (singular). Los pseudolegendarios, como Dragonite, no lo son. No se pueden criar
    ([RN-11](reglas-negocio.md#rn-11)).

Crianza
:   Obtener un Pokémon de un huevo. El equipo se cría en otro juego y se transfiere al juego
    objetivo ([forma de jugar](#forma-de-jugar)).

Generación
:   Etapa de la saga principal que agrupa varios juegos. Los Pokémon de una generación son los
    que aparecen en alguno de sus juegos (p. ej., la 1.ª generación incluye Rojo, Azul y
    Amarillo, con 151 Pokémon).

Juego objetivo
:   Juego de la saga principal que se quiere completar (p. ej., Pokémon Rojo Fuego). Pertenece a
    una generación. Ambos determinan los candidatos ([RN-03](reglas-negocio.md#rn-03)).

Completar un juego
:   Vencer al Campeón de la Liga Pokémon y entrar en el *Hall of Fame* del juego.

Favoritos
:   Lista única de Pokémon que el usuario considera elegibles para formar el equipo, común a
    todos los juegos. Cada favorito es una forma concreta y la evolución hasta la que se quiere
    llegar; las preevoluciones van implícitas ([RN-09](reglas-negocio.md#rn-09)).

Existir en un juego
:   Un Pokémon existe en un juego si se puede tener en él, aunque no se pueda atrapar allí
    (p. ej., porque se consigue por intercambio, evolución o transferencia).

Candidatos
:   Favoritos que existen en la generación y en el juego objetivo.

Candidatos válidos
:   Candidatos que además pasan el resto de filtros por candidato (legendarios, recorrido).
    Entre ellos se elige el equipo.

Combate clave
:   Combate obligatorio que marca la dificultad de un juego: líderes de gimnasio o sus
    equivalentes, Alto Mando, Campeón y jefes del equipo malvado
    ([RN-17](reglas-negocio.md#rn-17)).

Catálogo de reglas
:   Conjunto de reglas predefinidas en la aplicación. El usuario las configura, pero no crea
    reglas nuevas ([RF-14](requisitos-funcionales.md#rf-14)).

Regla dura
:   Condición obligatoria. Un candidato o equipo que no la cumple se descarta. Las de
    **presencia** obligan a incluir un Pokémon con ciertas características.

Regla blanda
:   Criterio que puntúa a un equipo. Cada regla blanda tiene un peso configurable.

Hall of Fame
:   Registro de los equipos con los que el usuario ha completado un juego.

Recorrido
:   Los juegos completados por el usuario, en el orden en que los completó, con su equipo.
    Determina qué Pokémon quedan excluidos en el siguiente juego
    ([RN-16](reglas-negocio.md#rn-16)).

Dato sin verificar
:   Dato que no se ha podido cargar de forma fiable desde las fuentes: tiene un valor inferido
    o está pendiente. El usuario lo confirma antes de generar el equipo, y desde ese momento
    es responsable de él ([RN-18](reglas-negocio.md#rn-18)).

## Contenido

- [Requisitos funcionales](requisitos-funcionales.md) (**RF-XX**).
- [Reglas de negocio](reglas-negocio.md) (**RN-XX**).
- [Cuestiones funcionales](cuestiones-abiertas.md) (**CA-XX**): decisiones abiertas, tomadas
  y aplazadas.

## Convenciones

- Los identificadores `RF-XX`, `RN-XX` y `CA-XX` son estables: no se reutilizan aunque el
  elemento se elimine. Si se elimina, se marca como *Retirado* en lugar de borrarlo.
- Prioridad de los requisitos según MoSCoW:
    - **Must**: imprescindible.
    - **Should**: importante.
    - **Could**: deseable.
    - **Won't**: descartado por ahora.
- Estado de las reglas de negocio: **Borrador**, **Vigente** o **Retirado**.
- Cada regla se cita en los tests que la verifican (`@pytest.mark.rn("RN-XX")`) y en los
  issues, PR y commits que la implementan o modifican.
