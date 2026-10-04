"""Metadata of the load that built reference.sqlite."""

from datetime import datetime

from sqlalchemy import JSON
from sqlmodel import Field

from db.reference.base import ReferenceModel


class IngestRun(ReferenceModel, table=True):
    """The ingest run that generated the file. There is a single row; the API exposes it.

    ``pokeapi_commit`` is null only when the load includes no PokeAPI data (e.g. in tests).
    """

    __tablename__ = "ingest_run"

    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime
    finished_at: datetime
    pokeapi_commit: str | None = None
    games: list[str] = Field(default_factory=list, sa_type=JSON)
    summary: dict[str, int] = Field(default_factory=dict, sa_type=JSON)
