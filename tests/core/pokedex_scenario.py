"""The real FireRed Pokédex scenario: a ``PokedexContext`` built from
``fixtures/pokedex_firered.json``.

The extract comes from a real ``reference.sqlite`` (see ``fixtures/README.md``): the 386
species of the National Pokédex with their encounters and evolutions in FireRed, and the
games that can send Pokémon to it.
"""

import json
from collections.abc import Iterable
from functools import cache
from pathlib import Path
from typing import TypedDict

from core.domain import EvolutionStep, GameInfo
from core.pokedex import DexSpecies, Encounter, PokedexContext, TransferSource

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pokedex_firered.json"

type _EncounterRow = tuple[str, str | None, str, int, list[str], str | None]


class _EvolutionJson(TypedDict):
    trigger: str
    conditions: dict[str, str | int | bool]


class _SpeciesJson(TypedDict):
    species: str
    number: int
    generation: int
    egg_groups: list[str]
    requires_incense: bool
    evolutions: list[dict[str, object]]
    encounters: list[_EncounterRow]
    is_event: bool


class _SourceJson(TypedDict):
    game: str
    max_species_generation: int | None
    starters: list[str]
    encounters: dict[str, list[_EncounterRow]]


class _GameJson(TypedDict):
    slug: str
    generation: int
    mechanics: list[str]
    has_breeding: bool
    starters: list[str]


class _PokedexJson(TypedDict):
    game: _GameJson
    species: list[_SpeciesJson]
    sources: list[_SourceJson]


@cache
def _data() -> _PokedexJson:
    data: _PokedexJson = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data


def _encounters(rows: Iterable[_EncounterRow]) -> tuple[Encounter, ...]:
    return tuple(
        Encounter(location, method, rarity, tuple(conditions), area, event_item)
        for location, area, method, rarity, conditions, event_item in rows
    )


def _species(raw: _SpeciesJson) -> DexSpecies:
    steps = []
    for step in raw["evolutions"]:
        conditions = step["conditions"]
        assert isinstance(conditions, dict)
        steps.append(
            EvolutionStep(
                str(step["from"]), raw["species"], str(step["trigger"]), tuple(conditions.items())
            )
        )
    return DexSpecies(
        species=raw["species"],
        number=raw["number"],
        generation=raw["generation"],
        egg_groups=frozenset(raw["egg_groups"]),
        requires_incense=raw["requires_incense"],
        evolutions=tuple(steps),
        encounters=_encounters(raw["encounters"]),
        is_event=raw["is_event"],
    )


@cache
def _all_species() -> tuple[DexSpecies, ...]:
    return tuple(_species(raw) for raw in _data()["species"])


def firered_pokedex(
    registered: Iterable[str] = (),
    impossible: Iterable[str] = (),
    completed: dict[str, Iterable[str]] | None = None,
    *,
    started: bool = True,
) -> PokedexContext:
    """FireRed's Pokédex with the user's marks.

    ``completed`` maps each source game in the Hall of Fame to the species registered in its
    Pokédex; the other sources are not completed.
    """
    data = _data()
    game = data["game"]
    completed = completed or {}
    sources = tuple(
        TransferSource(
            game=raw["game"],
            completed=raw["game"] in completed,
            registered=frozenset(completed.get(raw["game"], ())),
            encounters={s: _encounters(rows) for s, rows in raw["encounters"].items()},
            max_species_generation=raw["max_species_generation"],
            starters=frozenset(raw["starters"]),
        )
        for raw in data["sources"]
    )
    return PokedexContext(
        game=GameInfo(game["slug"], game["generation"], frozenset(game["mechanics"])),
        has_breeding=game["has_breeding"],
        species=_all_species(),
        registered=frozenset(registered),
        impossible=frozenset(impossible),
        started=started,
        sources=sources,
        starters=frozenset(game["starters"]),
    )
