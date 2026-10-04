"""Suggestions for the open slots of an incomplete team (RN-08, RF-10).

The suggestions are Pokémon of the game that are not favourites and pass the candidate filters
(CA-40). For each team they also have to fit with its members under the active constraints
between members. A slot reserved by a presence rule only admits the Pokémon that meet it.

They are ordered by what they would add to the team's score, then those with two types first
(RN-19), then in canonical order. Every one that fits is returned (CA-50); the interface
decides how many to show. Those with unconfirmed data are marked (CA-31).
"""

from collections.abc import Iterable, Sequence

from core.domain import PokemonData, PoolEntry
from core.engine.result import OpenSlots, Suggestion
from core.rules.team import PairConstraint, PresenceRequirement, conflict
from core.scoring import Scorer


def _fits(
    pokemon: PokemonData, team: Sequence[PokemonData], constraints: Sequence[PairConstraint]
) -> bool:
    return all(conflict(pokemon, member, constraints) is None for member in team)


def _order(suggestion: Suggestion) -> tuple[object, ...]:
    p = suggestion.pokemon
    return -suggestion.gain, not p.is_dual_type, p.dex_number, p.slug


class Suggester:
    """Suggests Pokémon for the open slots of the teams of one context."""

    def __init__(
        self,
        suggestible: Sequence[PoolEntry],
        constraints: Sequence[PairConstraint],
        scorer: Scorer,
    ) -> None:
        self._suggestible = tuple(suggestible)
        self._constraints = tuple(constraints)
        self._scorer = scorer

    def suggest(
        self, team: Sequence[PokemonData], entries: Iterable[PoolEntry]
    ) -> tuple[Suggestion, ...]:
        """The ``entries`` that fit with ``team``, best first."""
        base, _ = self._scorer.ranking_key(team)
        found = [
            Suggestion(
                e.pokemon, self._scorer.ranking_key((*team, e.pokemon))[0] - base, e.verified
            )
            for e in entries
            if _fits(e.pokemon, team, self._constraints)
        ]
        return tuple(sorted(found, key=_order))

    def open_slots(
        self, team: Sequence[PokemonData], reserved: Sequence[PresenceRequirement], free: int
    ) -> tuple[OpenSlots, ...]:
        """The reserved slots, one per presence rule, and then the free ones."""
        slots = [
            OpenSlots(
                1,
                requirement.rule_id,
                self.suggest(
                    team, (e for e in self._suggestible if e.pokemon.slug in requirement.options)
                ),
            )
            for requirement in reserved
        ]
        if free:
            slots.append(OpenSlots(free, None, self.suggest(team, self._suggestible)))
        return tuple(slots)
