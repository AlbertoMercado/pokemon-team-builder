"""What the engine returns: the best teams, the discards and how the presence rules apply."""

from dataclasses import dataclass
from enum import StrEnum

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
class RankedTeam:
    """A recommended team, its members in canonical order, with its score and breakdown."""

    members: tuple[PokemonData, ...]
    score: TeamScore

    @property
    def slugs(self) -> tuple[str, ...]:
        return tuple(member.slug for member in self.members)


@dataclass(frozen=True)
class GenerationResult:
    """The engine's answer for a ``GameContext``.

    ``teams`` are every team tied at the highest score after the RN-19 tie-break, in
    canonical order (RN-04). They are empty when the result is incomplete: the incomplete
    team and the suggestions come with the RN-08 phase of the engine.
    """

    status: GenerationStatus
    teams: tuple[RankedTeam, ...]
    discards: tuple[Discard, ...]
    presence: tuple[PresenceRequirement, ...]
    valid_candidates: tuple[str, ...]
    incomplete_reason: IncompleteReason | None = None
