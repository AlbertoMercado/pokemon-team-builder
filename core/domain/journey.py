"""The user's journey: games completed, in order, with their team (RN-16, RF-12)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JourneyMember:
    """A member of a registered team: its form, evolution line and region (CA-18)."""

    pokemon: str
    evolution_chain: int
    region: str | None = None


@dataclass(frozen=True)
class HallOfFameEntry:
    """A completed game. ``sequence`` is the order in the journey (RF-12)."""

    game: str
    generation: int
    sequence: int
    members: tuple[JourneyMember, ...]
