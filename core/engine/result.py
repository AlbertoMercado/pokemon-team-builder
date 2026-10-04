"""What the engine returns: the best teams, grouped, with suggestions for their open slots."""

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from core.domain import PokemonData
from core.rules.candidate import Discard
from core.rules.team import PresenceRequirement
from core.scoring import TeamScore


class GenerationStatus(StrEnum):
    COMPLETE = "complete"  # teams of 6 favourites that meet every hard rule (RN-01)
    INCOMPLETE = "incomplete"  # no team of 6: RN-08 applies


class IncompleteReason(StrEnum):
    """Why there is no team of 6 favourites (RN-08, RF-10)."""

    RESERVED_SLOT = "reserved_slot"  # a presence rule needs a Pokémon that is not a favourite
    NOT_ENOUGH_CANDIDATES = "not_enough_candidates"  # fewer than 6 valid candidates
    NO_VALID_TEAM = "no_valid_team"  # enough candidates, but no 6 meet the rules together


@dataclass(frozen=True)
class Suggestion:
    """A Pokémon that is not a favourite and fits an open slot of the team (RN-08).

    ``gain`` is what it would add to the team's score. ``verified`` is false when some of its
    data was not confirmed by the user (CA-31).
    """

    pokemon: PokemonData
    gain: Fraction
    verified: bool


@dataclass(frozen=True)
class OpenSlots:
    """Open slots of an incomplete team and the Pokémon suggested for them, best first.

    A slot reserved by a presence rule has its ``rule_id`` and only admits Pokémon that meet
    the rule; free slots (``rule_id`` is ``None``) admit any Pokémon that fits.
    """

    count: int
    rule_id: str | None
    suggestions: tuple[Suggestion, ...]


@dataclass(frozen=True)
class RankedTeam:
    """A recommended team, its members in canonical order, with its score and breakdown.

    ``open_slots`` is empty for a team of 6.
    """

    members: tuple[PokemonData, ...]
    score: TeamScore
    open_slots: tuple[OpenSlots, ...] = ()

    @property
    def slugs(self) -> tuple[str, ...]:
        return tuple(member.slug for member in self.members)


@dataclass(frozen=True)
class TeamGroup:
    """Tied teams that only differ in interchangeable members (CA-33).

    ``positions`` has, for each position, the members that can take it, all of them with the
    same types; every combination is one of ``teams``. A team that cannot be grouped is a
    group of its own, with one member per position.
    """

    positions: tuple[tuple[PokemonData, ...], ...]
    teams: tuple[RankedTeam, ...]


@dataclass(frozen=True)
class GenerationResult:
    """The engine's answer for a ``GameContext``.

    ``teams`` are every team tied at the highest score after the RN-19 tie-break, in
    canonical order (RN-04), and ``groups`` the same teams grouped (CA-33). When the result is
    incomplete they are the incomplete teams, with the most favourites possible, and their
    open slots (RN-08).
    """

    status: GenerationStatus
    teams: tuple[RankedTeam, ...]
    groups: tuple[TeamGroup, ...]
    discards: tuple[Discard, ...]
    presence: tuple[PresenceRequirement, ...]
    valid_candidates: tuple[str, ...]
    incomplete_reason: IncompleteReason | None = None
