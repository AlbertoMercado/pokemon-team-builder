"""Command line interface of the ingest: ``uv run python -m ingest``.

Documented in docs/05-operacion/ingesta.md.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from ingest.checks import FIRST_LOAD_CHECKS
from ingest.load import build_reference
from ingest.sources import Source
from ingest.sources.curated import (
    CuratedDataError,
    CuratedSource,
    read_curated,
    read_pinned_commits,
)
from ingest.sources.pokeapi import PokeapiCsvSource
from ingest.sources.pokeapi.download import CsvCache, download
from ingest.sources.pokeapi.sprites import SpriteCache
from ingest.sources.wikidex import WikidexSource
from ingest.sources.wikidex.fetch import PageCache, fetch_page

DEFAULT_DATA_DIR = Path("data")
REFERENCE_FILE_NAME = "reference.sqlite"
# Written by the API in the same data directory; its keys are checked before replacing.
USER_FILE_NAME = "user.sqlite"
# Curated data is versioned with the code, so it is found next to it, not in --data-dir.
CURATED_DIR = Path(__file__).resolve().parent.parent / "data" / "curated"


def default_sources(data_dir: Path, *, offline: bool) -> list[Source]:
    """Sources of a full load. Caches live in ``<data_dir>/cache``."""
    curated = read_curated(CURATED_DIR)
    downloader = None if offline else download
    cache = CsvCache(data_dir / "cache" / "pokeapi", curated.pokeapi_commit, downloader)
    pokeapi = PokeapiCsvSource(cache, curated)
    pages = PageCache(data_dir / "cache" / "wikidex", None if offline else fetch_page)
    return [pokeapi, CuratedSource(curated), WikidexSource(curated, pages, pokeapi.index)]


def default_sprites(data_dir: Path, *, offline: bool) -> SpriteCache:
    """Sprites of the pinned commit, cached in ``<data_dir>/cache/pokeapi-sprites`` (ADR-0010)."""
    commit = read_pinned_commits(CURATED_DIR / "pokeapi.yaml").sprites_commit
    return SpriteCache(data_dir, commit, None if offline else download)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ingest and return the process exit code (0 on success, 1 on failure)."""
    parser = argparse.ArgumentParser(
        prog="python -m ingest",
        description="Construye reference.sqlite a partir de las fuentes de datos.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="directorio donde se escriben reference.sqlite y la caché (por defecto: data)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "no descargar nada: usar solo la caché y fallar si falta algún fichero de datos "
            "(una imagen que falta solo da un aviso)"
        ),
    )
    args = parser.parse_args(argv)

    data_dir: Path = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        sources = default_sources(data_dir, offline=args.offline)
        sprites = default_sprites(data_dir, offline=args.offline)
    except CuratedDataError as error:
        print(f"ERROR en los datos curados; no se ha cargado nada.\n  - {error}")
        return 1
    report = build_reference(
        sources,
        data_dir / REFERENCE_FILE_NAME,
        FIRST_LOAD_CHECKS,
        data_dir / USER_FILE_NAME,
        sprites,
    )
    print(report.render())
    return 0 if report.succeeded else 1
