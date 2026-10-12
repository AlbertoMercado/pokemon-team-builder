"""Whether a game of the game catalogue can be a target game, and why not (RF-05, RF-25).

A game can be selected if it can receive a bred Pokémon (CA-29, CA-91), it is complete and it is
playable on a current Nintendo system (CA-92); the checks go in this order, the order of RF-25.
Whether it is playable comes from the catalogue when it is known and, if not, from the user's
answer: without one, the user has to be asked. A target game is a selected game that meets them
all and is not completed (CA-68, CA-93).
"""

from dataclasses import dataclass
from enum import StrEnum


class Obstacle(StrEnum):
    """Why a game cannot be a target game, in the order they are checked."""

    CANNOT_RECEIVE_BRED = "cannot_receive_bred"  # CA-29, CA-91
    MISSING_DATA = "missing_data"  # RF-05: see ``CatalogEntry.missing``
    PLAYABILITY_UNKNOWN = "playability_unknown"  # the user has to answer (CA-92)
    NOT_PLAYABLE = "not_playable"  # CA-92


@dataclass(frozen=True)
class CatalogEntry:
    """A game of the catalogue as the rules need it.

    ``missing`` is what it lacks to be complete (empty if it is complete); ``known_playable``,
    whether the catalogue knows it is playable on a current Nintendo system.
    """

    game: str
    receives_bred: bool
    missing: tuple[str, ...] = ()
    known_playable: bool = False


@dataclass(frozen=True)
class GameChoice:
    """What the user chose: whether the game is selected and their answer about whether it is
    playable (``None`` if they did not answer)."""

    selected: bool = False
    playable: bool | None = None


def playable(entry: CatalogEntry, choice: GameChoice) -> bool | None:
    """Whether the game is playable now: known by the catalogue, or the user's answer."""
    return True if entry.known_playable else choice.playable


def obstacles(entry: CatalogEntry, choice: GameChoice) -> list[Obstacle]:
    """Why ``entry`` cannot be selected, in the order of RF-25; empty if it can."""
    found = []
    if not entry.receives_bred:
        found.append(Obstacle.CANNOT_RECEIVE_BRED)
    if entry.missing:
        found.append(Obstacle.MISSING_DATA)
    match playable(entry, choice):
        case None:
            found.append(Obstacle.PLAYABILITY_UNKNOWN)
        case False:
            found.append(Obstacle.NOT_PLAYABLE)
        case True:
            pass
    return found


def is_target(entry: CatalogEntry, choice: GameChoice, *, completed: bool) -> bool:
    """A target game: selected, with no obstacle and not in the Hall of Fame (CA-93)."""
    return choice.selected and not obstacles(entry, choice) and not completed
