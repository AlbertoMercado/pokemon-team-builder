"""Schemas of the curated YAML files in ``data/curated/`` (ADR-0005).

Each model validates one file: unknown keys, wrong types or inconsistent values (such as a
pending value that has a value) fail the load. The files and their meaning are documented
in docs/02-ddt/datos-curados.md.
"""

import re
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from db.reference import BattleCategory

SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
COMMIT_PATTERN = r"^[0-9a-f]{40}$"
COVER_TITLE = re.compile(r"Archivo:[^|#\[\]{}]+\.(png|jpe?g)", re.IGNORECASE)

type Slug = str
type ReviewableOrigin = Literal["automatic", "inferred", "pending"]
type Mechanic = Literal["day_night_cycle", "contests"]
# Every mechanic a target game needs in games.yaml to be complete (RF-05).
MECHANICS: tuple[Mechanic, ...] = ("day_night_cycle", "contests")


class CuratedModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MechanicValue(CuratedModel):
    """A yes/no mechanic of a game. ``value`` is missing exactly when ``origin`` is pending."""

    value: bool | None = None
    origin: ReviewableOrigin
    note: str | None = None

    @model_validator(mode="after")
    def _value_matches_origin(self) -> Self:
        if (self.value is None) != (self.origin == "pending"):
            raise ValueError("value solo puede faltar, y debe faltar, si origin es pending")
        return self


class GamesFile(CuratedModel):
    """``games.yaml``: mechanics of each target game that condition evolutions (RN-15)."""

    games: dict[Slug, dict[Mechanic, MechanicValue]]


class StartersFile(CuratedModel):
    """``starters.yaml``: the starters of each game (RN-21, CA-87).

    Each starter is the form of its final evolution in that game, e.g. ``venusaur`` in
    FireRed (CA-59, CA-63). Which Pokémon a game offers to start is not in doubt, so the
    values have no origin.
    """

    games: dict[Slug, Annotated[list[Slug], Field(min_length=1)]]

    @model_validator(mode="after")
    def _unique_starters(self) -> Self:
        repeated = sorted(
            game for game, starters in self.games.items() if len(set(starters)) < len(starters)
        )
        if repeated:
            raise ValueError(f"iniciales repetidos en: {repeated}")
        return self


class BreedingFile(CuratedModel):
    """``breeding.yaml``: babies that only hatch when a parent holds an incense (CA-36).

    Maps the baby species to the incense it needs, e.g. ``azurill: sea-incense``.
    """

    incense_babies: dict[Slug, Slug]


class ArrivalRule(CuratedModel):
    """How the ingest proposes which Pokémon can arrive at a game in time (CA-28).

    With ``regional_pokedex``, a Pokémon can arrive if the stage that hatches from the egg
    and every stage up to it are in that Pokédex. Without it, arrival stays pending.
    """

    regional_pokedex: Slug | None = None
    origin: Literal["inferred", "pending"]
    note: str | None = None

    @model_validator(mode="after")
    def _pokedex_matches_origin(self) -> Self:
        if (self.regional_pokedex is None) != (self.origin == "pending"):
            raise ValueError("regional_pokedex solo puede faltar, y debe faltar, si es pending")
        return self


class ArrivalFile(CuratedModel):
    """``arrival.yaml``: arrival rule of each target game. Missing games stay pending."""

    games: dict[Slug, ArrivalRule]


class BattleEntry(CuratedModel):
    """A key battle of the list and where its team is on WikiDex.

    The team is in ``wikidex_page``, in the file's ``wikidex_section``. If that section has
    several teams, ``wikidex_team`` is the label that precedes the right one (the text of a
    ``;`` line, e.g. ``En Silph S.A.``). ``rival_starter_lines`` lists the starter lines of
    the rival, whose Pokémon are left out of the team (CA-26).
    """

    id: Slug = Field(pattern=SLUG_PATTERN)
    category: BattleCategory
    trainer: str
    wikidex_page: str
    wikidex_team: str | None = None
    rival_starter_lines: list[Slug] = Field(default_factory=list)
    note: str | None = None


