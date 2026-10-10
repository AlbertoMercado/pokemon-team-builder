"""Serves the API with the compiled web over the FireRed scenario, for the end-to-end tests.

    uv run python -m tests.e2e.serve [--port 8765]

Writes the real FireRed extract of the tests (``tests/api/scenario.py``), with the Pokédex of
FireRed and LeafGreen, as reference.sqlite in a temporary data directory, with a new
user.sqlite, and runs uvicorn with ``web/dist``, as the application runs installed. It uses
neither the network nor the user's data, and the directory is removed when it stops.
Playwright starts it (``web/playwright.config.ts``).
"""

import argparse
import tempfile
from pathlib import Path

import uvicorn

from api.config import Settings
from api.main import create_app
from tests.api.scenario import write_firered

WEB_DIR = Path(__file__).resolve().parents[2] / "web" / "dist"
DEFAULT_PORT = 8765


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    if not (WEB_DIR / "index.html").is_file():
        parser.error(f"no hay compilación de la web en {WEB_DIR}: ejecuta npm run build en web/")
    with tempfile.TemporaryDirectory(prefix="ptb-e2e-") as directory:
        data_dir = Path(directory)
        write_firered(data_dir)
        uvicorn.run(create_app(Settings(data_dir, WEB_DIR)), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
