# Web: desarrollo y comprobaciones

Cómo se arranca la web en desarrollo, cómo se regenera su cliente de la API y qué comprueba
la CI. Qué pantallas tiene y cómo se construye, en el [plan de la web](../02-ddt/plan-web.md);
cómo se usa, en el [manual de usuario](../04-manual-usuario/web.md).

!!! note "Estado"
    Las 8 fases del [plan de la web](../02-ddt/plan-web.md#fases): todas las pantallas, la
    API sirve la web compilada en un solo proceso y hay pruebas de extremo a extremo.

## Requisitos

- **Node 24 LTS** y npm, fijados en `web/.nvmrc`. Con `fnm` y `--use-on-cd`
  ([entorno de desarrollo](entorno-desarrollo-macos.md#paso-5-nodejs-con-fnm)), se elige solo
  al entrar en `web/`.
- **uv** y las dependencias de Python (`uv sync`): la API, y también para regenerar el cliente.

## Instalar

```bash
cd web
npm ci
```

## Arrancar en desarrollo

Hacen falta dos procesos, cada uno en su terminal:

```bash
uv run uvicorn api.main:app --reload   # en la raíz: la API en el puerto 8000
cd web && npm run dev                  # la web en http://localhost:5173
```

El servidor de Vite reenvía `/api` a `http://127.0.0.1:8000` (`web/vite.config.ts`), así que
la web y la API comparten el origen y no hace falta CORS. Al cambiar el código, la página se
actualiza sola.

## Un solo proceso

Para usar la aplicación sin desarrollar, la API sirve también la web compilada:

```bash
cd web && npm ci && npm run build && cd ..   # una vez, y cada vez que cambie la web
uv run uvicorn api.main:app                  # la aplicación en http://127.0.0.1:8000
```

- `npm run build` escribe la web en `web/dist` (fuera de git). La API la sirve en `/`
  (`api/web.py`) después de sus rutas: los ficheros de la compilación tal cual y, para el
  resto de rutas, `index.html`, así que una pantalla como `/juego/firered/resultado` se puede
  recargar o enlazar. Las rutas de `/api` nunca reciben la web: una desconocida responde `404`
  en JSON.
- `PTB_WEB_DIR` cambia el directorio de la compilación. Si no tiene `index.html`, la API
  arranca igual y solo sirve `/api`.
- Al actualizar el código, vuelve a compilar la web y reinicia la API.

## Cliente de la API

`web/src/api/schema.d.ts` contiene los tipos de todas las rutas y esquemas de la API. Se
genera, no se escribe ([ADR-0007](../03-adr/0007-cliente-generado-openapi.md)), y está en git.
**Al cambiar la API** (rutas, esquemas o descripciones), hay que regenerarlo en el mismo PR:

```bash
cd web && npm run api:generate
```

1. `uv run python -m api.openapi FICHERO` (`api/openapi.py`) escribe el OpenAPI de
   `create_app()` sin arrancar la API ni abrir las bases de datos.
2. `openapi-typescript` lo convierte en `schema.d.ts`.

Si un cambio de la API rompe la web, `npm run typecheck` lo señala.

## Comprobaciones

| Tarea | Comando (en `web/`) |
|-------|---------------------|
| Lint (ESLint con las reglas estrictas con tipos de typescript-eslint) | `npm run lint` |
| Formatear / comprobar el formato (Prettier) | `npm run format` / `npm run format:check` |
| Tipos | `npm run typecheck` |
| Tests unitarios y de pantallas (Vitest, Testing Library, MSW) | `npm run test` (`npm run test:watch` mientras se trabaja) |
| Compilar en `web/dist` | `npm run build` |

Los tests de pantallas no usan la API real: `src/test/server.ts` la simula con MSW y falla si
una pantalla hace una petición sin respuesta simulada.

### Pruebas de extremo a extremo

```bash
cd web && npx playwright install chromium   # una vez: el navegador de Playwright
npm run test:e2e                            # compila la web y ejecuta e2e/ con Playwright
```

`e2e/new-game.spec.ts` recorre el flujo de un juego nuevo contra la **API real**: favoritos →
reglas → nuevo juego en Rojo Fuego → revisión → resultado → elegir el equipo y registrarlo →
la siguiente generación excluye lo usado (RN-16). Playwright arranca la API con
`uv run python -m tests.e2e.serve` (`playwright.config.ts`), que escribe el escenario de Rojo
Fuego de los tests en un directorio temporal y sirve la web compilada en el puerto 8765. No usa
la red ni tus datos; los juegos aparecen como «Firered» porque el escenario no tiene sus
nombres en español. Si falla, el informe queda en `web/playwright-report/`.

### CI

`.github/workflows/ci.yml` tiene dos jobs para la web:

- **Web**: `npm ci`, regenera el cliente y falla si `schema.d.ts` cambia, y después el lint, el
  formato, los tipos, los tests y la compilación.
- **E2E**: instala Python, Node y Chromium y ejecuta `npm run test:e2e`. Si falla, sube el
  informe de Playwright como artefacto.

Son comprobaciones obligatorias para fusionar en `main`, como Python, Documentación y Secretos
(protección de la rama en GitHub).

## Problemas habituales

| Síntoma | Causa y solución |
|---------|------------------|
| Aviso «La API no responde» | La API no está arrancada o no está en el puerto 8000. |
| Aviso «No hay datos cargados» | No existe `reference.sqlite`: [carga los datos](ingesta.md) y reinicia la API. |
| `npm run typecheck` falla en `src/api/` tras cambiar la API | Falta regenerar el cliente con `npm run api:generate`. |
| `http://127.0.0.1:8000/` responde `{"detail":"Not Found"}` | No hay compilación de la web: `cd web && npm run build` y reinicia la API. |
| La web servida por la API no tiene los últimos cambios | Vuelve a ejecutar `npm run build` y recarga. |
| `npm run test:e2e` no encuentra el navegador | Instálalo una vez con `npx playwright install chromium`. |
| El job Web falla en «Cliente de la API al día» | `schema.d.ts` no está al día: regenéralo y súbelo. |
