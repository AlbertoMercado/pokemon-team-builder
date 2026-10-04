"""Weighted score of a team (RN-04), its breakdown per rule (RF-09) and the tie-break (RN-19).

``P(team) = Σ weight(r) · s(r, team)`` for every active soft rule ``r``, with exact
fractions (ADR-0006), so equal scores are really equal and ties are found exactly.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction

from core.domain import GameContext, PokemonData
from core.rules.soft import SOFT_RULES


@dataclass(frozen=True)
class RuleContribution:
    """What one soft rule adds to the team's score: ``weight · score`` (RF-09)."""

    rule_id: str
    weight: int
    score: Fraction
    penalized: tuple[str, ...] = ()

    @property
    def contribution(self) -> Fraction:
        return self.weight * self.score


@dataclass(frozen=True)
class TeamScore:
    """The team's total score, its breakdown and how many members have two types."""

    breakdown: tuple[RuleContribution, ...]
    dual_types: int

    @property
    def total(self) -> Fraction:
        """The sum of the contributions, so the breakdown always adds up (RF-09)."""
        return sum((rule.contribution for rule in self.breakdown), Fraction(0))

    @property
    def ranking_key(self) -> tuple[Fraction, int]:
        """Higher is better: score first, then members with two types (RN-19)."""
        return self.total, self.dual_types


def canonical_team(team: Iterable[PokemonData]) -> tuple[PokemonData, ...]:
    """Members in canonical order: National Pokédex number, then form (RF-08)."""
    return tuple(sorted(team, key=lambda p: (p.dex_number, p.slug)))


def score_team(team: Iterable[PokemonData], ctx: GameContext) -> TeamScore:
    """Score ``team`` with the active soft rules, in catalogue order."""
    members = canonical_team(team)
    settings = ctx.settings
    breakdown = []
    for rule_id in settings.active_soft_rules():
        result = SOFT_RULES[rule_id].score(members, ctx)
        breakdown.append(
            RuleContribution(rule_id, settings.weight(rule_id), result.value, result.penalized)
        )
    return TeamScore(tuple(breakdown), sum(1 for m in members if m.is_dual_type))
