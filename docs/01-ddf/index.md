# Documento de Diseño Funcional (DDF)

Describe **qué** hace la aplicación, sin entrar en **cómo** se implementa (eso corresponde al
[DDT](../02-ddt/index.md)). Es la fuente de verdad de los requisitos funcionales (**RF-XX**) y de
las reglas de negocio (**RN-XX**).

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 0.1 | 2026-10-02 | Versión inicial: alcance, requisitos RF-01 a RF-14 y reglas RN-01 a RN-10. |

## Propósito

Ayudar a elegir un equipo de 6 Pokémon con el que completar un juego concreto. El usuario
indica qué Pokémon le gustan y con qué criterios quiere elegir, y la aplicación propone el
equipo que mejor cumple esos criterios.

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

- El diseño detallado de las reglas de elección: qué reglas forman el catálogo, cómo puntúa
  cada una y la escala de pesos. El DDF fija el marco común a todas las reglas; las reglas
  concretas se definen más adelante y se incorporan aquí como `RN-XX`
  ([cuestiones aplazadas](cuestiones-abiertas.md#aplazadas)).

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
    end
    subgraph should ["Apoyo (Should)"]
        CAT[Catálogo y ficha<br/>de Pokémon]
    end
    subgraph could ["Deseable (Could)"]
        HOF[Hall of Fame]
        PER[Reglas<br/>personalizadas]
    end
    DAT --> CAT
    CAT -- añadir / quitar --> FAV
    FAV --> GEN
    REG --> GEN
    PER -.-> REG
    GEN -- equipo usado --> HOF
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

Generación
:   Etapa de la saga principal que agrupa varios juegos. Los Pokémon de una generación son los
    que aparecen en alguno de sus juegos (p. ej., la 1.ª generación incluye Rojo, Azul y
    Amarillo, con 151 Pokémon).

Juego objetivo
:   Juego de la saga principal que se quiere completar (p. ej., Pokémon Amarillo). Pertenece a
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
:   Favoritos que existen en la generación y en el juego objetivo. Entre ellos se elige el equipo.

Catálogo de reglas
:   Conjunto de reglas predefinidas en la aplicación. El usuario las configura, pero no crea
    reglas nuevas ([RF-14](requisitos-funcionales.md#rf-14)).

Regla dura
:   Condición obligatoria. Un candidato o equipo que no la cumple se descarta.

Regla blanda
:   Criterio que puntúa a un equipo. Cada regla blanda tiene un peso configurable.

Hall of Fame
:   Registro de los equipos con los que el usuario ha completado un juego.

## Contenido

- [Requisitos funcionales](requisitos-funcionales.md) (**RF-XX**).
- [Reglas de negocio](reglas-negocio.md) (**RN-XX**).
- [Cuestiones funcionales](cuestiones-abiertas.md) (**CA-XX**): decisiones tomadas y
  aplazadas.

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
