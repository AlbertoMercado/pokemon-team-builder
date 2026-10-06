"""Versions of the application and of the loaded data (GET /api/meta)."""

import tomllib
from functools import cache
from pathlib import Path

from sqlmodel import Session

from api.repositories import meta as repository
from api.schemas.meta import DataVersion, Meta
from db.reference import IngestRun

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


@cache
def app_version() -> str:
    """The version in pyproject.toml: the project is not installed as a package."""
    with PYPROJECT.open("rb") as file:
        version: str = tomllib.load(file)["project"]["version"]
    return version


def data_version(run: IngestRun | None) -> DataVersion | None:
    """The load that built reference.sqlite, as the API shows it."""
    if run is None:
        return None
    return DataVersion(
        pokeapi_commit=run.pokeapi_commit,
        sprites_commit=run.sprites_commit,
        ingested_at=run.finished_at,
        games=run.games,
    )


def meta(reference: Session) -> Meta:
    return Meta(app_version=app_version(), data=data_version(repository.ingest_run(reference)))
