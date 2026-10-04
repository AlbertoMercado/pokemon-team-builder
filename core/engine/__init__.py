"""Team generation engine: ``generate(ctx)`` (docs/02-ddt/algoritmo-generacion.md).

1. Filter the favourites with the candidate rules (RN-03, RN-11, RN-16).
2. Resolve the presence rules (RN-13, RN-14) to the first level that can be met. A level
   that needs a Pokémon that is not a favourite reserves a slot (RN-08).
3. Search the teams with the most favourites possible, up to 6 minus the reserved slots,
   without conflicts between members (RN-07, RN-12, RN-14) and meeting the presence rules,
   which come before the size of the team (CA-19).
4. Keep every team with the highest score, after the RN-19 tie-break (RN-04), and group the
   tied teams that only differ in interchangeable members (CA-33).
5. If the teams are not of 6, suggest Pokémon that are not favourites for their open slots
   (RN-08).

If no team can meet every presence rule at once, RN-13 comes first: RN-14 goes to its next
level, which reserves a slot for the evolutions of Eevee that are not favourites (CA-48).
"""

import dataclasses
from collections.abc import Sequence
from functools import partial

from core.domain import GameContext, PokemonData, PoolEntry
from core.engine import search
from core.engine.grouping import group_teams
from core.engine.result import (
    GenerationResult,
    GenerationStatus,
    IncompleteReason,
    OpenSlots,
    RankedTeam,
    Suggestion,
    TeamGroup,
)
from core.engine.suggestions import Suggester
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
    "OpenSlots",
    "RankedTeam",
    "Suggestion",
    "TeamGroup",
    "generate",
    "presence_requirements",
    "suggestible_entries",
]


def suggestible_entries(ctx: GameContext) -> list[PoolEntry]:
    """Pokémon of the game that are not favourites and pass the candidate filters (CA-40),
    in canonical order."""
    entries = sorted(ctx.pool, key=lambda e: (e.pokemon.dex_number, e.pokemon.slug))
    return [e for e in entries if first_exclusion(e.pokemon, e.availability, ctx) is None]


def presence_requirements(
    ctx: GameContext, valid: Sequence[PokemonData]
) -> tuple[PresenceRequirement, ...]:
    """The level of each active presence rule (RN-13, RN-14), in catalogue order."""
    suggestible = [e.pokemon for e in suggestible_entries(ctx)]
    return tuple(
        rule.requirement(valid, suggestible)
        for rule in PRESENCE_RULES
        if ctx.settings.is_enabled(rule.rule_id)
    )


def displace(
    requirement: PresenceRequirement, by: PresenceRequirement, ctx: GameContext
) -> PresenceRequirement:
    """``requirement`` at its next level, because its candidates never fit with ``by``'s.

    The rule is resolved again as if no favourite met it (CA-48).
    """
    [rule] = [r for r in PRESENCE_RULES if r.rule_id == requirement.rule_id]
    suggestible = [e.pokemon for e in suggestible_entries(ctx)]
    lower = rule.requirement((), suggestible)
    reason = (
        f"Sus candidatos ({', '.join(requirement.options)}) no caben en ningún equipo junto "
        f"con {by.rule_id}, que tiene prioridad"
    )
    return dataclasses.replace(lower, detail=f"{reason}. {lower.detail}")


def _conflicts(constraints: tuple[PairConstraint, ...], a: PokemonData, b: PokemonData) -> bool:
    return conflict(a, b, constraints) is not None


def _largest_best_teams(
    valid: Sequence[PokemonData],
    presence: Sequence[PresenceRequirement],
    constraints: tuple[PairConstraint, ...],
    scorer: Scorer,
) -> list[tuple[PokemonData, ...]]:
    """The best teams of the largest size that meets the presence rules (RN-08, CA-19).

    Empty if no team meets every presence rule at once.
    """
    reserved = sum(1 for p in presence if p.status is PresenceStatus.RESERVED)
    required = [frozenset(p.options) for p in presence if p.status is PresenceStatus.CANDIDATES]
    for size in range(TEAM_SIZE - reserved, len(required) - 1, -1):
        if size == 0:
            return [()]
        found = search.teams(valid, size, partial(_conflicts, constraints), required)
        _, winners = search.best_teams(found, scorer.ranking_key)
        if winners:
            return winners
    return []


def generate(ctx: GameContext) -> GenerationResult:
    """Generate the best teams of favourites for the context's game."""
    candidates, discards = valid_candidates(ctx)
    valid = [c.pokemon for c in candidates]  # already in canonical order
    presence = list(presence_requirements(ctx, valid))
    constraints = active_pair_constraints(ctx.settings)
    scorer = Scorer(ctx)

    winners = _largest_best_teams(valid, presence, constraints, scorer)
    while not winners:
        # The presence rules cannot be met together: the last one gives way (CA-48).
        required = [i for i, p in enumerate(presence) if p.status is PresenceStatus.CANDIDATES]
        last = required[-1]
        presence[last] = displace(presence[last], presence[required[0]], ctx)
        winners = _largest_best_teams(valid, presence, constraints, scorer)

    reserved = [p for p in presence if p.status is PresenceStatus.RESERVED]
    suggester = Suggester(suggestible_entries(ctx), constraints, scorer)
    teams = []
    for team in winners:
        free = TEAM_SIZE - len(reserved) - len(team)
        slots = suggester.open_slots(team, reserved, free)
        teams.append(RankedTeam(team, scorer.score(team), slots))

    reason = None
    if reserved:
        reason = IncompleteReason.RESERVED_SLOT
    elif len(valid) < TEAM_SIZE:
        reason = IncompleteReason.NOT_ENOUGH_CANDIDATES
    elif len(winners[0]) < TEAM_SIZE:
        reason = IncompleteReason.NO_VALID_TEAM
    return GenerationResult(
        GenerationStatus.INCOMPLETE if reason else GenerationStatus.COMPLETE,
        tuple(teams),
        group_teams(teams),
        tuple(discards),
        tuple(presence),
        tuple(p.slug for p in valid),
        reason,
    )
