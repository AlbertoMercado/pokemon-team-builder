"""The user's journey: games completed, in order, with their team (RN-16, RF-12)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JourneyMember:
    """A member of a registered team: its form, evolution line and region (CA-18).

    ``name`` is the Spanish name of the form, for the explanations; without it, the identifier.
    """

    pokemon: str
    evolution_chain: int
    region: str | None = None
    name: str | None = None

    @property
    def label(self) -> str:
        return self.name or self.pokemon


@dataclass(frozen=True)
class HallOfFameEntry:
    """A completed game. ``sequence`` is the order in the journey (RF-12).

    ``game_name`` is the Spanish name of the game, for the explanations; without it, ``game``.
    """

    game: str
    generation: int
    sequence: int
    members: tuple[JourneyMember, ...]
    game_name: str | None = None

    @property
    def game_label(self) -> str:
        return self.game_name or self.game
