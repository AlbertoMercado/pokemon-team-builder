"""Whether a game of the catalogue can be a target game, and why not (RF-05, RF-25, CA-91 to
CA-93): ``core/game_catalog.py``."""

import pytest

from core.game_catalog import CatalogEntry, GameChoice, Obstacle, is_target, obstacles

FIRERED = CatalogEntry("firered", receives_bred=True)
SWORD = CatalogEntry(
    "sword", receives_bred=True, missing=("generation_not_loaded",), known_playable=True
)
SWORD_LOADED = CatalogEntry("sword", receives_bred=True, known_playable=True)
RED = CatalogEntry("red", receives_bred=False, missing=("pokemon",))
SELECTED_PLAYABLE = GameChoice(selected=True, playable=True)


def test_a_complete_game_the_user_can_play_is_a_target() -> None:
    assert obstacles(FIRERED, SELECTED_PLAYABLE) == []
    assert is_target(FIRERED, SELECTED_PLAYABLE, completed=False)


def test_the_user_is_asked_whether_a_game_is_playable() -> None:
    """CA-92: unknown in the catalogue and without an answer."""
    assert obstacles(FIRERED, GameChoice()) == [Obstacle.PLAYABILITY_UNKNOWN]


def test_a_game_that_is_not_playable_cannot_be_a_target() -> None:
    """CA-92: Ruby has all its data, but cannot be played on a current system."""
    choice = GameChoice(selected=True, playable=False)
    assert obstacles(FIRERED, choice) == [Obstacle.NOT_PLAYABLE]
    assert not is_target(FIRERED, choice, completed=False)


def test_a_switch_game_is_known_to_be_playable() -> None:
    """CA-92: the user's answer does not matter when the catalogue knows."""
    assert obstacles(SWORD_LOADED, GameChoice(playable=False)) == []


def test_every_obstacle_in_the_order_of_rf25() -> None:
    """CA-29: Red cannot receive a bred Pokémon; it also lacks data and the answer."""
    assert obstacles(RED, GameChoice()) == [
        Obstacle.CANNOT_RECEIVE_BRED,
        Obstacle.MISSING_DATA,
        Obstacle.PLAYABILITY_UNKNOWN,
    ]
    assert obstacles(SWORD, GameChoice()) == [Obstacle.MISSING_DATA]


@pytest.mark.parametrize(
    ("choice", "completed"),
    [(GameChoice(playable=True), False), (SELECTED_PLAYABLE, True)],
    ids=["not-selected", "completed"],
)
def test_a_game_not_selected_or_completed_is_not_a_target(
    choice: GameChoice, completed: bool
) -> None:
    """CA-93: the user decides; CA-68: a completed game is not offered."""
    assert not is_target(FIRERED, choice, completed=completed)
