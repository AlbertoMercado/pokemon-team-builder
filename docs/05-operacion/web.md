# Web: desarrollo y comprobaciones

Cómo se arranca la web en desarrollo, cómo se regenera su cliente de la API y qué comprueba
la CI. Qué pantallas tiene y cómo se construye, en el [plan de la web](../02-ddt/plan-web.md);
cómo se usa, en el [manual de usuario](../04-manual-usuario/web.md).

!!! note "Estado"
    Fases 1, 2, 4 y 5 del [plan de la web](../02-ddt/plan-web.md#fases): proyecto, cliente
    de la API, navegación, Inicio, catálogo, ficha, favoritos, nuevo juego, revisión de datos y
    resultado. Hasta la fase 8, la web se sirve con el servidor de desarrollo de
    Vite, aparte de la API.

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

### CI

El job **Web** de `.github/workflows/ci.yml` ejecuta `npm ci`, regenera el cliente y falla si
`schema.d.ts` cambia, y después el lint, el formato, los tipos, los tests y la compilación.
Es una comprobación obligatoria para fusionar en `main`, como Python, Documentación y Secretos
(protección de la rama en GitHub).

## Problemas habituales

| Síntoma | Causa y solución |
|---------|------------------|
| Aviso «La API no responde» | La API no está arrancada o no está en el puerto 8000. |
| Aviso «No hay datos cargados» | No existe `reference.sqlite`: [carga los datos](ingesta.md) y reinicia la API. |
| `npm run typecheck` falla en `src/api/` tras cambiar la API | Falta regenerar el cliente con `npm run api:generate`. |
| El job Web falla en «Cliente de la API al día» | `schema.d.ts` no está al día: regenéralo y súbelo. |
