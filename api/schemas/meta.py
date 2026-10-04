"""Response of GET /api/meta."""

from datetime import datetime

from pydantic import BaseModel, Field


class DataVersion(BaseModel):
    """The load that built reference.sqlite."""

    pokeapi_commit: str | None = Field(description="Commit del volcado de PokeAPI usado.")
    ingested_at: datetime = Field(description="Cuándo terminó la carga.")
    games: list[str] = Field(description="Juegos cargados.")


class Meta(BaseModel):
    app_version: str = Field(description="Versión de la aplicación.")
    data: DataVersion | None = Field(description="La carga de los datos; nula si no hay registro.")
