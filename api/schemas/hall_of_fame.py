"""Requests and responses of the Hall of Fame: the user's journey (RF-12, RF-13, RN-16)."""

from datetime import date

from pydantic import BaseModel, Field, model_validator

from db.user.models import TEAM_SIZE

MEMBERS_DESCRIPTION = (
    "Las formas del equipo, de 1 a 6, en orden (`vulpix-alola` para Vulpix de Alola). Puede "
    "repetirse una forma."
)


class HallOfFameMemberOut(BaseModel):
    position: int = Field(description="Posición en el equipo, de 1 a 6.")
    pokemon: str = Field(description="Identificador de la forma.")
    name: str = Field(description="Nombre en español.")
    types: list[str] = Field(description="Tipos que tenía en ese juego, copiados al registrarlo.")
    image_url: str | None = Field(
        description="URL de su imagen en esta API (`/api/pokemon/{pokemon}/image`); nula si la "
        "forma no tiene imagen."
    )


class HallOfFameEntryOut(BaseModel):
    id: int
    game: str = Field(description="Identificador del juego completado.")
    game_name: str = Field(description="Nombre en español del juego.")
    generation: int | None = Field(
        description="Generación del juego (la de su lanzamiento); nula si ya no está cargado."
    )
    completed_on: date
    notes: str | None
    order: int = Field(
        description="Posición en el recorrido: por fecha y, a igualdad, por orden de registro."
    )
    last: bool = Field(description="Si es el último juego completado del recorrido.")
    members: list[HallOfFameMemberOut]


class HallOfFameEntryIn(BaseModel):
    game: str = Field(description="Juego completado: cualquiera de los cargados.")
    completed_on: date = Field(description="Cuándo se completó.")
    notes: str | None = None
    members: list[str] = Field(min_length=1, max_length=TEAM_SIZE, description=MEMBERS_DESCRIPTION)


class HallOfFamePatch(BaseModel):
    """What to change; at least one field. ``notes: null`` removes the notes."""

    game: str | None = None
    completed_on: date | None = None
    notes: str | None = None
    members: list[str] | None = Field(
        default=None, min_length=1, max_length=TEAM_SIZE, description=MEMBERS_DESCRIPTION
    )

    @model_validator(mode="after")
    def _something(self) -> "HallOfFamePatch":
        if not self.model_fields_set:
            raise ValueError("indica al menos un campo")
        for name in ("game", "completed_on", "members"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} no puede ser nulo")
        return self
