"""Readable constructors of engine data for the core tests.

They fill in sensible defaults so each test only states what matters to it, e.g.
``pokemon("gengar", ("ghost", "poison"), line=("gastly", "haunter"), steps=[...])``.
"""

from collections.abc import Iterable, Mapping, Sequence
from itertools import pairwise

from core.domain import (
    Availability,
    Candidate,
    ConditionValue,
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


def stage(
    slug: str,
    egg_groups: Iterable[str] = ("monster",),
    *,
    is_baby: bool = False,
    requires_incense: bool = False,
) -> Stage:
    return Stage(slug, slug, frozenset(egg_groups), is_baby, requires_incense)


def pokemon(
    slug: str,
    types: Sequence[str] = ("normal",),
    *,
    line: Sequence[str] = (),
    steps: Sequence[EvolutionStep] | None = None,
    stages: Sequence[Stage] | None = None,
    dex_number: int = 1,
    chain: int = 1,
    species: str | None = None,
    region: str | None = None,
    legendary: bool = False,
    mythical: bool = False,
) -> PokemonData:
    """A form whose line is ``line`` (earlier stages) plus itself.

    Without ``steps``, consecutive stages evolve by level; without ``stages``, every stage
    is in the monster egg group.
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
        types=tuple(types),
        evolution_chain=chain,
        stages=tuple(stages),
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
    journey_exclusions: Iterable[str] = (),
) -> GameContext:
    chart = chart or type_chart()
    return GameContext(
        game=game or GameInfo("firered", chart.generation),
        type_chart=chart,
        favorites=tuple(favorites),
        pool=tuple(pool),
        key_battles=tuple(key_battles),
        settings=settings or RuleSettings.defaults(),
        journey_exclusions=frozenset(journey_exclusions),
    )
