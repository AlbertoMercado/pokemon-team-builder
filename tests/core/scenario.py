"""The real FireRed scenario: a ``GameContext`` built from ``fixtures/firered.json``.

The extract comes from a real ``reference.sqlite`` (see ``fixtures/README.md``). Inferred and
pending values are taken as confirmed by the user (RN-18): the scenario uses the proposals of
the load as they are.
"""

import json
from collections.abc import Iterable
from functools import cache
from pathlib import Path
from typing import TypedDict

from core.domain import (
    Availability,
    Candidate,
    EvolutionStep,
    GameContext,
    GameInfo,
    KeyBattle,
    PokemonData,
    PoolEntry,
    Rival,
    Stage,
    TypeChart,
)
from core.rules.catalog import RuleSettings

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "firered.json"

# A plausible list of favourites: starters, classics, the three Eevee evolutions, Dragonite,
# a random evolution (none in Kanto), trade evolutions and two that cannot be bred.
FAVORITES = (
    "venusaur",
    "charizard",
    "blastoise",
    "butterfree",
    "pidgeot",
    "ninetales",
    "arcanine",
    "alakazam",
    "machamp",
    "tentacruel",
    "golem",
    "magneton",
    "dugtrio",
    "cloyster",
    "gengar",
    "exeggutor",
    "rhydon",
    "kangaskhan",
    "starmie",
    "scyther",
    "gyarados",
    "lapras",
    "vaporeon",
    "jolteon",
    "flareon",
    "aerodactyl",
    "snorlax",
    "zapdos",
    "dragonite",
    "mewtwo",
)


class _PokemonJson(TypedDict):
    slug: str
    species: str
    name: str
    dex_number: int
    generation: int
    types: list[str]
    evolution_chain: int
    stages: list[dict[str, str | bool]]
    line_egg_groups: list[str]
    evolution_steps: list[dict[str, object]]
    region: str | None
    is_legendary: bool
    is_mythical: bool
    exists_in_game: bool
    can_arrive: bool


@cache
def _data() -> dict[str, object]:
    data: dict[str, object] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data


def _pokemon(raw: _PokemonJson) -> PokemonData:
    stages = tuple(
        Stage(
            str(s["pokemon"]),
            str(s["species"]),
            bool(s["is_baby"]),
            bool(s["requires_incense"]),
        )
        for s in raw["stages"]
    )
    steps = []
    for step in raw["evolution_steps"]:
        conditions = step["conditions"]
        assert isinstance(conditions, dict)
        steps.append(
            EvolutionStep(
                str(step["from"]), str(step["to"]), str(step["trigger"]), tuple(conditions.items())
            )
        )
    return PokemonData(
        slug=raw["slug"],
        species=raw["species"],
        dex_number=raw["dex_number"],
        name=raw["name"],
        generation=raw["generation"],
        types=tuple(raw["types"]),
        evolution_chain=raw["evolution_chain"],
        stages=stages,
        line_egg_groups=frozenset(raw["line_egg_groups"]),
        evolution_steps=tuple(steps),
        region=raw["region"],
        is_legendary=raw["is_legendary"],
        is_mythical=raw["is_mythical"],
    )


@cache
def all_pokemon() -> dict[str, tuple[PokemonData, Availability]]:
    """Every form that can arrive at FireRed, with its availability."""
    raw_list = _data()["pokemon"]
    assert isinstance(raw_list, list)
    result: dict[str, tuple[PokemonData, Availability]] = {}
    for raw in raw_list:
        data = _pokemon(raw)
        result[data.slug] = (data, Availability(raw["exists_in_game"], raw["can_arrive"]))
    return result


def _type_chart() -> TypeChart:
    game = _data()["game"]
    types = _data()["types"]
    efficacy = _data()["type_efficacy"]
    assert isinstance(game, dict)
    assert isinstance(types, list)
    assert isinstance(efficacy, list)
    factors = {(a, d): f for a, d, f in efficacy}
    return TypeChart.from_hundredths(game["generation"], types, factors)


def _key_battles() -> tuple[KeyBattle, ...]:
    battles = _data()["key_battles"]
    assert isinstance(battles, list)
    return tuple(
        KeyBattle(
            slug=b["slug"],
            category=b["category"],
            trainer=b["trainer"],
            rivals=tuple(Rival(r["pokemon"], tuple(r["types"])) for r in b["rivals"]),
        )
        for b in battles
    )


def firered_context(
    favorites: Iterable[str] = FAVORITES, settings: RuleSettings | None = None
) -> GameContext:
    """FireRed with ``favorites``; every other form that can arrive is in the pool."""
    game = _data()["game"]
    assert isinstance(game, dict)
    known = all_pokemon()
    chosen = list(favorites)
    return GameContext(
        game=GameInfo(
            game["slug"],
            game["generation"],
            frozenset(game["mechanics"]),
            starters=frozenset(game["starters"]),
        ),
        type_chart=_type_chart(),
        favorites=tuple(Candidate(*known[slug]) for slug in chosen),
        pool=tuple(PoolEntry(*known[slug], True) for slug in known if slug not in chosen),
        key_battles=_key_battles(),
        settings=settings or RuleSettings.defaults(),
    )
