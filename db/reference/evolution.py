"""Evolution steps applicable in each version group (RN-07, RN-09, RN-15, RN-20)."""

from sqlalchemy import JSON
from sqlmodel import Field

from db.reference.base import ReferenceModel

type ConditionValue = str | int | bool


class EvolutionStep(ReferenceModel, table=True):
    """One way of evolving ``from_pokemon`` into ``to_pokemon`` in a version group.

    ``trigger`` (``level-up``, ``trade``, ``use-item``, ``shed``…) and ``conditions`` (the
    non-empty PokeAPI conditions, e.g. ``{"minimum_happiness": 160, "time_of_day": "day"}``)
    are stored as PokeAPI gives them. Deciding whether a step is tedious or random is a
    business rule and belongs to ``core/evolution.py``. A step may have several rows when
    there are alternative methods.
    """

    __tablename__ = "evolution_step"

    id: int | None = Field(default=None, primary_key=True)
    version_group: str = Field(foreign_key="version_group.slug", index=True)
    from_pokemon: str = Field(foreign_key="pokemon.slug")
    to_pokemon: str = Field(foreign_key="pokemon.slug")
    trigger: str
    conditions: dict[str, ConditionValue] = Field(default_factory=dict, sa_type=JSON)
