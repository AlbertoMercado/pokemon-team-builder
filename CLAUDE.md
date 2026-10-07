# CLAUDE.md

Índice para trabajar en este repositorio con Claude Code. Cada regla está en una línea y enlaza
a su fuente: lee solo la sección que necesites.

**pokemon-team-builder**: aplicación personal y sin ánimo de lucro que, a partir de una lista de
Pokémon favoritos y un juego objetivo, genera un equipo de 6 con reglas duras (filtros) y blandas
(puntuación ponderada). Detalle: [DDF](docs/01-ddf/index.md).

## Reglas imprescindibles

- **Idioma**: documentación, commits, issues y PR en español; código, identificadores, ficheros
  de código y comentarios técnicos en inglés.
- **Flujo**: GitHub Flow. `main` está protegida; todo entra por PR desde una rama `feat/`, `fix/`,
  `docs/`, `chore/` o `test/`, con [Conventional Commits](https://www.conventionalcommits.org/es/)
  en español. Los cinco jobs de la [CI](docs/05-operacion/comandos.md#ci) deben pasar.
- **Reglas de negocio**: el [DDF](docs/01-ddf/index.md#convenciones) es la fuente de verdad. No
  implementes una regla (`RN-XX`), requisito (`RF-XX`) o decisión (`CA-XX`) sin documentarla
  antes; los números no se reutilizan. Cada test de una regla lleva
  `@pytest.mark.rn("RN-XX")` y la cita en su nombre o *docstring*; issues, PR y commits citan su
  identificador.
- **Arquitectura**: `core/` es puro (solo biblioteca estándar, sin red ni BD). Dependencias
  permitidas: `api → core, db` e `ingest → db`
  ([arquitectura](docs/02-ddt/arquitectura.md#reglas-de-dependencia)). Una decisión relevante,
  un [ADR](docs/03-adr/index.md) desde la plantilla.
- **Tipado**: mypy estricto; nada de `Any` ni `# type: ignore` sin justificar.
- **Datos externos**: los tests nunca usan la red (`tests/conftest.py`); usan extractos reales en
  `tests/<paquete>/fixtures/`. WikiDex, siempre con caché local, límite de peticiones y
  `User-Agent` descriptivo ([ingesta](docs/05-operacion/ingesta.md#wikidex)).
- **Documentación**: en el mismo PR y en la fuente única de su tema, enlazando desde el resto en
  lugar de copiar ([cómo se documenta](docs/02-ddt/documentacion.md#en-cada-pr)). Los cambios
  para el usuario, una línea en **Sin publicar** del `CHANGELOG.md`.
- **Versiones**: SemVer. Para publicar, la skill `publicar-version`: Claude prepara hasta el PR
  en verde y **no** fusiona, etiqueta ni crea la *release*
  ([versiones](docs/05-operacion/versiones.md#publicar-una-version)).

## Dónde está cada cosa

Comandos de desarrollo: [Comandos y CI](docs/05-operacion/comandos.md). Lo pendiente: las
[issues](https://github.com/AlbertoMercado/pokemon-team-builder/issues). Mapa de fuentes (los
enlaces son relativos a `docs/02-ddt/`):

@docs/02-ddt/documentacion.md
