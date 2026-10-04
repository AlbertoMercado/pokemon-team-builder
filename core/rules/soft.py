"""Soft rules: RN-06, RN-15, RN-17 and RN-20, each scoring a team between 0 and 1.

``core.scoring`` multiplies each score by the rule's weight (RN-04). The score is not additive
per member (RN-17 depends on the combination), but everything a rule needs from each member
is computed once, in its ``MemberProfile`` (docs/02-ddt/algoritmo-generacion.md): the search
scores many teams from the same candidates. A team may have fewer than 6 members (RN-08).
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import lcm
from types import MappingProxyType
from typing import Protocol

from core import evolution
from core.domain import GameContext, KeyBattle, PokemonData, Rival, TypeChart

SUPER_EFFECTIVE = Fraction(2)
RESISTED = Fraction(1, 2)


@dataclass(frozen=True)
class Rivals:
    """Every rival Pokémon of the key battles, one bit each, and the bits of each battle.

    A Pokémon that appears in several battles has one bit per appearance, so each battle
    keeps its own rivals (RN-17). ``battle_factors`` and ``denominator`` let RN-17 add the
    battles with integers: a battle with ``n`` rivals counts its covered aspects times
    ``denominator / (2n)``, and the sum is divided by ``denominator`` and the battles once.
    """

    rivals: tuple[Rival, ...]
    battle_masks: tuple[int, ...]
    battle_factors: tuple[int, ...]
    denominator: int

    @classmethod
    def of(cls, battles: Iterable[KeyBattle]) -> "Rivals":
        rivals: list[Rival] = []
        masks: list[int] = []
        for battle in battles:
            first = len(rivals)
            rivals.extend(battle.rivals)
            masks.append(((1 << len(battle.rivals)) - 1) << first)
        denominator = lcm(*(2 * mask.bit_count() for mask in masks))
        factors = tuple(denominator // (2 * mask.bit_count()) for mask in masks)
        return cls(tuple(rivals), tuple(masks), factors, denominator)


def _attacks(pokemon: PokemonData, rival: Rival, chart: TypeChart) -> bool:
    """A type of ``pokemon`` is super effective (x2 or more) against the rival."""
    return any(chart.factor(t, rival.types) >= SUPER_EFFECTIVE for t in pokemon.types)


def _defends(pokemon: PokemonData, rival: Rival, chart: TypeChart) -> bool:
    """``pokemon`` resists (x0.5 or less) a type of the rival and is weak to none."""
    factors = [chart.factor(t, pokemon.types) for t in rival.types]
    return min(factors) <= RESISTED and max(factors) < SUPER_EFFECTIVE


@dataclass(frozen=True)
class MemberProfile:
    """What the soft rules need from one member, computed once per candidate.

    ``attack`` and ``defense`` are bit sets over ``Rivals.rivals``: the rivals this member
    covers in attack and in defense (RN-17).
    """

    pokemon: PokemonData
    tedious: bool
    random: bool
    attack: int
    defense: int


def member_profile(pokemon: PokemonData, ctx: GameContext, rivals: Rivals) -> MemberProfile:
    assessment = evolution.assess(pokemon, ctx.game)
    chart = ctx.type_chart
    attack = defense = 0
    for bit, rival in enumerate(rivals.rivals):
        if _attacks(pokemon, rival, chart):
            attack |= 1 << bit
        if _defends(pokemon, rival, chart):
            defense |= 1 << bit
    return MemberProfile(pokemon, assessment.is_tedious, assessment.is_random, attack, defense)


@dataclass(frozen=True)
class SoftScore:
    """A rule's score for a team, between 0 and 1, and the members that count against it."""

    value: Fraction
    penalized: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 1:
            raise ValueError(f"puntuación fuera de 0 a 1: {self.value}")


class SoftRule(Protocol):
    """A soft rule of the catalogue, scoring a team from its members' profiles."""

    @property
    def rule_id(self) -> str: ...

    def score(self, team: Sequence[MemberProfile], rivals: Rivals) -> SoftScore: ...


class SameSpeciesRule:
    """RN-06: 1 if no two members are forms of the same species, 0 otherwise."""

    rule_id = "RN-06"

    def score(self, team: Sequence[MemberProfile], rivals: Rivals) -> SoftScore:
        counts = Counter(m.pokemon.species for m in team)
        penalized = tuple(m.pokemon.slug for m in team if counts[m.pokemon.species] > 1)
        return SoftScore(Fraction(0 if penalized else 1), penalized)


class TediousEvolutionRule:
    """RN-15: 1 - (members with a tedious evolution / members of the team).

    An empty team scores 1: nobody needs a tedious evolution.
    """

    rule_id = "RN-15"

    def score(self, team: Sequence[MemberProfile], rivals: Rivals) -> SoftScore:
        penalized = tuple(m.pokemon.slug for m in team if m.tedious)
        if not team:
            return SoftScore(Fraction(1))
        return SoftScore(1 - Fraction(len(penalized), len(team)), penalized)


class RandomEvolutionRule:
    """RN-20: 1 if no member needs a random evolution, 0 otherwise."""

    rule_id = "RN-20"

    def score(self, team: Sequence[MemberProfile], rivals: Rivals) -> SoftScore:
        penalized = tuple(m.pokemon.slug for m in team if m.random)
        return SoftScore(Fraction(0 if penalized else 1), penalized)


class KeyBattleCoverageRule:
    """RN-17: types effective against the key battles.

    Each rival scores the mean of attack and defense (0, 1/2 or 1, CA-24); each battle, the
    mean of its rivals; the rule, the mean of the battles. Only the types of the members and
    the rivals count, with the game's type chart (RN-10). Without key battles the rule cannot
    reward anything and scores 0 (CA-46 rules that case out at load time).
    """

    rule_id = "RN-17"

    def score(self, team: Sequence[MemberProfile], rivals: Rivals) -> SoftScore:
        if not rivals.battle_masks:
            return SoftScore(Fraction(0))
        attack = defense = 0
        for member in team:
            attack |= member.attack
            defense |= member.defense
        covered = sum(
            ((attack & mask).bit_count() + (defense & mask).bit_count()) * factor
            for mask, factor in zip(rivals.battle_masks, rivals.battle_factors, strict=True)
        )
        return SoftScore(Fraction(covered, rivals.denominator * len(rivals.battle_masks)))


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
