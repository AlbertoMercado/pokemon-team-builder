"""Base class, shared enums and column helpers for the reference.sqlite models.

Reference models use their own ``MetaData`` so that creating the reference schema never
creates user.sqlite tables, and vice versa (ADR-0003).
"""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import MetaData
from sqlmodel import SQLModel


class ReferenceModel(SQLModel):
    """Base class of every table in reference.sqlite."""

    metadata = MetaData()


class Origin(StrEnum):
    """Where a reviewable value comes from (RN-18).

    ``confirmed`` is not stored here: confirmations live in user.sqlite.
    """

    AUTOMATIC = "automatic"
    INFERRED = "inferred"
    PENDING = "pending"


class BattleCategory(StrEnum):
    """Kind of key battle scored by RN-17."""

    GYM_LEADER = "gym_leader"
    ELITE_FOUR = "elite_four"
    CHAMPION = "champion"
    VILLAIN_BOSS = "villain_boss"
    RIVAL_FINAL = "rival_final"


def enum_column(enum_class: type[StrEnum]) -> SAEnum:
    """Column type that stores an enum as its text value (``"inferred"``), not its name."""
    return SAEnum(
        enum_class,
        values_callable=lambda members: [member.value for member in members],
        native_enum=False,
        length=max(len(member.value) for member in enum_class),
    )


def origin_check(value_column: str, origin_column: str) -> str:
    """SQL condition: a value is missing exactly when its origin is ``pending``."""
    return f"({value_column} IS NULL) = ({origin_column} = '{Origin.PENDING.value}')"
