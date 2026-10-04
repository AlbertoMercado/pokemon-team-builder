"""Command line interface of the ingest: ``uv run python -m ingest``.

Documented in docs/05-operacion/ingesta.md.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from ingest.load import build_reference
from ingest.sources import Source

DEFAULT_DATA_DIR = Path("data")
REFERENCE_FILE_NAME = "reference.sqlite"


def default_sources() -> list[Source]:
    """Sources of a full load. Empty until the PokeAPI adapter exists (phase 3)."""
    return []


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
        help="directorio de datos donde se escribe reference.sqlite (por defecto: data)",
    )
    args = parser.parse_args(argv)

    data_dir: Path = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    report = build_reference(default_sources(), data_dir / REFERENCE_FILE_NAME)
    print(report.render())
    return 0 if report.succeeded else 1
