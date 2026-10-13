"""Evolution difficulty: tedious (RN-15), random (RN-20) or impossible in the target game.

Steps keep PokeAPI's trigger and conditions as loaded (docs/02-ddt/modelo-datos.md); the
catalog of evolution methods (``core.domain.evolution``, curated data) says why each one is
tedious, random or impossible without a mechanic of the game. A step whose trigger and
conditions are all easy is easy.

When a pair of stages has several alternative methods, the player chooses the easiest one:
the pair is tedious only if every alternative is.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import groupby

from core import breeding
from core.domain import EvolutionCatalog, EvolutionStep, GameInfo, PokemonData, Tedium

__all__ = ["EvolutionAssessment", "Tedium", "assess", "step_tedium"]


def step_tedium(
    step: EvolutionStep, game: GameInfo, catalog: EvolutionCatalog
) -> frozenset[Tedium]:
    """Why ``step`` is tedious in ``game``; empty if it is easy.

    ``EvolutionCatalogError`` if its trigger or a condition is not in ``catalog``.
    """
    methods = [catalog.trigger(step.trigger), *(catalog.condition(n) for n, _ in step.conditions)]
    reasons: set[Tedium] = set()
    for method in methods:
        if method.unless_learnt_by_level and step.move_learnt_by_level:
            continue  # CA-32: it learns the move by level, so it knows it when it evolves
        if method.tedium is not None:
            reasons.add(method.tedium)
        if method.requires_mechanic is not None and not game.has(method.requires_mechanic):
            reasons.add(Tedium.IMPOSSIBLE)
    return frozenset(reasons)


def _easiest(
    alternatives: Iterable[EvolutionStep], game: GameInfo, catalog: EvolutionCatalog
) -> frozenset[Tedium]:
    """Reasons of the easiest alternative: fewest reasons, a random one only as last resort."""
    return min(
        (step_tedium(step, game, catalog) for step in alternatives),
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


def assess(pokemon: PokemonData, game: GameInfo, catalog: EvolutionCatalog) -> EvolutionAssessment:
    """Assess every step from the stage that hatches up to ``pokemon`` (CA-25)."""
    order = {stage.pokemon: index for index, stage in enumerate(pokemon.stages)}
    steps = sorted(breeding.steps_from_egg(pokemon), key=lambda s: order[s.from_pokemon])
    tedious: list[tuple[str, str, frozenset[Tedium]]] = []
    for (origin, evolved), alternatives in groupby(
        steps, key=lambda s: (s.from_pokemon, s.to_pokemon)
    ):
        reasons = _easiest(alternatives, game, catalog)
        if reasons:
            tedious.append((origin, evolved, reasons))
    return EvolutionAssessment(pokemon.slug, tuple(tedious))
