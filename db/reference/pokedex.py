"""Pokédexes and the ways of obtaining each Pokémon in a game (RN-22, RN-24 to RN-26).

Encounters come from PokeAPI as it gives them: deciding which way is simpler is a business
rule and belongs to ``core/`` (ADR-0013). What PokeAPI lacks is curated: the Pokédex of each
game, the transfers between games, the event Pokémon and the missing Spanish names.
"""

from sqlalchemy import JSON, CheckConstraint, UniqueConstraint
from sqlmodel import Field

from db.reference.base import ReferenceModel


class Pokedex(ReferenceModel, table=True):
    """A Pokédex of PokeAPI, such as ``national`` or ``kanto``."""

    __tablename__ = "pokedex"

    slug: str = Field(primary_key=True)


class PokedexNumber(ReferenceModel, table=True):
    """Number of a loaded species in a Pokédex, which sets its order there (RN-23)."""

    __tablename__ = "pokedex_number"
    __table_args__ = (UniqueConstraint("pokedex", "number"),)

    pokedex: str = Field(primary_key=True, foreign_key="pokedex.slug")
    species: str = Field(primary_key=True, foreign_key="species.slug")
    number: int


class GamePokedex(ReferenceModel, table=True):
    """The Pokédex that a game completes (RN-22). Curated data."""

    __tablename__ = "game_pokedex"

    game: str = Field(primary_key=True, foreign_key="game.slug")
    pokedex: str = Field(primary_key=True, foreign_key="pokedex.slug")


class Location(ReferenceModel, table=True):
    """A place where Pokémon are obtained, such as ``celadon-city``.

    ``name_es`` comes from PokeAPI or, where it lacks it, from the curated data; null if
    neither has it, and then ``name_en`` is shown. ``event_item`` is the item handed out at an
    event without which the place cannot be reached, such as ``mystic-ticket`` for Navel Rock
    (curated).
    """

    __tablename__ = "location"

    slug: str = Field(primary_key=True)
    name_es: str | None = None
    name_en: str
    event_item: str | None = None


class Encounter(ReferenceModel, table=True):
    """A way of obtaining a Pokémon in a place of a game, as PokeAPI gives it (RN-26).

    ``method`` is PokeAPI's encounter method (``walk``, ``surf``, ``gift``, ``npc-trade``,
    ``roaming-grass``…) and ``conditions`` the sorted list of its condition values
    (``time-night``, ``starter-squirtle``, ``item-helix-fossil``…). ``area`` is the part of the
    place, such as ``b1f``, or null if the place has one. ``rarity`` is the probability, in
    percent, of meeting the Pokémon in that area with that method and those conditions.
    """

    __tablename__ = "encounter"
    __table_args__ = (
        CheckConstraint("rarity BETWEEN 1 AND 100", name="rarity_percent"),
        CheckConstraint("min_level <= max_level", name="level_range"),
    )

    id: int | None = Field(default=None, primary_key=True)
    game: str = Field(foreign_key="game.slug", index=True)
    location: str = Field(foreign_key="location.slug")
    area: str | None = None
    pokemon: str = Field(foreign_key="pokemon.slug", index=True)
    method: str
    conditions: list[str] = Field(default_factory=list, sa_type=JSON)
    rarity: int
    min_level: int
    max_level: int


class GameTransfer(ReferenceModel, table=True):
    """``from_game`` can send Pokémon to ``to_game`` (RN-25). Curated data.

    ``max_species_generation`` limits the species that can be sent to those of that generation
    or earlier, such as 1 with the Time Capsule; null if there is no limit.
    """

    __tablename__ = "game_transfer"
    __table_args__ = (CheckConstraint("from_game <> to_game", name="different_games"),)

    from_game: str = Field(primary_key=True, foreign_key="game.slug")
    to_game: str = Field(primary_key=True, foreign_key="game.slug")
    max_species_generation: int | None = Field(default=None, foreign_key="generation.number")


class EventPokemon(ReferenceModel, table=True):
    """A Pokémon obtained in a game through an event distribution (RN-24). Curated data."""

    __tablename__ = "event_pokemon"

    game: str = Field(primary_key=True, foreign_key="game.slug")
    pokemon: str = Field(primary_key=True, foreign_key="pokemon.slug")
