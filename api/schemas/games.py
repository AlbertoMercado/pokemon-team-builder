"""Response of the games: the target ones (RF-05) or every loaded game (RF-12), with their
covers (RF-18)."""

from pydantic import BaseModel, Field


class GameOut(BaseModel):
    game: str = Field(description="Identificador del juego, p. ej. `firered`.")
    name: str = Field(description="Nombre en español.")
    generation: int = Field(description="Generación del juego.")
    version_group: str = Field(description="Grupo de versiones, p. ej. `firered-leafgreen`.")
    target: bool = Field(description="Si se puede elegir como juego objetivo (RF-05).")
    cover_url: str | None = Field(
        description="URL de su portada en esta API (`/api/games/{game}/cover`); nula si el juego "
        "no tiene portada (RF-18)."
    )
    cover_source_url: str | None = Field(
        description="Página del fichero de la portada en WikiDex, su titular y procedencia "
        "(CA-56, ADR-0011); nula si el juego no tiene portada."
    )
