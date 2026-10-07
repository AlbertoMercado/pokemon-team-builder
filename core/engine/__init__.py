"""Team generation engine: ``generate(ctx)`` (docs/02-ddt/algoritmo-generacion.md).

1. Filter the favourites with the candidate rules (RN-03, RN-11, RN-16).
2. Resolve the presence rules (RN-13, RN-14, RN-21) to the first level that can be met. A
   level that needs a Pokémon that is not a favourite reserves a slot (RN-08), except in
   RN-21, which chooses a starter of the game as a member (CA-65).
3. Search the teams with the most favourites possible, up to 6 minus the reserved slots,
   without conflicts between members (RN-07, RN-12, RN-14, RN-21) and meeting the presence
   rules, which come before the size of the team (CA-19).
4. Keep every team with the highest score, after the RN-19 tie-break (RN-04), and group the
   tied teams that only differ in interchangeable members (CA-33).
5. If the teams are not of 6, suggest Pokémon that are not favourites for their open slots
   (RN-08).

The presence rules are met in catalogue order: RN-13, RN-14 and RN-21. One whose members fit
in no team with those of the rules before it gives way and goes to its next level (CA-48,
CA-61).
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
    PairConstraint,
    PresenceRequirement,
    PresenceStatus,
    active_pair_constraints,
    conflict,
    presence_rules,
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
    "resolved_presence",
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
    """The level of each active presence rule (RN-13, RN-14, RN-21), in catalogue order."""
    suggestible = [e.pokemon for e in suggestible_entries(ctx)]
    return tuple(
        rule.requirement(valid, suggestible)
        for rule in presence_rules(ctx.game)
        if ctx.settings.is_enabled(rule.rule_id)
    )


def displace(
    requirement: PresenceRequirement, by: Sequence[PresenceRequirement], ctx: GameContext
) -> PresenceRequirement:
    """``requirement`` at its next level, because its options never fit with ``by``'s.

    The rule is resolved again as if no favourite met it (CA-48) and, if that is already its
    level (RN-21 choosing a starter that is not a favourite), as if nothing in the game did.
    """
    [rule] = [r for r in presence_rules(ctx.game) if r.rule_id == requirement.rule_id]
    suggestible = [e.pokemon for e in suggestible_entries(ctx)]
    lower = rule.requirement((), suggestible)
    if lower.level <= requirement.level:
        lower = rule.requirement((), ())
    ids = [r.rule_id for r in by]
    priority = (
        f"{ids[0]}, que tiene prioridad"
        if len(ids) == 1
        else f"{', '.join(ids[:-1])} y {ids[-1]}, que tienen prioridad"
    )
    reason = (
        f"Sus opciones ({', '.join(requirement.options)}) no caben en ningún equipo junto "
        f"con {priority}"
    )
    return dataclasses.replace(lower, detail=f"{reason}. {lower.detail}")


def _conflicts(constraints: tuple[PairConstraint, ...], a: PokemonData, b: PokemonData) -> bool:
    return conflict(a, b, constraints) is not None


def _members(
    valid: Sequence[PokemonData],
    presence: Sequence[PresenceRequirement],
    suggestible: Sequence[PokemonData],
) -> list[PokemonData]:
    """Who can be in the team: the valid candidates and the Pokémon that a presence rule
    chooses although they are not favourites (CA-65), in canonical order."""
    chosen = {slug for p in presence if p.status is PresenceStatus.CHOSEN for slug in p.options}
    extra = [p for p in suggestible if p.slug in chosen]
    return sorted([*valid, *extra], key=lambda p: (p.dex_number, p.slug))


def _sizes(presence: Sequence[PresenceRequirement]) -> tuple[range, list[frozenset[str]]]:
    """The team sizes to try, largest first, and the sets the team must take one from."""
    reserved = sum(1 for p in presence if p.status is PresenceStatus.RESERVED)
    required = [frozenset(p.options) for p in presence if p.requires_member]
    return range(TEAM_SIZE - reserved, len(required) - 1, -1), required


def _largest_best_teams(
    members: Sequence[PokemonData],
    presence: Sequence[PresenceRequirement],
    constraints: tuple[PairConstraint, ...],
    scorer: Scorer,
) -> list[tuple[PokemonData, ...]]:
    """The best teams of the largest size that meets the presence rules (RN-08, CA-19).

    Empty if no team meets every presence rule at once.
    """
    sizes, required = _sizes(presence)
    for size in sizes:
        if size == 0:
            return [()]
        found = search.teams(members, size, partial(_conflicts, constraints), required)
        _, winners = search.best_teams(found, scorer.ranking_key)
        if winners:
            return winners
    return []


def _some_team(
    members: Sequence[PokemonData],
    presence: Sequence[PresenceRequirement],
    constraints: tuple[PairConstraint, ...],
) -> bool:
    """Whether some team of the sizes ``_largest_best_teams`` tries meets the presence rules.

    The search is lazy, so it stops at the first team, without scoring any.
    """
    sizes, required = _sizes(presence)
    for size in sizes:
        if size == 0:
            return True
        found = search.teams(members, size, partial(_conflicts, constraints), required)
        if next(found, None) is not None:
            return True
    return False


def _meet_presence(
    ctx: GameContext,
    valid: Sequence[PokemonData],
    constraints: tuple[PairConstraint, ...],
) -> list[PresenceRequirement]:
    """The presence rules at the level some team meets them together.

    They are added in catalogue order. While no team meets one together with the rules before
    it, it gives way and goes to its next level (CA-48, CA-61).
    """
    suggestible = [e.pokemon for e in suggestible_entries(ctx)]
    resolved: list[PresenceRequirement] = []
    for requirement in presence_requirements(ctx, valid):
        current = requirement
        while current.requires_member:
            trial = [*resolved, current]
            if _some_team(_members(valid, trial, suggestible), trial, constraints):
                break
            current = displace(current, [r for r in resolved if r.requires_member], ctx)
        resolved.append(current)
    return resolved


def resolved_presence(ctx: GameContext) -> tuple[PresenceRequirement, ...]:
    """The presence rules at the level ``generate`` resolves them, without generating.

    Only searches whether a team meets them, not the best teams, so it is much cheaper than
    ``generate(ctx).presence``. Used to check a team chosen by the user (``check_team``).
    """
    candidates, _ = valid_candidates(ctx)
    valid = [c.pokemon for c in candidates]
    return tuple(_meet_presence(ctx, valid, active_pair_constraints(ctx)))


def generate(ctx: GameContext) -> GenerationResult:
    """Generate the best teams of favourites for the context's game."""
    candidates, discards = valid_candidates(ctx)
    valid = [c.pokemon for c in candidates]  # already in canonical order
    constraints = active_pair_constraints(ctx)
    scorer = Scorer(ctx)
    presence = _meet_presence(ctx, valid, constraints)
    suggestible = suggestible_entries(ctx)
    members = _members(valid, presence, [e.pokemon for e in suggestible])
    winners = _largest_best_teams(members, presence, constraints, scorer)

    reserved = [p for p in presence if p.status is PresenceStatus.RESERVED]
    suggester = Suggester(suggestible, constraints, scorer)
    teams = []
    for team in winners:
        free = TEAM_SIZE - len(reserved) - len(team)
        slots = suggester.open_slots(team, reserved, free)
        teams.append(RankedTeam(team, scorer.score(team), slots))

    # A starter chosen by RN-21 adds one possible member, not all its options (CA-65).
    chosen = sum(1 for p in presence if p.status is PresenceStatus.CHOSEN)
    reason = None
    if reserved:
        reason = IncompleteReason.RESERVED_SLOT
    elif len(valid) + chosen < TEAM_SIZE:
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
