"""Filters per candidate: RN-03, RN-11 and RN-16, each with the reason of a discard (RF-10).

They apply in this order to the favourites, and the first that fails is the reason given.
Suggestions (RN-08) go through the same filters (CA-40).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from core import breeding, journey
from core.domain import Availability, Candidate, GameContext, PokemonData


class DiscardReason(StrEnum):
    GENERATION = "generation"  # RN-03, level 1: it appeared in a later generation
    GAME = "game"  # RN-03, level 2: it cannot be had in the target game
    ARRIVAL = "arrival"  # RN-03, level 3: it cannot arrive and evolve before the end (CA-28)
    BREEDING = "breeding"  # RN-11: its line cannot be bred
    JOURNEY = "journey"  # RN-16: already used in the journey


@dataclass(frozen=True)
class Discard:
    """Why a favourite is not a valid candidate.

    ``fact_key`` is the reviewable fact that decided it, when it was confirmed by the user
    (RN-18), so the result can say which confirmed data was used (RF-09).
    """

    pokemon: str
    rule_id: str
    reason: DiscardReason
    detail: str
    fact_key: str | None = None


class CandidateFilter(Protocol):
    """A hard rule applied to each candidate on its own."""

    @property
    def rule_id(self) -> str: ...

    def exclusion(
        self, pokemon: PokemonData, availability: Availability, ctx: GameContext
    ) -> Discard | None:
        """The discard if the rule excludes the Pokémon, or ``None`` if it passes."""
        ...


class AvailabilityFilter:
    """RN-03: from the target generation and game, and able to arrive in time."""

    rule_id = "RN-03"

    def exclusion(
        self, pokemon: PokemonData, availability: Availability, ctx: GameContext
    ) -> Discard | None:
        game = ctx.game
        if pokemon.generation > game.generation:
            return Discard(
                pokemon.slug,
                self.rule_id,
                DiscardReason.GENERATION,
                f"{pokemon.name} aparece en la {pokemon.generation}.ª generación y "
                f"{game.slug} es de la {game.generation}.ª",
            )
        if not availability.exists_in_game:
            return Discard(
                pokemon.slug,
                self.rule_id,
                DiscardReason.GAME,
                f"{pokemon.name} no se puede tener en {game.slug}",
                f"pokemon:{game.slug}:{pokemon.slug}:exists",
            )
        if not availability.can_arrive:
            return Discard(
                pokemon.slug,
                self.rule_id,
                DiscardReason.ARRIVAL,
                f"{pokemon.name} no puede llegar a {game.slug} y evolucionar antes de completarlo",
                f"pokemon:{game.slug}:{pokemon.slug}:arrival",
            )
        return None


class BreedingFilter:
    """RN-11: the line can be bred, because the team is bred in another game."""

    rule_id = "RN-11"

    def exclusion(
        self, pokemon: PokemonData, availability: Availability, ctx: GameContext
    ) -> Discard | None:
        if breeding.can_be_bred(pokemon):
            return None
        groups = ", ".join(sorted(pokemon.line_egg_groups))
        return Discard(
            pokemon.slug,
            self.rule_id,
            DiscardReason.BREEDING,
            f"{pokemon.name} no se puede criar (grupos huevo de su línea: {groups})",
        )


class JourneyFilter:
    """RN-16: not used in the teams of the journey that affect the target game."""

    rule_id = "RN-16"

    def exclusion(
        self, pokemon: PokemonData, availability: Availability, ctx: GameContext
    ) -> Discard | None:
        found = journey.excluding_entry(pokemon, ctx.journey, ctx.game.generation)
        if found is None:
            return None
        entry, member = found
        return Discard(
            pokemon.slug,
            self.rule_id,
            DiscardReason.JOURNEY,
            f"{pokemon.name} queda excluido porque se usó {member.pokemon} en {entry.game}",
        )


CANDIDATE_FILTERS: tuple[CandidateFilter, ...] = (
    AvailabilityFilter(),
    BreedingFilter(),
    JourneyFilter(),
)


def first_exclusion(
    pokemon: PokemonData, availability: Availability, ctx: GameContext
) -> Discard | None:
    """The first active filter that excludes the Pokémon, in catalogue order."""
    for candidate_filter in CANDIDATE_FILTERS:
        if not ctx.settings.is_enabled(candidate_filter.rule_id):
            continue
        discard = candidate_filter.exclusion(pokemon, availability, ctx)
        if discard is not None:
            return discard
    return None


def canonical_order(candidates: Sequence[Candidate]) -> list[Candidate]:
    """National Pokédex number, then form identifier: the order of every result (RF-08)."""
    return sorted(candidates, key=lambda c: (c.pokemon.dex_number, c.pokemon.slug))


def valid_candidates(ctx: GameContext) -> tuple[list[Candidate], list[Discard]]:
    """Favourites that pass every active filter, and why the others do not (RF-10)."""
    valid: list[Candidate] = []
    discards: list[Discard] = []
    for candidate in canonical_order(ctx.favorites):
        discard = first_exclusion(candidate.pokemon, candidate.availability, ctx)
        if discard is None:
            valid.append(candidate)
        else:
            discards.append(discard)
    return valid, discards
