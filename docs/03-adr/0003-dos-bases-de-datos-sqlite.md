# 0003 · Dos bases de datos SQLite: referencia y usuario

- **Estado**: Aceptado
- **Fecha**: 2026-10-03
- **Decisores**: Alberto Mercado

## Contexto

Hay dos tipos de datos con ciclos de vida muy distintos:

- **Datos de referencia** (Pokémon, juegos, tipos, evoluciones, combates clave). Los genera la
  ingesta y se vuelven a cargar enteros cuando se actualizan las fuentes.
- **Datos del usuario** (favoritos, configuración de reglas, *Hall of Fame* y confirmaciones
  de [RN-18](../01-ddf/reglas-negocio.md#rn-18)). Hay que conservarlos siempre.

[RF-11](../01-ddf/requisitos-funcionales.md#rf-11) exige que repetir la carga no duplique datos
ni borre las confirmaciones del usuario.

## Decisión

Usamos **dos ficheros SQLite**:

- `reference.sqlite`: lo escribe solo la ingesta. Cada carga lo **reconstruye entero** en un
  fichero temporal, lo comprueba y sustituye al anterior de una vez. Su esquema no necesita
  migraciones.
- `user.sqlite`: lo escribe solo la API. Su esquema evoluciona con migraciones de **Alembic**.

Se enlazan con **claves naturales estables** (los identificadores de PokeAPI, como
`vulpix-alola` o `firered`). Como no puede haber claves foráneas entre ficheros, la ingesta
comprueba antes de sustituir `reference.sqlite` que todas las claves que usa `user.sqlite`
siguen existiendo.

## Alternativas consideradas

### Una sola base de datos con dos grupos de tablas

- ✅ Claves foráneas reales y una sola conexión.
- ❌ Repetir la ingesta exige borrar y volver a cargar tablas con cuidado sin tocar las del
  usuario, y migrar el esquema de referencia en cada cambio.

### Actualización incremental de los datos de referencia

- ✅ No hay que reconstruir todo.
- ❌ Lógica de comparación y borrado más compleja y propensa a dejar datos huérfanos. Los datos
  son pequeños (unos pocos MB) y reconstruirlos es rápido.

## Consecuencias

### Positivas

- La ingesta se puede repetir sin efectos secundarios: o se sustituye el fichero entero o se
  conserva el anterior.
- Los datos del usuario se pueden copiar, restaurar o versionar por separado.
- Solo hay que migrar el esquema de `user.sqlite`.

### Negativas / riesgos

- Sin claves foráneas entre ficheros, la integridad se comprueba en la ingesta.
- Si PokeAPI renombra un identificador, hay que corregir `user.sqlite` con una migración de
  datos. La ingesta lo detecta y no sustituye la base de datos.

### Acciones derivadas

- [ ] Configurar Alembic para `user.sqlite`.
- [ ] Ignorar `*.sqlite` y `data/cache/` en `.gitignore`.

## Referencias

- [Modelo de datos](../02-ddt/modelo-datos.md)
