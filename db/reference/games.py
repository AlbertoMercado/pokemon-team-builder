"""Generations, version groups, games, the game catalogue and per-game data (RN-03, RN-15,
RN-21, RF-05, RF-25)."""

from enum import StrEnum

from sqlalchemy import JSON, CheckConstraint
from sqlmodel import Field

from db.reference.base import Origin, ReferenceModel, enum_column, origin_check


class Generation(ReferenceModel, table=True):
    """A main-series generation, identified by its number (1 to 9)."""

    __tablename__ = "generation"

    number: int = Field(primary_key=True)
    slug: str = Field(unique=True)


class VersionGroup(ReferenceModel, table=True):
    """Games that share data, such as ``firered-leafgreen``.

    Evolution steps are resolved per version group. ``order`` is PokeAPI's chronological
    order and decides which evolution rows apply to a group (see the data load plan).
    """

    __tablename__ = "version_group"

    slug: str = Field(primary_key=True)
    generation: int = Field(foreign_key="generation.number")
    order: int = Field(unique=True)


class Game(ReferenceModel, table=True):
    """A main-series game loaded with its data. ``is_target`` marks the complete ones: they
    have everything the rules need (RF-05, CA-67).

    ``cover`` is the path of its cover relative to the data directory and ``cover_source`` the
    title of its file in WikiDex, for the attribution; both null if it has no cover (RF-18,
    ADR-0011).
    """

    __tablename__ = "game"

    slug: str = Field(primary_key=True)
    name_es: str
    version_group: str = Field(foreign_key="version_group.slug")
    generation: int = Field(foreign_key="generation.number")
    release_order: int
    has_breeding: bool
    is_target: bool
    cover: str | None = None
    cover_source: str | None = None


class Platform(StrEnum):
    GAME_BOY = "game_boy"
    GAME_BOY_COLOR = "game_boy_color"
    GAME_BOY_ADVANCE = "game_boy_advance"
    DS = "ds"
    THREE_DS = "3ds"
    SWITCH = "switch"


class Playability(StrEnum):
    """Whether a game can be played on a current Nintendo system (CA-92)."""

    YES = "yes"
    UNKNOWN = "unknown"  # the user is asked


class MissingData(StrEnum):
    """What a game of the catalogue lacks to be complete (RF-05)."""

    GENERATION_NOT_LOADED = "generation_not_loaded"
    POKEMON = "pokemon"  # which Pokémon exist and can arrive (RN-03)
    MECHANICS = "mechanics"  # RN-15
    KEY_BATTLES = "key_battles"  # RN-17
    STARTERS = "starters"  # RN-21


class CatalogGame(ReferenceModel, table=True):
    """A game of the game catalogue (RF-25, CA-90), loaded or not.

    ``game`` is PokeAPI's version identifier; the games of a generation that is not loaded have
    no ``game`` row. ``catalog_order`` is the release order. ``receives_bred`` says whether a
    Pokémon bred in another game can reach it (CA-29, CA-91), and ``playable_now`` whether it
    is known to be playable on a current Nintendo system (CA-92). ``missing`` is what it lacks
    to be complete, empty if it is.
    """

    __tablename__ = "catalog_game"

    game: str = Field(primary_key=True)
    name_es: str
    generation: int
    platform: Platform = Field(sa_type=enum_column(Platform))
    catalog_order: int = Field(unique=True)
    receives_bred: bool
    playable_now: Playability = Field(sa_type=enum_column(Playability))
    missing: list[MissingData] = Field(default_factory=list, sa_type=JSON)


class GameMechanic(ReferenceModel, table=True):
    """A yes/no game mechanic that conditions evolutions, such as ``day_night_cycle`` (RN-15).

    Curated data, usually inferred, so the user confirms it (RN-18). ``value`` is null while
    the origin is ``pending``.
    """

    __tablename__ = "game_mechanic"
    __table_args__ = (CheckConstraint(origin_check("value", "origin"), name="value_origin"),)

    game: str = Field(primary_key=True, foreign_key="game.slug")
    mechanic: str = Field(primary_key=True)
    value: bool | None
    origin: Origin = Field(sa_type=enum_column(Origin))
    fact_key: str = Field(unique=True)


class GameStarter(ReferenceModel, table=True):
    """A starter of a target game, as the form of its final evolution there (RN-21, CA-59).

    Curated data that is not in doubt, so it has no origin and the user does not confirm it.
    """

    __tablename__ = "game_starter"

    game: str = Field(primary_key=True, foreign_key="game.slug")
    pokemon: str = Field(primary_key=True, foreign_key="pokemon.slug")


class GamePokemon(ReferenceModel, table=True):
    """Whether a Pokémon exists in a game and can arrive there in time (RN-03).

    ``can_arrive``: the stage that hatches from the egg can reach the game and evolve into
    the favourite before completing it (CA-28). The column is ``exists_in_game`` rather than
    ``exists`` because the latter is an SQL keyword. Each value is null while its origin is
    ``pending``. Their fact keys are ``pokemon:<game>:<pokemon>:exists`` and
    ``pokemon:<game>:<pokemon>:arrival``.
    """

    __tablename__ = "game_pokemon"
    __table_args__ = (
        CheckConstraint(origin_check("exists_in_game", "exists_origin"), name="exists_origin"),
        CheckConstraint(origin_check("can_arrive", "arrival_origin"), name="arrival_origin"),
    )

    game: str = Field(primary_key=True, foreign_key="game.slug")
    pokemon: str = Field(primary_key=True, foreign_key="pokemon.slug")
    exists_in_game: bool | None
    exists_origin: Origin = Field(sa_type=enum_column(Origin))
    can_arrive: bool | None
    arrival_origin: Origin = Field(sa_type=enum_column(Origin))
