"""Versions of the application and of the loaded data (GET /api/meta)."""

import tomllib
from functools import cache
from pathlib import Path

from sqlmodel import Session

from api.repositories import meta as repository
from api.schemas.meta import DataVersion, Meta

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


@cache
def app_version() -> str:
    """The version in pyproject.toml: the project is not installed as a package."""
    with PYPROJECT.open("rb") as file:
        version: str = tomllib.load(file)["project"]["version"]
    return version


def meta(reference: Session) -> Meta:
    run = repository.ingest_run(reference)
    data = None
    if run is not None:
        data = DataVersion(
            pokeapi_commit=run.pokeapi_commit, ingested_at=run.finished_at, games=run.games
        )
    return Meta(app_version=app_version(), data=data)
