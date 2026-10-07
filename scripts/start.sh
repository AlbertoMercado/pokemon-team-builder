#!/usr/bin/env bash
# Prepare and start the application on this computer, in one command: a backup of user.sqlite,
# the Python dependencies, the data load, the compiled web and, last, the API serving it.
# It is what updating to a new version asks for (docs/05-operacion/versiones.md).
#
# Usage, from anywhere: scripts/start.sh [ingest options, such as --offline or --no-covers]
# PTB_DATA_DIR, PTB_HOST and PTB_PORT change the data directory, the address and the port.
# Any step that fails stops the script; a failed load keeps the previous data.
set -euo pipefail

cd "$(dirname "$0")/.."

DATA_DIR="${PTB_DATA_DIR:-data}"
HOST="${PTB_HOST:-127.0.0.1}"
PORT="${PTB_PORT:-8000}"
current_step=""

step() {
    current_step="$1"
    printf '\n==> %s\n' "$1"
}

trap 'printf "\nERROR en el paso «%s». No se ha arrancado la aplicación.\n" "$current_step" >&2' ERR

if [[ -f "$DATA_DIR/user.sqlite" ]]; then
    step "Copia de seguridad de $DATA_DIR/user.sqlite"
    mkdir -p "$DATA_DIR/backups"
    backup="$DATA_DIR/backups/user-$(date +%Y%m%d-%H%M%S).sqlite"
    # sqlite3's .backup gives a consistent copy even if the file is in use.
    if command -v sqlite3 >/dev/null; then
        sqlite3 "$DATA_DIR/user.sqlite" ".backup '$backup'"
    else
        cp "$DATA_DIR/user.sqlite" "$backup"
    fi
    echo "Copia en $backup"
fi

step "Dependencias de Python (uv sync)"
uv sync

step "Carga de datos (ingesta)"
uv run python -m ingest --data-dir "$DATA_DIR" "$@"

step "Web: dependencias (npm ci) y compilación (npm run build)"
(cd web && npm ci && npm run build)

step "Arrancando la aplicación en http://$HOST:$PORT (Ctrl+C para pararla)"
trap - ERR
PTB_DATA_DIR="$DATA_DIR" exec uv run uvicorn api.main:app --host "$HOST" --port "$PORT"
