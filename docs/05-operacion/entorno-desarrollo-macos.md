# Configuración del entorno de desarrollo en macOS

Guía para preparar un Mac y descargar el proyecto **pokemon-team-builder** para trabajar en él.

Tiempo estimado: 20-30 minutos. Todas las herramientas son gratuitas, salvo Claude Code, que requiere una suscripción de Claude (Pro o superior).

Cada paso termina con un comando de **comprobación**. Si la comprobación falla, no sigas al paso siguiente.

---

## Requisitos previos

- macOS actualizado, con permisos de administrador.
- Una cuenta de GitHub con acceso al repositorio.
- Una cuenta de Claude con suscripción Pro o superior (para Claude Code).
- Terminal: la app Terminal de macOS (shell `zsh`, la predeterminada).

---

## Paso 1. Homebrew (gestor de paquetes)

Si ya está instalado, `brew --version` mostrará la versión y puedes saltar este paso.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Al terminar, el instalador muestra dos líneas para añadir `brew` al PATH. Cópialas y ejecútalas.

**Comprobación:** `brew --version`

---

## Paso 2. Git

macOS incluye Git con las Command Line Tools. Si no lo tienes, instálalo con Homebrew:

```bash
brew install git
```

Configura tu identidad y las opciones del proyecto:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "email-de-tu-cuenta@github.com"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global fetch.prune true
```

`fetch.prune` hace que `git fetch` y `git pull` eliminen las referencias a ramas remotas que ya no existen (GitHub borra la rama al fusionar cada PR).

**Comprobación:** `git --version` y `git config --global --list`

---

## Paso 3. GitHub CLI

Se usa para clonar el repositorio y para que Claude Code gestione issues y pull requests.

```bash
brew install gh
gh auth login
```

En el asistente elige: **GitHub.com → HTTPS → Yes (autenticar Git con tus credenciales de GitHub) → Login with a web browser**.

**Comprobación:** `gh auth status`

---

## Paso 4. Python con uv

`uv` gestiona las versiones de Python, los entornos virtuales y las dependencias (sustituye a pip, venv y pyenv).

```bash
brew install uv
uv python install 3.13
```

**Comprobación:** `uv --version` y `uv python list`

---

## Paso 5. Node.js con fnm

Necesario para el frontend (`web/`). `fnm` permite cambiar de versión de Node por proyecto.

```bash
brew install fnm
echo 'eval "$(fnm env --use-on-cd --shell zsh)"' >> ~/.zshrc
source ~/.zshrc
fnm install --lts
fnm default lts-latest
```

**Comprobación:** `node --version` y `npm --version`

---

## Paso 6. VS Code y extensiones

```bash
brew install --cask visual-studio-code
```

Abre VS Code, pulsa `Cmd+Shift+P` y ejecuta **"Shell Command: Install 'code' command in PATH"**. Después instala las extensiones del proyecto:

```bash
code --install-extension ms-python.python
code --install-extension charliermarsh.ruff
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension bierner.markdown-mermaid
code --install-extension anthropic.claude-code
```

| Extensión | Para qué sirve |
|---|---|
| Python | Soporte del lenguaje, depuración, entornos |
| Ruff | Lint y formato de Python |
| ESLint / Prettier | Lint y formato del frontend |
| Markdown Mermaid | Ver los diagramas de la documentación |
| Claude Code | Ver los cambios de Claude Code como diffs en el editor |

**Comprobación:** `code --version` y `code --list-extensions`

---

## Paso 7. Claude Code

Instálalo siguiendo la documentación oficial: <https://code.claude.com/docs/en/overview>

Después inicia sesión con tu cuenta de Claude (la primera vez que ejecutes `claude` te lo pedirá) y actualízalo:

```bash
claude update
```

Si lo instalaste con Homebrew, actualízalo con `brew upgrade --cask claude-code`.

**Comprobación:** `claude --version`

---

## Paso 8. Descargar el proyecto

```bash
mkdir -p ~/Proyectos && cd ~/Proyectos
gh repo clone AlbertoMercado/pokemon-team-builder
cd pokemon-team-builder
```

**Comprobación:** `git status` debe indicar que estás en la rama `main` y sin cambios.

---

## Paso 9. Instalar las dependencias del proyecto

### Backend (Python)

```bash
uv sync
```

Crea el entorno virtual `.venv` con Python 3.13 e instala todas las dependencias, incluidas las de desarrollo, según `pyproject.toml` y `uv.lock`.

### Hooks de pre-commit

```bash
uv run pre-commit install
```

A partir de aquí, cada `git commit` ejecuta automáticamente ruff, mypy, gitleaks y las comprobaciones básicas.

### Frontend (cuando exista la carpeta `web/` con su `package.json`)

```bash
cd web
npm ci
cd ..
```

### Abrir el proyecto en VS Code

```bash
code .
```

Si VS Code pregunta qué intérprete de Python usar, elige el de `.venv` del proyecto.

**Comprobación:**

```bash
uv run ruff check .
uv run pytest
uv run pre-commit run --all-files
```

Los tres comandos deben terminar sin errores. Mientras no haya tests, `pytest` termina con «no tests ran» (código de salida 5); es el comportamiento esperado.

---

## Paso 10. Empezar a trabajar

### Flujo de trabajo (GitHub Flow)

1. Actualiza `main`: `git switch main && git pull`
2. Crea una rama: `git switch -c feat/descripcion-corta` (prefijos: `feat/`, `fix/`, `docs/`, `chore/`, `test/`)
3. Trabaja y haz commits con **Conventional Commits** (`feat: ...`, `fix: ...`, `docs: ...`)
4. Sube la rama y abre un pull request: `git push -u origin HEAD && gh pr create`
5. Cuando la CI esté en verde y el PR esté revisado, haz merge a `main`.

La rama `main` está protegida: no se puede hacer push directo y todo cambio entra mediante pull request.

### Trabajar con Claude Code

Desde la raíz del proyecto:

```bash
claude
```

Claude Code lee automáticamente `CLAUDE.md`, que contiene el stack, la estructura y las convenciones del proyecto. Forma habitual de trabajo:

- Una tarea o issue por sesión, por ejemplo: *"Resuelve el issue #12"*.
- Pídele el plan antes de que haga cambios en tareas grandes.
- Revisa siempre el PR antes de hacer merge, especialmente en el motor de equipos (`core/`).

---

## Resumen rápido (para quien ya tiene las herramientas)

```bash
gh repo clone AlbertoMercado/pokemon-team-builder
cd pokemon-team-builder
uv sync
uv run pre-commit install
(cd web && npm ci)      # solo cuando exista web/package.json
code .
claude
```

---

## Solución de problemas

| Problema | Solución |
|---|---|
| `command not found: brew` después de instalarlo | Ejecuta las dos líneas que mostró el instalador para añadirlo al PATH y abre una terminal nueva. |
| `command not found: node` | Comprueba que la línea de `fnm` está en `~/.zshrc` y abre una terminal nueva. |
| `gh` pide credenciales al hacer push | Vuelve a ejecutar `gh auth login` y elige autenticar Git con tus credenciales. |
| `uv sync` usa otra versión de Python | Ejecuta `uv python install 3.13` y repite `uv sync`. |
| El commit falla por los hooks | Lee el mensaje: normalmente ruff ya ha corregido el formato. Añade los cambios con `git add` y repite el commit. |
| VS Code no detecta el entorno | `Cmd+Shift+P` → "Python: Select Interpreter" → elige `.venv`. |

---

## Herramientas pendientes para fases posteriores

- **Docker Desktop** (gratuito para uso personal): se añadirá a esta guía en la fase de despliegue.
