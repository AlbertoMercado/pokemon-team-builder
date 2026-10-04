# 0008 · Cargas bloqueadas: informe para el arquitecto y resolución por nueva versión

- **Estado**: Aceptado
- **Fecha**: 2026-10-04
- **Decisores**: Alberto Mercado

## Contexto

La ingesta es una CLI que el administrador ejecuta a mano y que construye `reference.sqlite`
aparte de la aplicación ([ADR-0002](0002-monolito-modular-nucleo-puro.md),
[ADR-0003](0003-dos-bases-de-datos-sqlite.md)). Al actualizar el commit de PokeAPI o añadir
una generación, la carga puede encontrar cosas que la aplicación no sabe tratar:

- un disparador o una condición de evolución sin catalogar
  ([CA-42](../01-ddf/cuestiones-abiertas.md#resueltas));
- una evolución que exige un movimiento sin que estén cargados los movimientos por nivel
  ([CA-45](../01-ddf/cuestiones-abiertas.md#resueltas));
- un juego objetivo sin combates clave ([CA-46](../01-ddf/cuestiones-abiertas.md#resueltas));
- el equipo de un combate clave que no se encuentra en WikiDex.

Ninguno se puede resolver dentro de la carga: exigen decidir cómo los tratan las reglas
(RN-15, RN-17, RN-20) o completar los datos curados. Se planteó catalogarlos desde la web, pero
obligaba a que la API lanzara la ingesta, que hoy tiene prohibido (`api-not-ingest`), y a
guardar decisiones del modelo en `user.sqlite`, fuera de git.

## Decisión

- **La ingesta sigue siendo una CLI manual** que ejecuta el administrador. La API no la lanza.
- **Recoge todos los bloqueos antes de parar.** La carga sigue hasta el final, acumula los
  bloqueos y, si hay alguno, no sustituye `reference.sqlite` y termina con el **código de
  salida 2** (0 si se completa, 1 si falla por otro motivo).
- **Genera un informe en JSON y en Markdown** en `data/reports/`, fuera de git. El Markdown se
  genera a partir del JSON y está pensado para el arquitecto. De cada bloqueo dice qué es,
  dónde aparece, a qué reglas afecta, qué decisión hace falta y una plantilla para
  completarlo.
- **Se resuelve siempre con una nueva versión por PR**: el arquitecto cambia los datos
  curados o, si hace falta, el DDF, un ADR o el código, y el administrador repite la carga.
- **La CLI nunca escribe en git.** Los informes se registran después, a mano, siguiendo el
  [protocolo de informes de carga](../05-operacion/ingesta.md#carga-bloqueada).

## Alternativas consideradas

### Catalogar lo desconocido desde la web

- ✅ El usuario desbloquea la carga sin esperar a una nueva versión.
- ❌ La API tendría que lanzar la ingesta y seguir su progreso, rompiendo `api-not-ingest`.
- ❌ Decisiones del modelo en `user.sqlite`, sin historial ni revisión.

### Parar en el primer problema

- ✅ Es lo que ya hace la carga ante un error.
- ❌ Una vuelta por problema: el arquitecto arregla uno y aparece el siguiente.

### Informe solo en la terminal o en un log

- ✅ Sin nada que construir.
- ❌ Se pierde al cerrar la terminal y no se puede mandar ni comparar.

### Crear un issue de GitHub desde la CLI

- ✅ El arquitecto lo recibe sin pasos manuales.
- ❌ La CLI publicaría fuera, con credenciales y red, y mezclaría la ingesta con GitHub. Se
  puede añadir como opción en el futuro.

### Fichero local fuera de git para desbloquear mientras llega el PR

- ✅ No bloquea al administrador.
- ❌ Dos fuentes de verdad; es fácil que el arreglo local nunca pase a git.

### Cargar parcialmente, sin lo afectado

- ✅ El resto de los datos se actualiza.
- ❌ Cada regla tendría que tratar datos «no utilizables»; contradice CA-42 y CA-46.

## Consecuencias

### Positivas

- Todo lo que cambia cómo se interpretan los datos queda en git y revisado.
- Una sola vuelta por carga bloqueada, con la lista completa y plantillas para completar.
- Se mantienen los contratos de dependencia: `api` no depende de `ingest`.
- El código de salida distingue un fallo de un «hace falta revisar el modelo».

### Negativas / riesgos

- Un caso trivial también espera a una nueva versión. Son raros: aparecen al cambiar de
  commit de PokeAPI o al añadir juegos.
- La ingesta tiene que separar los bloqueos (que se acumulan) de los errores (que cortan la
  carga), y su informe pasa a ser una interfaz con formato estable.
- Registrar los informes en git es un paso manual que se puede olvidar; lo recoge el
  protocolo.

### Acciones derivadas

- [ ] Fase 7 del [plan de carga](../02-ddt/plan-carga-datos.md#fases): bloqueos, informe en
  JSON y Markdown y código de salida 2.
- [ ] Registrar en git el informe de la primera carga que siga el protocolo.

## Referencias

- [RF-11](../01-ddf/requisitos-funcionales.md#rf-11),
  [RF-16](../01-ddf/requisitos-funcionales.md#rf-16),
  [CA-47](../01-ddf/cuestiones-abiertas.md#resueltas)
- [Ingesta de datos](../05-operacion/ingesta.md) e
  [informes de carga](../05-operacion/informes-carga/index.md)
