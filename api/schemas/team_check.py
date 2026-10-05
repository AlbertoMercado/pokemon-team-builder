"""Request and response of the check of a chosen team (RF-12, CA-53)."""

from pydantic import BaseModel, Field

from db.user.models import TEAM_SIZE


class TeamCheckIn(BaseModel):
    members: list[str] = Field(
        min_length=1,
        max_length=TEAM_SIZE,
        description="Las formas del equipo elegido, de 1 a 6, sin repetir: favoritos o "
        "sugerencias del resultado.",
    )


class TeamProblemOut(BaseModel):
    rule_id: str = Field(description="La regla que no se cumple.")
    members: list[str] = Field(
        description="Los miembros afectados: uno (un filtro), dos (incompatibles) o ninguno "
        "(una regla de presencia que el equipo no cumple)."
    )
    detail: str = Field(description="Explicación en español.")


class TeamCheckOut(BaseModel):
    valid: bool = Field(description="Si el equipo cumple las reglas activas.")
    problems: list[TeamProblemOut] = Field(
        description="Por cada regla que no se cumple: primero los filtros por miembro, después "
        "los pares incompatibles y por último las reglas de presencia."
    )
    unverified: list[str] = Field(
        description="Miembros con datos sin confirmar (CA-31). No es un problema."
    )
