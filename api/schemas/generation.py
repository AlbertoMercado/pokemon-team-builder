"""Response of a generation of teams (RF-08, RF-09, RF-10).

Scores are rounded integers whose contributions add up to the total (CA-51); the engine
decides the order and the ties with the exact values.
"""

from pydantic import BaseModel, Field

from api.schemas.meta import DataVersion
from api.schemas.review import ReviewFactOut, ReviewValue
from core.engine import GenerationStatus, IncompleteReason
from core.review import FactKind
from core.rules.candidate import DiscardReason
from core.rules.team import PresenceStatus


class PokemonOut(BaseModel):
    pokemon: str = Field(description="Identificador de la forma.")
    name: str = Field(description="Nombre en español.")
    dex_number: int = Field(description="Número de la Pokédex Nacional.")
    types: list[str] = Field(description="Tipos en el juego objetivo, el primario primero.")


class RuleScoreOut(BaseModel):
    """What one active soft rule adds to the team's score (RF-09)."""

    rule_id: str
    name: str
    weight: int = Field(description="Peso de la regla, de 0 a 10.")
    score: int = Field(description="Puntuación de la regla en el equipo, en porcentaje (0 a 100).")
    contribution: int = Field(
        description="Lo que aporta al total (peso · puntuación), redondeado de forma que las "
        "aportaciones sumen la puntuación del equipo."
    )
    penalized: list[str] = Field(description="Miembros que cuentan en contra.")


class SuggestionOut(BaseModel):
    pokemon: PokemonOut
    gain: int = Field(description="Lo que aportaría a la puntuación del equipo, redondeado.")
    verified: bool = Field(description="Falso si alguno de sus datos está sin confirmar (CA-31).")


class OpenSlotsOut(BaseModel):
    count: int = Field(description="Cuántos huecos son.")
    rule_id: str | None = Field(
        description="La regla de presencia que reserva el hueco; nula si son huecos libres."
    )
    suggestions: list[SuggestionOut] = Field(
        description="Todas las que encajan, de mejor a peor (CA-50). Con varios huecos libres, "
        "cada una encaja con el equipo, pero no necesariamente con las demás."
    )


class TeamOut(BaseModel):
    members: list[str] = Field(description="Los miembros, en orden de la Pokédex Nacional.")
    score: int = Field(description="Puntuación del equipo, redondeada.")
    dual_type_members: int = Field(description="Miembros con dos tipos, para desempatar (RN-19).")
    breakdown: list[RuleScoreOut] = Field(
        description="Las reglas blandas activas, en orden del catálogo."
    )
    open_slots: list[OpenSlotsOut] = Field(
        description="Huecos con sus sugerencias, si el equipo tiene menos de 6 (RN-08)."
    )


class GroupOut(BaseModel):
    """Tied teams that only differ in interchangeable members (CA-33)."""

    positions: list[list[PokemonOut]] = Field(
        description="Por cada posición, los Pokémon que la pueden ocupar, todos con los mismos "
        "tipos. Cada combinación es uno de los equipos del grupo."
    )
    teams: list[TeamOut]


class DiscardOut(BaseModel):
    pokemon: str
    name: str
    rule_id: str
    reason: DiscardReason = Field(
        description="`generation`, `game` o `arrival` (RN-03), `breeding` (RN-11) o "
        "`journey` (RN-16)."
    )
    detail: str = Field(description="Explicación en español.")
    fact_key: str | None = Field(
        description="El dato confirmado por el usuario que decidió el descarte, si lo hay."
    )


class PresenceOut(BaseModel):
    rule_id: str
    level: int = Field(description="Nivel de la regla en el DDF que se aplica.")
    status: PresenceStatus = Field(
        description="`candidates` (el equipo incluye una de `options`), `reserved` (se reserva "
        "un hueco para una de `options`, que no son favoritos) o `unmet` (no se puede cumplir)."
    )
    options: list[str]
    detail: str


class ConfirmedFactOut(BaseModel):
    fact_key: str
    kind: FactKind
    name: str = Field(description="Nombre en español de la mecánica, el entrenador o el Pokémon.")
    value: ReviewValue


class GenerationOut(BaseModel):
    game: str
    status: GenerationStatus = Field(
        description="`complete` si hay equipos de 6 favoritos; si no, `incomplete` (RN-08)."
    )
    incomplete_reason: IncompleteReason | None = Field(
        description="Si es incompleto: `reserved_slot` (una regla de presencia necesita un "
        "Pokémon que no es favorito), `not_enough_candidates` (menos de 6 válidos) o "
        "`no_valid_team` (no hay 6 que cumplan juntos las reglas)."
    )
    score: int = Field(description="Puntuación de los equipos recomendados, redondeada.")
    groups: list[GroupOut] = Field(
        description="Los equipos empatados en cabeza, ya desempatados con RN-19, agrupados."
    )
    discards: list[DiscardOut] = Field(
        description="Favoritos descartados, en orden de la Pokédex Nacional (RF-10)."
    )
    presence: list[PresenceOut] = Field(description="Las reglas de presencia activas.")
    confirmed_facts: list[ConfirmedFactOut] = Field(
        description="Datos confirmados por el usuario que intervienen en la generación (RF-09)."
    )
    data_version: DataVersion | None = Field(description="La carga de datos usada.")


class PendingDataDetail(BaseModel):
    message: str
    pending: list[ReviewFactOut] = Field(description="Los datos que faltan por confirmar.")


class PendingDataOut(BaseModel):
    """Body of the 409 when some data that takes part is still unverified (RN-18)."""

    detail: PendingDataDetail
