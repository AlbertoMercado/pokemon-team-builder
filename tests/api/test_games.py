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
            "completed": False,
            "cover_url": None,
            "cover_source_url": None,
        },
        {
            "game": "leafgreen",
            "name": "Leafgreen",
            "generation": 3,
            "version_group": "firered-leafgreen",
            "target": True,
            "completed": False,
            "cover_url": None,
            "cover_source_url": None,
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


def test_an_incomplete_game_cannot_be_chosen(make_client: ClientFactory, data_dir: Path) -> None:
    """RF-05 and CA-67: Ruby is loaded, but without its key battles it is not complete. It is
    not offered, its review and generation answer 404 even by its address, and it is still
    listed for the Hall of Fame."""
    ruby = GameRow("ruby", version_group="ruby-sapphire", is_target=False, release_order=7)
    reference_database(data_dir, games=[ruby, GameRow("firered", release_order=10)])
    client = make_client()

    assert [g["game"] for g in client.get("/api/games").json()] == ["firered"]
    every = client.get("/api/games", params={"all": "true"}).json()
    assert [(g["game"], g["target"]) for g in every] == [("ruby", False), ("firered", True)]
    assert client.get("/api/games/ruby/review").status_code == 404
    assert client.post("/api/games/ruby/generations").status_code == 404
    response = client.post("/api/games/ruby/team-checks", json={"members": ["bulbasaur"]})
    assert response.status_code == 404
