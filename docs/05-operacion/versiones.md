# Versiones

Cómo se numeran las versiones de la aplicación y cómo se publica una nueva. Los cambios de cada
versión están en el [`CHANGELOG.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/CHANGELOG.md)
y en las [*releases* de GitHub](https://github.com/AlbertoMercado/pokemon-team-builder/releases).

## Numeración

El proyecto sigue [SemVer](https://semver.org/lang/es/) (`MAYOR.MENOR.PARCHE`) desde la
**1.0.0**, la primera versión estable, que ya se usa con datos reales en `user.sqlite`.

| Sube | Cuándo | Ejemplos |
|------|--------|----------|
| **MAYOR** | Un cambio incompatible para quien usa la aplicación. | Quitar o cambiar un endpoint o un campo de la API; un cambio de `user.sqlite` que no se puede migrar sin perder datos; quitar una opción de la CLI de ingesta. |
| **MENOR** | Funcionalidad nueva compatible. | Un endpoint, una pantalla o una regla RN-XX nuevos; un juego objetivo nuevo; una migración de Alembic que conserva los datos. |
| **PARCHE** | Correcciones compatibles. | Un error del motor, de la web o de la ingesta; textos; dependencias. |

Los cambios que solo tocan la documentación o la CI no necesitan versión.

La versión vive en `pyproject.toml` (la lee la API y la devuelve en `GET /api/meta` y en el
OpenAPI) y se repite en `web/package.json`. `uv.lock` y `web/package-lock.json` se actualizan
con ella.

## Publicar una versión

1. Crea una rama `chore/release-X.Y.Z` desde `main`.
2. Sube la versión:

    ```bash
    # pyproject.toml: version = "X.Y.Z"
    uv lock
    cd web && npm version X.Y.Z --no-git-tag-version
    ```

3. En `CHANGELOG.md`, pasa lo de **Sin publicar** a una sección `[X.Y.Z] - AAAA-MM-DD` y
   actualiza los enlaces del final.
4. Si cambia el ejemplo de `GET /api/meta` del [manual de la API](../04-manual-usuario/api.md),
   actualízalo.
5. Abre el PR (`chore: publicar la versión X.Y.Z`) y fusiónalo cuando pase la CI.
6. Etiqueta el commit de `main` y crea la *release* con las notas del `CHANGELOG.md`:

    ```bash
    git switch main && git pull
    git tag -a vX.Y.Z -m "Versión X.Y.Z"
    git push origin vX.Y.Z
    gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <notas>
    ```

## Actualizar a una versión nueva

Antes de actualizar, **haz copia de `data/user.sqlite`**: es la única base de datos que no se
puede regenerar ([arrancar la API](api.md#base-de-datos-del-usuario-usersqlite)). Después:

```bash
git switch main && git pull     # o git checkout vX.Y.Z
uv sync
cd web && npm ci && npm run build
```

Al arrancar, la API aplica las migraciones pendientes de `user.sqlite`. Si el `CHANGELOG.md`
indica que hay que repetir la carga, ejecuta antes la [ingesta](ingesta.md). En el servidor,
sigue la [puesta en producción](puesta-en-produccion.md#actualizar-la-aplicacion).
