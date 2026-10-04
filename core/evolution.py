"""Evolution difficulty: tedious (RN-15), random (RN-20) or impossible in the target game.

Steps keep PokeAPI's trigger and conditions as loaded (docs/02-ddt/modelo-datos.md); this
module turns them into the reasons why a step is tedious. A step with no reason is easy:
level, friendship or affection, a stone or another item, or a held item on its own.
Anything this module does not know is tedious, so a new PokeAPI condition never makes a
hard evolution look easy.

When a pair of stages has several alternative methods, the player chooses the easiest one:
the pair is tedious only if every alternative is.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from itertools import groupby

from core import breeding
from core.domain import CONTESTS, DAY_NIGHT_CYCLE, EvolutionStep, GameInfo, PokemonData


class Tedium(StrEnum):
    """Why an evolution step is tedious (RN-15, CA-20, CA-35)."""

    TRADE = "trade"  # trade, with or without an item or a given Pokémon
    SHED = "shed"  # Nincada → Shedinja: a free slot and a Poké Ball
    RANDOM = "random"  # the result cannot be chosen (Wurmple); also RN-20
    STATS = "stats"  # comparing Attack and Defense (Tyrogue)
    TIME_OF_DAY = "time_of_day"  # day or night (Eevee → Espeon)
    BEAUTY = "beauty"  # a contest condition (Feebas → Milotic)
    LOCATION = "location"  # level up in a given place or region (Magneton → Magnezone)
    PARTY = "party"  # a given Pokémon or type in the party (Mantyke → Mantine)
    MOVE = "move"  # knowing a move or a move type
    OTHER = "other"  # any other unusual requirement or an unknown trigger or condition
    IMPOSSIBLE = "impossible"  # the game lacks the mechanic: evolve it in another game


# Triggers that are easy unless a condition says otherwise.
EASY_TRIGGERS = frozenset({"level-up", "use-item"})
TRIGGER_TEDIUM = {"trade": Tedium.TRADE, "shed": Tedium.SHED}

# Conditions that never make a step tedious.
EASY_CONDITIONS = frozenset(
    {"minimum_level", "minimum_happiness", "minimum_affection", "trigger_item", "held_item"}
)
CONDITION_TEDIUM = {
    "percentage_chance": Tedium.RANDOM,
    "condition_expression": Tedium.RANDOM,
    "relative_physical_stats": Tedium.STATS,
    "time_of_day": Tedium.TIME_OF_DAY,
    "minimum_beauty": Tedium.BEAUTY,
    "location": Tedium.LOCATION,
    "region": Tedium.LOCATION,
    "party_species": Tedium.PARTY,
    "party_type": Tedium.PARTY,
    # Without the moves learnt by level (``level_move``, not loaded yet) a required move is
    # assumed not to be learnt by level (CA-32). No evolution up to the 3rd generation
    # needs one.
    "known_move": Tedium.MOVE,
    "known_move_type": Tedium.MOVE,
    # Part of a trade: the trade already makes it tedious.
    "trade_species": Tedium.TRADE,
}
# Conditions that need a mechanic the target game may not have.
REQUIRED_MECHANIC = {"time_of_day": DAY_NIGHT_CYCLE, "minimum_beauty": CONTESTS}


def step_tedium(step: EvolutionStep, game: GameInfo) -> frozenset[Tedium]:
    """Why ``step`` is tedious in ``game``; empty if it is easy."""
    reasons: set[Tedium] = set()
    if step.trigger in TRIGGER_TEDIUM:
        reasons.add(TRIGGER_TEDIUM[step.trigger])
    elif step.trigger not in EASY_TRIGGERS:
        reasons.add(Tedium.OTHER)
    for name, _ in step.conditions:
        if name in EASY_CONDITIONS:
            continue
        reasons.add(CONDITION_TEDIUM.get(name, Tedium.OTHER))
        mechanic = REQUIRED_MECHANIC.get(name)
        if mechanic is not None and not game.has(mechanic):
            reasons.add(Tedium.IMPOSSIBLE)
    return frozenset(reasons)


def _easiest(alternatives: Iterable[EvolutionStep], game: GameInfo) -> frozenset[Tedium]:
    """Reasons of the easiest alternative: fewest reasons, a random one only as last resort."""
    return min(
        (step_tedium(step, game) for step in alternatives),
        key=lambda reasons: (Tedium.RANDOM in reasons, len(reasons), sorted(reasons)),
    )


@dataclass(frozen=True)
class EvolutionAssessment:
    """How hard it is to reach a favourite from the stage that hatches (RN-15, RN-20).

    ``tedious_steps`` maps each tedious pair of stages to its reasons, in line order.
    """

    pokemon: str
    tedious_steps: tuple[tuple[str, str, frozenset[Tedium]], ...]

    @property
    def is_tedious(self) -> bool:
        """Some step needs a tedious evolution (RN-15)."""
        return bool(self.tedious_steps)

    @property
    def is_random(self) -> bool:
        """Some step has a result the player cannot choose (RN-20)."""
        return any(Tedium.RANDOM in reasons for _, _, reasons in self.tedious_steps)


def assess(pokemon: PokemonData, game: GameInfo) -> EvolutionAssessment:
    """Assess every step from the stage that hatches up to ``pokemon`` (CA-25)."""
    order = {stage.pokemon: index for index, stage in enumerate(pokemon.stages)}
    steps = sorted(breeding.steps_from_egg(pokemon), key=lambda s: order[s.from_pokemon])
    tedious: list[tuple[str, str, frozenset[Tedium]]] = []
    for (origin, evolved), alternatives in groupby(
        steps, key=lambda s: (s.from_pokemon, s.to_pokemon)
    ):
        reasons = _easiest(alternatives, game)
        if reasons:
            tedious.append((origin, evolved, reasons))
    return EvolutionAssessment(pokemon.slug, tuple(tedious))
