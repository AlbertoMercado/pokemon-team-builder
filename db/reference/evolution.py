"""Evolution steps applicable in each version group, and the category of each evolution
method (RN-07, RN-09, RN-15, RN-20)."""

from enum import StrEnum

from sqlalchemy import JSON, CheckConstraint
from sqlmodel import Field

from db.reference.base import ReferenceModel, enum_column

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


class LevelMove(ReferenceModel, table=True):
    """A move that ``pokemon`` learns by levelling up in a version group, at ``level``.

    Only the moves that some evolution needs to know (``known_move``), to decide whether that
    step is tedious: it is not if the Pokémon learns the move by level from level 2 (RN-15,
    CA-32). At level 1 it only learns it with the move reminder.
    """

    __tablename__ = "level_move"

    pokemon: str = Field(primary_key=True, foreign_key="pokemon.slug")
    version_group: str = Field(primary_key=True, foreign_key="version_group.slug")
    move: str = Field(primary_key=True)
    level: int = Field(primary_key=True)


class MethodKind(StrEnum):
    TRIGGER = "trigger"
    CONDITION = "condition"


class MethodCategory(StrEnum):
    EASY = "easy"
    TEDIOUS = "tedious"
    RANDOM = "random"


class TediumReason(StrEnum):
    """Why a tedious method is tedious, to explain it in the breakdown (RN-15)."""

    TRADE = "trade"
    SHED = "shed"
    STATS = "stats"
    TIME_OF_DAY = "time_of_day"
    BEAUTY = "beauty"
    LOCATION = "location"
    PARTY = "party"
    MOVE = "move"
    OTHER = "other"


class EvolutionMethod(ReferenceModel, table=True):
    """The category of an evolution trigger or condition, from ``evolution_methods.yaml``.

    ``name`` is PokeAPI's identifier of the trigger, or the key of the condition in
    ``EvolutionStep.conditions``. Only a tedious method has a ``reason``.
    ``requires_mechanic`` is the game mechanic without which the step is impossible there;
    ``unless_learnt_by_level`` marks the methods that need the moves learnt by level (CA-32,
    CA-45). Steps whose methods are not here block the load (CA-42, ADR-0008).
    """

    __tablename__ = "evolution_method"
    __table_args__ = (
        CheckConstraint("(reason IS NULL) = (category != 'tedious')", name="tedious_reason"),
    )

    kind: MethodKind = Field(primary_key=True, sa_type=enum_column(MethodKind))
    name: str = Field(primary_key=True)
    category: MethodCategory = Field(sa_type=enum_column(MethodCategory))
    reason: TediumReason | None = Field(default=None, sa_type=enum_column(TediumReason))
    requires_mechanic: str | None = None
    unless_learnt_by_level: bool = False
