"""Requests and responses of the review of unverified data (RF-15, RN-18)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, StrictBool, StrictStr

from core.review import FactKind

type ReviewValue = StrictBool | list[StrictStr]

VALUE_DESCRIPTION = (
    "Un booleano (mecánica, existencia o llegada) o, en un combate clave, la lista de Pokémon "
    "de su equipo en orden."
)


class LoadedOrigin(StrEnum):
    """Origin of a reviewable value in the load (RN-18); automatic ones are not reviewed."""

    INFERRED = "inferred"
    PENDING = "pending"


class ReviewStatus(StrEnum):
    PENDING = "pending"  # the user has to confirm it before generating
    CONFIRMED = "confirmed"  # confirmed for the current proposal


class ReviewFactOut(BaseModel):
    fact_key: str = Field(
        description="Clave estable del dato, p. ej. `pokemon:firered:raichu:arrival`."
    )
    kind: FactKind = Field(
        description="`mechanic` (mecánica del juego), `key_battle` (equipo de un combate clave), "
        "`exists` (la forma se puede tener en el juego) o `arrival` (puede llegar y evolucionar "
        "antes de completarlo)."
    )
    subject: str = Field(description="La mecánica, el combate clave o la forma.")
    name: str = Field(description="Nombre en español de la mecánica, el entrenador o el Pokémon.")
    origin: LoadedOrigin = Field(
        description="`inferred` (con propuesta) o `pending` (sin propuesta)."
    )
    proposal: ReviewValue | None = Field(
        description=f"Valor propuesto por la carga; nulo si está pendiente. {VALUE_DESCRIPTION}"
    )
    status: ReviewStatus = Field(
        description="`pending` si hay que confirmarlo antes de generar; `confirmed` si ya está."
    )
    value: ReviewValue | None = Field(description="El valor confirmado; nulo si no lo está.")
    confirmed_at: datetime | None = Field(description="Cuándo se confirmó; nulo si no lo está.")
    outdated: bool = Field(
        description="Se confirmó, pero una carga posterior propone otro valor: hay que volver a "
        "confirmarlo."
    )
    source_url: str | None = Field(
        description="En un combate clave, la revisión de la página de WikiDex de la que sale su "
        "equipo (ADR-0004); nula en los demás datos o si no se conoce."
    )


class ReviewOut(BaseModel):
    game: str
    pending: int = Field(description="Datos que faltan por confirmar; con 0 se puede generar.")
    facts: list[ReviewFactOut] = Field(
        description="Los datos inferidos o pendientes que intervienen en la generación: primero "
        "los del juego (mecánicas y, con RN-17 activa, combates clave) y después los de cada "
        "favorito en orden de la Pokédex Nacional, salvo los ya descartados con datos conocidos."
    )


class ConfirmationIn(BaseModel):
    value: ReviewValue = Field(description=f"El valor propuesto o corregido. {VALUE_DESCRIPTION}")
