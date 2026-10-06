---
name: publicar-version
description: Publica una versión nueva de pokemon-team-builder (SemVer, CHANGELOG, etiqueta vX.Y.Z y release de GitHub). Úsala cuando el usuario pida publicar, sacar, lanzar o preparar una versión o release, o cuando diga que ya ha ejecutado los comandos de publicación y haya que comprobarla.
---

# Publicar una versión

Protocolo de publicación documentado en `docs/05-operacion/versiones.md`. Tiene tres fases:

1. **Preparar** (Claude): todo lo que se puede hacer sin fusionar en `main` ni publicar.
2. **Publicar** (usuario): Claude le da los comandos exactos para fusionar, etiquetar y crear
   la *release*, porque son acciones visibles fuera del repositorio local.
3. **Comprobar** (Claude): cuando el usuario dice que los ha ejecutado, Claude verifica que
   todo ha quedado bien.

Si el usuario dice que ya ha ejecutado los comandos, salta directamente a la fase 3.

## Fase 1 · Preparar

1. **Punto de partida**
   - `git switch main && git pull` y `git fetch --tags --prune`. El árbol tiene que estar
     limpio; si no lo está, para y pregunta.
   - Última versión: `git describe --tags --abbrev=0` (y la de `pyproject.toml`).
   - Cambios desde entonces: `git log --oneline --first-parent <última>..main` y la sección
     **Sin publicar** de `CHANGELOG.md`.
   - Si no hay cambios desde la última etiqueta, dilo y para.

2. **Número de versión**
   - Si el usuario lo ha dicho, úsalo.
   - Si no, dedúcelo con la tabla de numeración de `docs/05-operacion/versiones.md`
     (MAYOR: incompatible en API, `user.sqlite` sin migración que conserve los datos o CLI;
     MENOR: `feat`; PARCHE: solo `fix`, textos o dependencias) y **confírmalo con el usuario
     antes de seguir**, explicando por qué.

3. **Rama y cambios** (`chore/release-X.Y.Z`)
   - `pyproject.toml`: `version = "X.Y.Z"`; después `uv lock`.
   - `cd web && npm version X.Y.Z --no-git-tag-version` (actualiza también `package-lock.json`).
   - `CHANGELOG.md`: pasa el contenido de **Sin publicar** a `## [X.Y.Z] - AAAA-MM-DD` (fecha
     de hoy) y deja **Sin publicar** vacía. Completa lo que falte con los PR fusionados desde
     la última etiqueta, agrupado en *Añadido*, *Cambiado*, *Corregido*, *Eliminado* y
     *Pendiente*, citando `#PR`, `RF-XX` y `RN-XX`. Actualiza los enlaces del final
     (`[Sin publicar]` compara desde `vX.Y.Z`; añade `[X.Y.Z]`).
   - `docs/04-manual-usuario/api.md`: el ejemplo de `GET /api/meta` con la versión nueva.
   - Busca otras apariciones de la versión anterior:
     `grep -rn "<anterior>" --exclude-dir={node_modules,.venv,.git,site,data} .`
   - Si es una versión MAYOR, explica en el CHANGELOG qué se rompe y cómo actualizar.

4. **Comprobaciones locales**: `uv run pytest`, `uv run mypy`, `uv run lint-imports`,
   `uv run mkdocs build --strict` y `uv run pre-commit run --all-files`. Si cambia algo de la
   web, también `cd web && npm run typecheck && npm run test`. Si algo falla, arréglalo antes
   de seguir o para y explícalo.

5. **Commit y PR**
   - Commit `chore: publicar la versión X.Y.Z` (Conventional Commits, en español).
   - `git push -u origin chore/release-X.Y.Z` y `gh pr create` con el título del commit; en la
     descripción, qué incluye y qué falta después de fusionar.
   - Espera a la CI: `gh pr checks <n> --watch`. Los cinco jobs tienen que pasar.

6. **Notas de la *release***: extrae la sección de la versión a un fichero del *scratchpad*
   o comprueba que el `awk` del comando del paso siguiente la extrae bien.

## Fase 2 · Publicar (comandos para el usuario)

No ejecutes tú `gh pr merge`, `git tag`, `git push` de etiquetas ni `gh release create`. Al
terminar la fase 1, resume lo hecho (PR, CI y comprobaciones) y da estos comandos con el número
de PR y la versión ya sustituidos, con el prefijo `!` para que los ejecute en la sesión:

```
! gh pr merge <n> --merge --delete-branch && git switch main && git pull && git tag -a vX.Y.Z -m "Versión X.Y.Z" && git push origin vX.Y.Z
```

```
! awk '/^## \[X.Y.Z\]/{f=1;next} /^## \[|^\[Sin publicar\]:/{f=0} f' CHANGELOG.md > /tmp/notas-X.Y.Z.md && gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/notas-X.Y.Z.md --latest
```

Termina pidiéndole que te avise cuando los haya ejecutado, para comprobarlos.

## Fase 3 · Comprobar

```bash
git fetch --tags --prune
git status -sb                                   # main igual que origin/main
gh pr view <n> --json state,mergeCommit          # MERGED
git cat-file -t vX.Y.Z                           # tag (anotada)
git rev-parse vX.Y.Z^{commit} origin/main        # el mismo commit
git ls-remote --tags origin vX.Y.Z               # está en el remoto
git show vX.Y.Z:pyproject.toml | grep '^version' # X.Y.Z
gh release view vX.Y.Z --json tagName,isDraft,isPrerelease,url,body
gh release list --limit 3                        # vX.Y.Z es Latest
git branch -a | grep release                     # la rama ya no existe
gh run list --branch main --limit 1              # CI del merge; espera con gh run watch
```

Comprueba que las notas de la *release* son la sección `X.Y.Z` del CHANGELOG (ni vacías ni con
la de otra versión) y que la CI de `main` termina en verde.

Informa con una tabla (comprobación → resultado). Si algo está mal, explica cómo corregirlo y,
si hace falta un comando de publicación, dáselo al usuario como en la fase 2. Recuérdale
comprobar `GET /api/meta` en su API y que lo nuevo se anota en **Sin publicar**.
