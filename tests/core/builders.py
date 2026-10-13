"""Readable constructors of engine data for the core tests.

They fill in sensible defaults so each test only states what matters to it, e.g.
``pokemon("gengar", ("ghost", "poison"), line=("gastly", "haunter"), steps=[...])``.

``EVOLUTION_METHODS`` is the real catalog of evolution methods, read from the curated data,
so the tests of RN-15 and RN-20 also check how it classifies each method.
"""

import zlib
from collections.abc import Iterable, Mapping, Sequence
from itertools import pairwise
from pathlib import Path

import yaml

from core.domain import (
    Availability,
    Candidate,
    ConditionValue,
    EvolutionCatalog,
    EvolutionMethod,
    EvolutionStep,
    GameContext,
    GameInfo,
    HallOfFameEntry,
    JourneyMember,
    KeyBattle,
    MethodCategory,
    PokemonData,
    PoolEntry,
    Rival,
    Stage,
    Tedium,
    TypeChart,
)
from core.rules.catalog import RuleSettings

CURATED_EVOLUTION_METHODS = (
    Path(__file__).resolve().parents[2] / "data" / "curated" / "evolution_methods.yaml"
)


def _evolution_methods(entries: Mapping[str, Mapping[str, str]]) -> dict[str, EvolutionMethod]:
    return {
        name: EvolutionMethod(
            MethodCategory(entry["category"]),
            Tedium(entry["reason"]) if "reason" in entry else None,
            entry.get("requires_mechanic"),
            bool(entry.get("unless_learnt_by_level", False)),
        )
        for name, entry in entries.items()
    }


def evolution_catalog() -> EvolutionCatalog:
    """The catalog of ``data/curated/evolution_methods.yaml``."""
    raw = yaml.safe_load(CURATED_EVOLUTION_METHODS.read_text(encoding="utf-8"))
    return EvolutionCatalog(
        _evolution_methods(raw["triggers"]), _evolution_methods(raw["conditions"])
    )


EVOLUTION_METHODS = evolution_catalog()

GEN1_TYPES = (
    "normal",
    "fighting",
    "flying",
    "poison",
    "ground",
    "rock",
    "bug",
    "ghost",
    "fire",
    "water",
    "grass",
    "electric",
    "psychic",
    "ice",
    "dragon",
)
GEN3_TYPES = (*GEN1_TYPES, "steel", "dark")


def type_chart(
    generation: int = 3,
    types: Sequence[str] = GEN3_TYPES,
    overrides: Mapping[tuple[str, str], int] | None = None,
) -> TypeChart:
    """A chart where every factor is x1 (100) except ``overrides``, in hundredths."""
    factors = {(a, d): 100 for a in types for d in types}
    factors.update(overrides or {})
    return TypeChart.from_hundredths(generation, types, factors)


def step(
    from_pokemon: str, to_pokemon: str, trigger: str = "level-up", **conditions: ConditionValue
) -> EvolutionStep:
    return EvolutionStep(from_pokemon, to_pokemon, trigger, tuple(conditions.items()))


def stage(slug: str, *, is_baby: bool = False, requires_incense: bool = False) -> Stage:
    return Stage(slug, slug, is_baby, requires_incense)


def pokemon(
    slug: str,
    types: Sequence[str] = ("normal",),
    *,
    line: Sequence[str] = (),
    steps: Sequence[EvolutionStep] | None = None,
    stages: Sequence[Stage] | None = None,
    dex_number: int = 1,
    generation: int = 1,
    chain: int | None = None,
    egg_groups: Iterable[str] = ("monster",),
    species: str | None = None,
    region: str | None = None,
    legendary: bool = False,
    mythical: bool = False,
) -> PokemonData:
    """A form whose line is ``line`` (earlier stages) plus itself.

    Without ``steps``, consecutive stages evolve by level; without ``stages``, they are
    plain stages. Without ``chain``, the line gets its own chain, derived from its first
    stage. ``egg_groups`` are those of the whole line.
    """
    slugs = (*line, slug)
    if stages is None:
        stages = [stage(s) for s in slugs]
    if steps is None:
        steps = [step(a, b, minimum_level=16) for a, b in pairwise(slugs)]
    return PokemonData(
        slug=slug,
        species=species or slug,
        dex_number=dex_number,
        name=slug.capitalize(),
        generation=generation,
        types=tuple(types),
        evolution_chain=chain if chain is not None else zlib.crc32(slugs[0].encode()),
        stages=tuple(stages),
        line_egg_groups=frozenset(egg_groups),
        evolution_steps=tuple(steps),
        region=region,
        is_legendary=legendary,
        is_mythical=mythical,
    )


def candidate(data: PokemonData, *, exists: bool = True, can_arrive: bool = True) -> Candidate:
    return Candidate(data, Availability(exists_in_game=exists, can_arrive=can_arrive))


def pool_entry(
    data: PokemonData, *, exists: bool = True, can_arrive: bool = True, verified: bool = True
) -> PoolEntry:
    return PoolEntry(data, Availability(exists, can_arrive), verified)


def battle(
    slug: str, *rivals: tuple[str, Sequence[str]], category: str = "gym_leader"
) -> KeyBattle:
    return KeyBattle(
        slug=slug,
        category=category,
        trainer=slug.capitalize(),
        rivals=tuple(Rival(name, tuple(types)) for name, types in rivals),
    )


def context(
    favorites: Sequence[Candidate] = (),
    *,
    pool: Sequence[PoolEntry] = (),
    key_battles: Sequence[KeyBattle] = (),
    chart: TypeChart | None = None,
    game: GameInfo | None = None,
    settings: RuleSettings | None = None,
    journey: Sequence[HallOfFameEntry] = (),
) -> GameContext:
    chart = chart or type_chart()
    return GameContext(
        game=game or GameInfo("firered", chart.generation),
        type_chart=chart,
        favorites=tuple(favorites),
        pool=tuple(pool),
        key_battles=tuple(key_battles),
        settings=settings or RuleSettings.defaults(),
        evolution_methods=EVOLUTION_METHODS,
        journey=tuple(journey),
    )


def completed(game: str, generation: int, sequence: int, *members: PokemonData) -> HallOfFameEntry:
    """A Hall of Fame entry whose team is ``members``."""
    return HallOfFameEntry(
        game=game,
        generation=generation,
        sequence=sequence,
        members=tuple(JourneyMember(m.slug, m.evolution_chain, m.region) for m in members),
    )
