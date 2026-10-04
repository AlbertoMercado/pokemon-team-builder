"""Weighted score of a team (RN-04), its breakdown per rule (RF-09) and the tie-break (RN-19).

``P(team) = Σ weight(r) · s(r, team)`` for every active soft rule ``r``, with exact
fractions (ADR-0006), so equal scores are really equal and ties are found exactly.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction

from core.domain import GameContext, PokemonData
from core.rules.soft import SOFT_RULES, MemberProfile, Rivals, member_profile


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


class Scorer:
    """Scores teams of one context, computing each member's profile only once.

    The engine scores many teams built from the same candidates; ``ranking_key`` skips the
    breakdown, and ``score`` builds it for the teams that are shown.
    """

    def __init__(self, ctx: GameContext) -> None:
        settings = ctx.settings
        self._ctx = ctx
        self._rivals = Rivals.of(ctx.key_battles)
        self._rules = tuple(
            (SOFT_RULES[rule_id], settings.weight(rule_id))
            for rule_id in settings.active_soft_rules()
        )
        self._profiles: dict[str, MemberProfile] = {}

    def profile(self, pokemon: PokemonData) -> MemberProfile:
        cached = self._profiles.get(pokemon.slug)
        if cached is None or cached.pokemon != pokemon:
            cached = member_profile(pokemon, self._ctx, self._rivals)
            self._profiles[pokemon.slug] = cached
        return cached

    def _profiles_of(self, team: Iterable[PokemonData]) -> tuple[MemberProfile, ...]:
        return tuple(self.profile(member) for member in canonical_team(team))

    def ranking_key(self, team: Iterable[PokemonData]) -> tuple[Fraction, int]:
        """The same as ``score(team).ranking_key``, without building the breakdown."""
        profiles = self._profiles_of(team)
        total = sum(
            (weight * rule.score(profiles, self._rivals).value for rule, weight in self._rules),
            Fraction(0),
        )
        return total, sum(1 for p in profiles if p.pokemon.is_dual_type)

    def score(self, team: Iterable[PokemonData]) -> TeamScore:
        """Score ``team`` with the active soft rules, in catalogue order."""
        profiles = self._profiles_of(team)
        breakdown = []
        for rule, weight in self._rules:
            result = rule.score(profiles, self._rivals)
            breakdown.append(RuleContribution(rule.rule_id, weight, result.value, result.penalized))
        return TeamScore(tuple(breakdown), sum(1 for p in profiles if p.pokemon.is_dual_type))


def score_team(team: Iterable[PokemonData], ctx: GameContext) -> TeamScore:
    """Score one team; to score many teams of the same context, use a ``Scorer``."""
    return Scorer(ctx).score(team)
