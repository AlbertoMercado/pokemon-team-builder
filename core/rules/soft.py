"""Soft rules: RN-06, RN-15, RN-17 and RN-20, each scoring a team between 0 and 1.

``core.scoring`` multiplies each score by the rule's weight (RN-04). A team is the members
as ``PokemonData``, in canonical order; it may have fewer than 6 (RN-08).
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Protocol

from core import evolution
from core.domain import GameContext, KeyBattle, PokemonData, Rival, TypeChart

SUPER_EFFECTIVE = Fraction(2)
RESISTED = Fraction(1, 2)


@dataclass(frozen=True)
class SoftScore:
    """A rule's score for a team, between 0 and 1, and the members that count against it."""

    value: Fraction
    penalized: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 1:
            raise ValueError(f"puntuación fuera de 0 a 1: {self.value}")


class SoftRule(Protocol):
    """A soft rule of the catalogue."""

    @property
    def rule_id(self) -> str: ...

    def score(self, team: Sequence[PokemonData], ctx: GameContext) -> SoftScore: ...


class SameSpeciesRule:
    """RN-06: 1 if no two members are forms of the same species, 0 otherwise."""

    rule_id = "RN-06"

    def score(self, team: Sequence[PokemonData], ctx: GameContext) -> SoftScore:
        counts = Counter(member.species for member in team)
        penalized = tuple(m.slug for m in team if counts[m.species] > 1)
        return SoftScore(Fraction(0 if penalized else 1), penalized)


class TediousEvolutionRule:
    """RN-15: 1 - (members with a tedious evolution / members of the team).

    An empty team scores 1: nobody needs a tedious evolution.
    """

    rule_id = "RN-15"

    def score(self, team: Sequence[PokemonData], ctx: GameContext) -> SoftScore:
        penalized = tuple(m.slug for m in team if evolution.assess(m, ctx.game).is_tedious)
        if not team:
            return SoftScore(Fraction(1))
        return SoftScore(1 - Fraction(len(penalized), len(team)), penalized)


class RandomEvolutionRule:
    """RN-20: 1 if no member needs a random evolution, 0 otherwise."""

    rule_id = "RN-20"

    def score(self, team: Sequence[PokemonData], ctx: GameContext) -> SoftScore:
        penalized = tuple(m.slug for m in team if evolution.assess(m, ctx.game).is_random)
        return SoftScore(Fraction(0 if penalized else 1), penalized)


def _attack(team: Sequence[PokemonData], rival: Rival, chart: TypeChart) -> bool:
    """Some member has a type that is super effective (x2 or more) against the rival."""
    return any(
        chart.factor(type_name, rival.types) >= SUPER_EFFECTIVE
        for member in team
        for type_name in member.types
    )


def _defense(team: Sequence[PokemonData], rival: Rival, chart: TypeChart) -> bool:
    """Some member resists (x0.5 or less) a type of the rival and is weak to none."""
    for member in team:
        factors = [chart.factor(type_name, member.types) for type_name in rival.types]
        if min(factors) <= RESISTED and max(factors) < SUPER_EFFECTIVE:
            return True
    return False


def rival_score(team: Sequence[PokemonData], rival: Rival, chart: TypeChart) -> Fraction:
    """Mean of attack and defense against one rival Pokémon: 0, 1/2 or 1 (CA-24)."""
    return Fraction(int(_attack(team, rival, chart)) + int(_defense(team, rival, chart)), 2)


def battle_score(team: Sequence[PokemonData], battle: KeyBattle, chart: TypeChart) -> Fraction:
    """Mean of the battle's rivals."""
    total = sum((rival_score(team, rival, chart) for rival in battle.rivals), Fraction(0))
    return total / len(battle.rivals)


class KeyBattleCoverageRule:
    """RN-17: types effective against the key battles, the mean of every battle.

    Only the types of the members and the rivals count, with the game's type chart (RN-10).
    Without key battles the rule cannot reward anything and scores 0.
    """

    rule_id = "RN-17"

    def score(self, team: Sequence[PokemonData], ctx: GameContext) -> SoftScore:
        if not ctx.key_battles:
            return SoftScore(Fraction(0))
        chart = ctx.type_chart
        total = sum((battle_score(team, b, chart) for b in ctx.key_battles), Fraction(0))
        return SoftScore(total / len(ctx.key_battles))


SOFT_RULES: Mapping[str, SoftRule] = MappingProxyType(
    {
        rule.rule_id: rule
        for rule in (
            SameSpeciesRule(),
            TediousEvolutionRule(),
            KeyBattleCoverageRule(),
            RandomEvolutionRule(),
        )
    }
)
