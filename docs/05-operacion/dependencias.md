# Dependencias: revisar y actualizar

Cómo saber qué dependencias están desactualizadas, cómo actualizarlas y qué hay que tener en
cuenta en cada caso. Cuándo un cambio de dependencias necesita versión, en
[versiones](versiones.md#numeracion).

## Dónde se fijan las versiones

| Qué | Rangos | Versión exacta |
|-----|--------|----------------|
| Python (aplicación y desarrollo) | `pyproject.toml` (`dependencies` y grupo `dev`) | `uv.lock` |
| Web | `web/package.json` | `web/package-lock.json` |
| Hooks de pre-commit | — | `rev` en `.pre-commit-config.yaml` |
| Acciones de la CI | — | SHA del commit en `.github/workflows/ci.yml`, con la versión en un comentario |
| Node | `engines.node` en `web/package.json` | `web/.nvmrc` (lo usan la CI y `fnm`) |
| Python (intérprete) | `requires-python` en `pyproject.toml` | el que instala `uv` |

Los rangos solo marcan el mínimo; la versión que se usa la fija el fichero de bloqueo. Una
actualización dentro del rango cambia solo el fichero de bloqueo.

## Revisar qué está desactualizado

```bash
uv tree --outdated --depth 1     # Python: las líneas con «latest» tienen versión nueva
cd web && npm outdated           # web: «Wanted» dentro del rango, «Latest» la última
```

## Criterio

- **Parches y versiones menores**: juntas en un PR `chore/actualizar-dependencias`.
- **Versiones mayores**: una por PR (`chore/<paquete>-<versión>`), después de revisar sus
  cambios incompatibles y si las demás dependencias la admiten (`npm view <paquete>
  peerDependencies`). Si no se puede todavía, se anota por qué en el PR o en una issue.
- **CHANGELOG y versión**: las dependencias de la aplicación (`dependencies` de
  `pyproject.toml` y de `web/package.json`) cambian lo que usa el usuario, así que llevan una
  línea en **Sin publicar** y, como mínimo, una versión de parche. Las de desarrollo (grupo
  `dev`, `devDependencies`, hooks y acciones de la CI) no.

## Actualizar

### Python

```bash
uv lock --upgrade-package ruff --upgrade-package mypy   # solo esos paquetes
uv lock --upgrade                                       # todos, dentro de los rangos
uv sync
```

Para una versión mayor fuera del rango, se sube el mínimo en `pyproject.toml` (`uv add
'paquete>=X'` o `uv add --dev 'paquete>=X'`).

### Web

```bash
cd web
npm update vite typescript-eslint     # dentro del rango; sin nombres, todas
npm install -D paquete@^X             # versión mayor (sin -D si es de la aplicación)
```

### Hooks de pre-commit y acciones de la CI

- **ruff**: el `rev` de `ruff-pre-commit` debe coincidir con la versión de ruff de `uv.lock`,
  para que el hook y `uv run ruff` den el mismo resultado. Se cambian juntos.
- **Resto de hooks**: `uv run pre-commit autoupdate --repo <url>`, revisando el cambio.
- **Acciones de la CI**: se fijan por SHA. Al actualizar una, se cambian a la vez el SHA y el
  comentario con su versión.

## Casos especiales

- **`@types/node`**: su versión mayor debe coincidir con la de Node de `web/.nvmrc`. Con tipos de
  una versión más nueva, el código podría usar funciones que el Node instalado no tiene y fallar
  al ejecutarse. Se actualiza junto con Node, cuando la nueva versión de Node es LTS, y en el
  mismo PR se cambian `web/.nvmrc`, `engines.node` y las guías que citan la versión de Node.
- **TypeScript y `openapi-typescript`**: `openapi-typescript` declara que necesita TypeScript
  `^5.x`; el bloque `overrides` de `web/package.json` le hace usar la versión del proyecto
  ([detalle](web.md#cliente-de-la-api)). Se quita cuando admita la versión del proyecto.
- **TypeScript 7**: todavía no es posible, porque ni `typescript-eslint` ni
  `openapi-typescript` funcionan sin la API de JavaScript del compilador, que TypeScript 7.0 no
  ofrece. Se retoma con TypeScript 7.1 y un `typescript-eslint` que lo admita.

## Comprobar

Antes del PR, todas las comprobaciones de la CI en local:

```bash
uv run pre-commit run --all-files && uv run pytest && uv run mkdocs build --strict
cd web && npm ci && npm run lint && npm run format:check && npm run typecheck \
  && npm run test && npm run api:generate && git status --short && npm run test:e2e
```

`npm ci` sobre una instalación limpia descubre conflictos de dependencias que `npm install` solo
avisa. Tras `npm run api:generate`, `git status` no debe mostrar cambios en
`web/src/api/schema.d.ts`: un generador nuevo puede cambiar el cliente sin que cambie la API.
Una versión menor de `mypy` puede añadir comprobaciones nuevas; si aparecen errores, se
corrigen en el mismo PR.
