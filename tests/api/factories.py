"""Builders of reference.sqlite files for the API tests.

Each test creates the reference data it needs in a temporary data directory, with the models of
``db/reference``, as ``tests/core/builders.py`` does for the engine.
"""

from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from db.reference import IngestRun, create_reference_schema
from db.sqlite import create_sqlite_engine

LOADED_AT = datetime(2026, 10, 4, 10, 0, 0, tzinfo=UTC)


def reference_database(
    data_dir: Path,
    *,
    pokeapi_commit: str | None = "bc92d3b",
    games: tuple[str, ...] = ("firered", "leafgreen"),
) -> Path:
    """An empty reference.sqlite with the record of its load."""
    path = data_dir / "reference.sqlite"
    engine = create_sqlite_engine(path)
    create_reference_schema(engine)
    with Session(engine) as session:
        session.add(
            IngestRun(
                started_at=LOADED_AT,
                finished_at=LOADED_AT,
                pokeapi_commit=pokeapi_commit,
                games=list(games),
            )
        )
        session.commit()
    engine.dispose()
    return path
