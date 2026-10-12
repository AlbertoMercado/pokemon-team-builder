"""/api/game-catalog: the user chooses their target games in the game catalogue (RF-25, RF-05,
CA-90 to CA-93)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from db.reference import MissingData, Platform, Playability
from db.sqlite import create_sqlite_engine
from tests.api.conftest import ClientFactory
from tests.api.factories import GameRow, catalog_game, reference_database

CATALOG = "/api/game-catalog"
RUBY = GameRow("ruby", version_group="ruby-sapphire", is_target=False, release_order=7)
RED = GameRow("red", generation=1, version_group="red-blue", is_target=False, release_order=1)


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    """Red (no bred Pokémon), Ruby (without key battles), FireRed (complete) and Sword, which is
    not loaded and is known to be playable."""
    path = reference_database(data_dir, games=[RED, RUBY, GameRow("firered", release_order=10)])
    sword = catalog_game("sword", 8, 3, complete=False)
    sword.platform, sword.playable_now = Platform.SWITCH, Playability.YES
    sword.missing = [MissingData.GENERATION_NOT_LOADED]
    engine = create_sqlite_engine(path)
    with Session(engine) as session:
        session.add(sword)
        session.commit()
    engine.dispose()
    return make_client()


def _choose(client: TestClient, game: str, **change: bool) -> tuple[int, dict[str, object]]:
    response = client.put(f"{CATALOG}/{game}", json=change)
    body: dict[str, object] = response.json()
    return response.status_code, body


def _codes(reasons: object) -> list[str]:
    assert isinstance(reasons, list)
    return [reason["code"] for reason in reasons]


def test_every_game_with_why_it_cannot_be_a_target(client: TestClient) -> None:
    """RF-25: in release order; CA-93: nothing is selected at first."""
    games = {game["game"]: game for game in client.get(CATALOG).json()}

    assert list(games) == ["red", "ruby", "firered", "sword"]
    assert not any(game["selected"] or game["target"] for game in games.values())
    assert _codes(games["red"]["obstacles"]) == [
        "cannot_receive_bred",
        "missing_data",
        "playability_unknown",
    ]
    assert _codes(games["ruby"]["missing"]) == ["key_battles"]
    assert _codes(games["firered"]["obstacles"]) == ["playability_unknown"]
    assert games["sword"]["known_playable"] is True
    assert _codes(games["sword"]["missing"]) == ["generation_not_loaded"]
    assert games["sword"]["missing"][0]["text"] == "Su generación todavía no se carga"


def test_selecting_a_playable_complete_game_makes_it_a_target(client: TestClient) -> None:
    status, game = _choose(client, "firered", selected=True, playable=True)

    assert status == 200
    assert (game["selected"], game["playable"], game["target"]) == (True, True, True)
    assert [g["game"] for g in client.get("/api/games").json()] == ["firered"]


def test_a_game_of_unknown_playability_asks_for_the_answer(client: TestClient) -> None:
    """CA-92: selecting it without answering is a 409 that says what to ask."""
    status, body = _choose(client, "firered", selected=True)

    assert status == 409
    detail = body["detail"]
    assert isinstance(detail, dict)
    assert _codes(detail["obstacles"]) == ["playability_unknown"]
    assert client.get("/api/games").json() == []


def test_a_game_that_is_not_playable_cannot_be_selected(client: TestClient) -> None:
    """CA-92: the answer is kept, but the game is not selected."""
    status, body = _choose(client, "firered", selected=True, playable=False)

    assert status == 409
    detail = body["detail"]
    assert isinstance(detail, dict)
    assert detail["message"] == "Firered no se puede seleccionar como juego objetivo"
    [game] = [g for g in client.get(CATALOG).json() if g["game"] == "firered"]
    assert (game["selected"], game["playable"]) == (False, False)
    assert _codes(game["obstacles"]) == ["not_playable"]


def test_a_game_lacking_data_says_what_it_lacks(client: TestClient) -> None:
    """RF-05: Ruby has no key battles; Red cannot even receive a bred Pokémon (CA-29)."""
    status, body = _choose(client, "ruby", selected=True, playable=True)
    assert status == 409
    detail = body["detail"]
    assert isinstance(detail, dict)
    assert (_codes(detail["obstacles"]), _codes(detail["missing"])) == (
        ["missing_data"],
        ["key_battles"],
    )
    status, body = _choose(client, "red", selected=True, playable=True)
    detail = body["detail"]
    assert isinstance(detail, dict)
    assert _codes(detail["obstacles"])[0] == "cannot_receive_bred"


def test_a_selected_game_can_be_removed_and_is_no_longer_a_target(client: TestClient) -> None:
    _choose(client, "firered", selected=True, playable=True)

    status, game = _choose(client, "firered", selected=False)

    assert (status, game["selected"], game["target"]) == (200, False, False)
    response = client.get("/api/games/firered/review")
    assert response.status_code == 404
    assert "catálogo de juegos" in response.json()["detail"]


def test_a_selected_game_that_becomes_not_playable_stays_selected(client: TestClient) -> None:
    """CA-93: it is no longer a target, and the catalogue says why."""
    _choose(client, "firered", selected=True, playable=True)

    status, game = _choose(client, "firered", playable=False)

    assert (status, game["selected"], game["target"]) == (200, True, False)
    assert client.get("/api/games").json() == []


def test_unknown_game_and_empty_change(client: TestClient) -> None:
    assert client.put(f"{CATALOG}/stadium", json={"selected": True}).status_code == 404
    assert client.put(f"{CATALOG}/firered", json={}).status_code == 422
