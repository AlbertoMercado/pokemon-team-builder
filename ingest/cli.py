"""Command line interface of the ingest: ``uv run python -m ingest``.

Documented in docs/05-operacion/ingesta.md.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from ingest.checks import FIRST_LOAD_CHECKS
from ingest.load import build_reference
from ingest.sources import Source
from ingest.sources.pokeapi import PokeapiCsvSource, read_pinned_commit
from ingest.sources.pokeapi.download import CsvCache, download

DEFAULT_DATA_DIR = Path("data")
REFERENCE_FILE_NAME = "reference.sqlite"
# Curated data is versioned with the code, so it is found next to it, not in --data-dir.
CURATED_DIR = Path(__file__).resolve().parent.parent / "data" / "curated"


def default_sources(data_dir: Path, *, offline: bool) -> list[Source]:
    """Sources of a full load. Caches live in ``<data_dir>/cache``."""
    commit = read_pinned_commit(CURATED_DIR / "pokeapi.yaml")
    cache = CsvCache(data_dir / "cache" / "pokeapi", commit, None if offline else download)
    return [PokeapiCsvSource(cache)]


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
        help="no descargar nada: usar solo la caché y fallar si falta algún fichero",
    )
    args = parser.parse_args(argv)

    data_dir: Path = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    sources = default_sources(data_dir, offline=args.offline)
    report = build_reference(sources, data_dir / REFERENCE_FILE_NAME, FIRST_LOAD_CHECKS)
    print(report.render())
    return 0 if report.succeeded else 1
