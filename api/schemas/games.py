"""Response of the games: the target ones (RF-05) or every loaded game (RF-12)."""

from pydantic import BaseModel, Field


class GameOut(BaseModel):
    game: str = Field(description="Identificador del juego, p. ej. `firered`.")
    name: str = Field(description="Nombre en español.")
    generation: int
    version_group: str = Field(description="Grupo de versiones, p. ej. `firered-leafgreen`.")
    target: bool = Field(description="Si se puede elegir como juego objetivo (RF-05).")
