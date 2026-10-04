"""Response of the target games (RF-05)."""

from pydantic import BaseModel, Field


class GameOut(BaseModel):
    game: str = Field(description="Identificador del juego, p. ej. `firered`.")
    name: str = Field(description="Nombre en español.")
    generation: int
    version_group: str = Field(description="Grupo de versiones, p. ej. `firered-leafgreen`.")
