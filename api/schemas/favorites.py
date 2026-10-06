"""Requests and responses of the favourites (RF-03, RF-04)."""

from datetime import datetime

from pydantic import BaseModel, Field


class FavoriteOut(BaseModel):
    pokemon: str = Field(description="Identificador de la forma, p. ej. `vulpix-alola`.")
    name: str = Field(description="Nombre en español.")
    dex_number: int = Field(description="Número de la Pokédex Nacional.")
    types: list[str] = Field(description="Tipos actuales (de la última generación cargada).")
    image_url: str | None = Field(
        description="URL de su imagen en esta API (`/api/pokemon/{pokemon}/image`); nula si la "
        "forma no tiene imagen."
    )
    added_at: datetime


class FavoritesOut(BaseModel):
    total: int = Field(description="Número de favoritos.")
    favorites: list[FavoriteOut] = Field(description="En orden de la Pokédex Nacional.")
