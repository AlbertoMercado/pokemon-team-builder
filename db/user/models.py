"""SQLModel models of user.sqlite: the user's favourites, settings, journey and confirmations.

Columns that point to reference.sqlite (``pokemon``, ``game``, ``fact_key``) hold natural keys
and cannot be foreign keys, because they live in another file (ADR-0003). Tables and columns
are documented in docs/02-ddt/modelo-datos.md.
"""

from datetime import date, datetime

from sqlalchemy import JSON, CheckConstraint, Column, ForeignKey, Integer, MetaData
from sqlmodel import Field, SQLModel

from db.user.values import ConfirmedValue

# Stable constraint names, so that Alembic can alter them in SQLite's batch mode.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

MAX_WEIGHT = 10
TEAM_SIZE = 6


class UserModel(SQLModel):
    """Base class of every table in user.sqlite, with its own ``MetaData`` (ADR-0003)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Favorite(UserModel, table=True):
    """A favourite form: the evolution the user wants to reach (RF-04, RN-09)."""

    __tablename__ = "favorite"

    pokemon: str = Field(primary_key=True)
    added_at: datetime


class RuleSetting(UserModel, table=True):
    """A configurable rule the user has changed (RF-06, RF-07).

    Rules without a row use the catalogue's defaults (CA-41). ``weight`` is only set for soft
    rules, from 0 to 10 (CA-05).
    """

    __tablename__ = "rule_setting"
    __table_args__ = (
        CheckConstraint(f"weight IS NULL OR weight BETWEEN 0 AND {MAX_WEIGHT}", name="weight"),
    )

    rule_id: str = Field(primary_key=True)
    enabled: bool = True
    weight: int | None = None


class HallOfFameEntry(UserModel, table=True):
    """A completed game, in the user's journey (RF-12, RN-16).

    ``sequence`` is the order of registration and breaks ties between equal dates.
    """

    __tablename__ = "hall_of_fame_entry"

    id: int | None = Field(default=None, primary_key=True)
    game: str
    completed_on: date
    sequence: int = Field(unique=True)
    notes: str | None = None


class HallOfFameMember(UserModel, table=True):
    """A member of a registered team, with its types in that game as a copy (CA-07)."""

    __tablename__ = "hall_of_fame_member"
    __table_args__ = (CheckConstraint(f"position BETWEEN 1 AND {TEAM_SIZE}", name="position"),)

    entry: int = Field(
        sa_column=Column(
            Integer, ForeignKey("hall_of_fame_entry.id", ondelete="CASCADE"), primary_key=True
        )
    )
    position: int = Field(primary_key=True)
    pokemon: str
    types: list[str] = Field(sa_type=JSON)


class FactConfirmation(UserModel, table=True):
    """A reviewable value confirmed or corrected by the user (RN-18, RF-15).

    ``confirmed_value`` is a boolean, or the list of Pokémon of a key battle.
    ``proposed_value_hash`` is the hash of the value proposed when it was confirmed: if a new
    load proposes something else, the confirmation no longer applies.
    """

    __tablename__ = "fact_confirmation"

    fact_key: str = Field(primary_key=True)
    game: str
    confirmed_value: ConfirmedValue = Field(sa_type=JSON)
    proposed_value_hash: str
    confirmed_at: datetime
