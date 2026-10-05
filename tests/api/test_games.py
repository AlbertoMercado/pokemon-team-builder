"""/api/games: the games that can be the target (RF-05, CA-29)."""

from pathlib import Path

from tests.api.conftest import ClientFactory
from tests.api.factories import GameRow, reference_database


def test_target_games_or_every_loaded_game_in_release_order(
    make_client: ClientFactory, data_dir: Path
) -> None:
    games = [
        GameRow(
            "red",
            generation=1,
            version_group="red-blue",
            is_target=False,
            has_breeding=False,
            release_order=1,
        ),
        GameRow(
            "gold", generation=2, version_group="gold-silver", is_target=False, release_order=4
        ),
        GameRow("leafgreen", release_order=11),
        GameRow("firered", release_order=10),
    ]
    reference_database(data_dir, games=games)
    body = make_client().get("/api/games").json()
    assert body == [
        {
            "game": "firered",
            "name": "Firered",
            "generation": 3,
            "version_group": "firered-leafgreen",
            "target": True,
        },
        {
            "game": "leafgreen",
            "name": "Leafgreen",
            "generation": 3,
            "version_group": "firered-leafgreen",
            "target": True,
        },
    ]
    every = make_client().get("/api/games", params={"all": "true"}).json()
    assert [(g["game"], g["target"]) for g in every] == [
        ("red", False),
        ("gold", False),
        ("firered", True),
        ("leafgreen", True),
    ]


def test_without_reference_data_games_answer_503(make_client: ClientFactory) -> None:
    assert make_client().get("/api/games").status_code == 503
