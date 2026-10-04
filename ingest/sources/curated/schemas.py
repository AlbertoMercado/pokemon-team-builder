"""Schemas of the curated YAML files in ``data/curated/`` (ADR-0005).

Each model validates one file: unknown keys, wrong types or inconsistent values (such as a
pending value that has a value) fail the load. The files and their meaning are documented
in docs/02-ddt/datos-curados.md.
"""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from db.reference import BattleCategory

SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"

type Slug = str
type ReviewableOrigin = Literal["automatic", "inferred", "pending"]
type Mechanic = Literal["day_night_cycle", "contests"]


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


class PinnedCommitFile(CuratedModel):
    """``pokeapi.yaml``: full SHA of the pinned PokeAPI commit (ADR-0004)."""

    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
