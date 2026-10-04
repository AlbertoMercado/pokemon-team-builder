"""Team generation engine: ``generate(ctx)`` (docs/02-ddt/algoritmo-generacion.md).

1. Filter the favourites with the candidate rules (RN-03, RN-11, RN-16).
2. Resolve the presence rules (RN-13, RN-14) to the first level that can be met.
3. Search every team of 6 without conflicts between members (RN-07, RN-12, RN-14) that
   meets the presence rules.
4. Keep every team with the highest score, after the RN-19 tie-break (RN-04).

Teams have exactly 6 members (RN-01), all of them favourites (RN-02). When that is not
possible the result is incomplete (RN-08).
"""

from functools import partial

from core.domain import GameContext, PokemonData
from core.engine import search
from core.engine.result import (
    GenerationResult,
    GenerationStatus,
    IncompleteReason,
    RankedTeam,
)
from core.rules.candidate import first_exclusion, valid_candidates
from core.rules.team import (
    PRESENCE_RULES,
    PairConstraint,
    PresenceRequirement,
    PresenceStatus,
    active_pair_constraints,
    conflict,
)
from core.scoring import Scorer

TEAM_SIZE = 6

__all__ = [
    "TEAM_SIZE",
    "GenerationResult",
    "GenerationStatus",
    "IncompleteReason",
    "RankedTeam",
    "generate",
    "presence_requirements",
]


def _suggestible(ctx: GameContext) -> list[PokemonData]:
    """Pokémon of the game that are not favourites and pass the candidate filters (CA-40)."""
    entries = sorted(ctx.pool, key=lambda e: (e.pokemon.dex_number, e.pokemon.slug))
    return [e.pokemon for e in entries if first_exclusion(e.pokemon, e.availability, ctx) is None]


def presence_requirements(
    ctx: GameContext, valid: list[PokemonData]
) -> tuple[PresenceRequirement, ...]:
    """The level of each active presence rule (RN-13, RN-14)."""
    suggestible = _suggestible(ctx)
    return tuple(
        rule.requirement(valid, suggestible)
        for rule in PRESENCE_RULES
        if ctx.settings.is_enabled(rule.rule_id)
    )


def _conflicts(constraints: tuple[PairConstraint, ...], a: PokemonData, b: PokemonData) -> bool:
    return conflict(a, b, constraints) is not None


def generate(ctx: GameContext) -> GenerationResult:
    """Generate the best teams of 6 favourites for the context's game."""
    candidates, discards = valid_candidates(ctx)
    valid = [c.pokemon for c in candidates]  # already in canonical order
    presence = presence_requirements(ctx, valid)

    def incomplete(reason: IncompleteReason) -> GenerationResult:
        return GenerationResult(
            GenerationStatus.INCOMPLETE,
            (),
            tuple(discards),
            presence,
            tuple(p.slug for p in valid),
            reason,
        )

    if any(p.status is PresenceStatus.RESERVED for p in presence):
        return incomplete(IncompleteReason.RESERVED_SLOT)
    if len(valid) < TEAM_SIZE:
        return incomplete(IncompleteReason.NOT_ENOUGH_CANDIDATES)

    required = [frozenset(p.options) for p in presence if p.status is PresenceStatus.CANDIDATES]
    constraints = active_pair_constraints(ctx.settings)
    found = search.teams(valid, TEAM_SIZE, partial(_conflicts, constraints), required)
    scorer = Scorer(ctx)
    _, winners = search.best_teams(found, scorer.ranking_key)
    if not winners:
        return incomplete(IncompleteReason.NO_VALID_TEAM)
    return GenerationResult(
        GenerationStatus.COMPLETE,
        tuple(RankedTeam(team, scorer.score(team)) for team in winners),
        tuple(discards),
        presence,
        tuple(p.slug for p in valid),
    )