class KeyBattlesFile(CuratedModel):
    """``key_battles/<file>.yaml``: key battles shared by the games of a version group.

    The order of ``battles`` is the usual order in the game (RN-17). ``wikidex_section`` is
    the title of the section with the games' teams on every trainer page.
    """

    games: list[Slug] = Field(min_length=1)
    wikidex_section: str
    battles: list[BattleEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_ids(self) -> Self:
        ids = [battle.id for battle in self.battles]
        duplicated = sorted({battle_id for battle_id in ids if ids.count(battle_id) > 1})
        if duplicated:
            raise ValueError(f"ids de combate repetidos: {duplicated}")
        return self


class CoversFile(CuratedModel):
    """``covers.yaml``: the title of the cover of each game in WikiDex (RF-18, ADR-0011).

    Titles have no common pattern, so each one is curated. A game without entry has no cover.
    """

    covers: dict[Slug, str]

    @model_validator(mode="after")
    def _file_titles(self) -> Self:
        wrong = sorted(
            game for game, title in self.covers.items() if not COVER_TITLE.fullmatch(title)
        )
        if wrong:
            raise ValueError(
                f"títulos que no son un fichero de imagen de WikiDex ('Archivo:….png'): {wrong}"
            )
        return self


class PokedexFile(CuratedModel):
    """``pokedex.yaml``: the Pokédex that each game completes (RN-22, CA-70).

    A list, because a game with a reduced Pokédex completes the union of those of the base
    game and its downloadable content.
    """

    games: dict[Slug, Annotated[list[Slug], Field(min_length=1)]]


class TransferGroup(CuratedModel):
    """Games that can send Pokémon to each other (RN-25).

    ``max_species_generation`` limits the species to those of that generation or earlier,
    such as 1 with the Time Capsule between the 1st and the 2nd generation.
    """

    games: list[Slug] = Field(min_length=2)
    max_species_generation: int | None = Field(default=None, ge=1)
    note: str | None = None

    @model_validator(mode="after")
    def _unique_games(self) -> Self:
        if len(set(self.games)) < len(self.games):
            raise ValueError(f"juegos repetidos en el grupo: {self.games}")
        return self


class TransfersFile(CuratedModel):
    """``transfers.yaml``: groups of games that can send Pokémon to each other (CA-78).

    Each game of a group can send to every other game of the group. If two groups join the
    same games, the least restrictive one applies.
    """

    groups: list[TransferGroup] = Field(min_length=1)


class EventGroup(CuratedModel):
    """Pokémon obtained in some games only through an event distribution (RN-24)."""

    games: list[Slug] = Field(min_length=1)
    pokemon: list[Slug] = Field(min_length=1)
    note: str | None = None


class EventsFile(CuratedModel):
    """``events.yaml``: the event Pokémon of each game (CA-78)."""

    events: list[EventGroup] = Field(min_length=1)


class LocationEntry(CuratedModel):
    """What PokeAPI lacks of a location: its Spanish name, or the event item without which it
    cannot be reached, such as the Mystic Ticket for Navel Rock."""

    name_es: str | None = Field(default=None, min_length=1)
    event_item: Slug | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _has_data(self) -> Self:
        if self.name_es is None and self.event_item is None:
            raise ValueError("cada lugar necesita name_es, event_item o los dos")
        return self


class LocationsFile(CuratedModel):
    """``locations.yaml``: Spanish names and event items of locations (ADR-0013)."""

    locations: dict[Slug, LocationEntry]


class PinnedCommitFile(CuratedModel):
    """``pokeapi.yaml``: full SHAs of the pinned commits of PokeAPI.

    ``commit`` is the one of the CSV dump (ADR-0004) and ``sprites_commit`` the one of the
    PokeAPI/sprites repository (ADR-0010).
    """

    commit: str = Field(pattern=COMMIT_PATTERN)
    sprites_commit: str = Field(pattern=COMMIT_PATTERN)
