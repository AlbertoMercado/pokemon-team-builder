"""Serves the API with the compiled web over the FireRed scenario, for the end-to-end tests.

    uv run python -m tests.e2e.serve [--port 8765]

Writes the real FireRed extract of the tests (``tests/api/scenario.py``), with the Pokédex of
FireRed and LeafGreen, as reference.sqlite in a temporary data directory, with a new
user.sqlite, and runs uvicorn with ``web/dist``, as the application runs installed. It uses
neither the network nor the user's data, and the directory is removed when it stops.
Playwright starts it (``web/playwright.config.ts``).

Every form gets a sprite and an artwork, and both games a cover, generated here: plain PNG of
deliberately different shapes (tall, wide, small), so that the layout tests
(``web/e2e/layout.spec.ts``) notice an image that does not keep its box (#65). Real images are
never versioned (ADR-0010, ADR-0011).
"""

import argparse
import tempfile
from pathlib import Path

import uvicorn
from PIL import Image
from sqlmodel import Session, col, select

from api.config import Settings
from api.main import create_app
from db.reference import Game, Pokemon
from db.sqlite import create_sqlite_engine
from tests.api.scenario import write_firered

WEB_DIR = Path(__file__).resolve().parents[2] / "web" / "dist"
DEFAULT_PORT = 8765
SPRITES = Path("cache/pokeapi-sprites")
COVERS = Path("cache/wikidex/covers")
# Width and height of the generated images, in turn: tall, wide, small and square. Trimmed
# sprites and covers have any proportion; each list mixes them.
SPRITE_SHAPES = ((24, 56), (56, 24), (12, 12), (40, 40))
ARTWORK_SHAPES = ((120, 256), (256, 120), (256, 256))
COVER_SHAPES = {"firered": (180, 256), "leafgreen": (256, 180)}
COLOR = (200, 60, 60, 255)


def _png(data_dir: Path, path: Path, size: tuple[int, int]) -> str:
    """Writes a plain PNG of ``size`` at ``path``, relative to ``data_dir``; returns ``path``."""
    target = data_dir / path
    target.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, COLOR).save(target)
    return path.as_posix()


def write_images(data_dir: Path) -> None:
    """Gives every form of reference.sqlite its sprite and artwork, and every game its cover."""
    engine = create_sqlite_engine(data_dir / "reference.sqlite")
    with Session(engine) as session:
        forms = session.exec(select(Pokemon).order_by(col(Pokemon.pokeapi_id))).all()
        for index, form in enumerate(forms):
            name = f"{form.pokeapi_id}.png"
            form.image = _png(
                data_dir, SPRITES / "trimmed" / name, SPRITE_SHAPES[index % len(SPRITE_SHAPES)]
            )
            form.artwork = _png(
                data_dir,
                SPRITES / "official-artwork-256" / name,
                ARTWORK_SHAPES[index % len(ARTWORK_SHAPES)],
            )
        for game in session.exec(select(Game)).all():
            game.cover = _png(data_dir, COVERS / f"{game.slug}-256.png", COVER_SHAPES[game.slug])
            game.cover_source = f"Archivo:Carátula de {game.name_es}.png"
        session.commit()
    engine.dispose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    if not (WEB_DIR / "index.html").is_file():
        parser.error(f"no hay compilación de la web en {WEB_DIR}: ejecuta npm run build en web/")
    with tempfile.TemporaryDirectory(prefix="ptb-e2e-") as directory:
        data_dir = Path(directory)
        write_firered(data_dir)
        write_images(data_dir)
        uvicorn.run(create_app(Settings(data_dir, WEB_DIR)), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
