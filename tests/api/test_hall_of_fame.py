"""/api/hall-of-fame: register, list, correct and remove completed games (RF-12, RF-13)."""

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import ClientFactory
from tests.api.factories import DEFAULT_GAMES, GameRow, form, reference_database

HALL_OF_FAME = "/api/hall-of-fame"
GAMES = (*DEFAULT_GAMES, GameRow("red", 1, "red-blue", is_target=False, has_breeding=False))
POKEMON = [
    form("clefairy", ("normal",), dex=35, past={1: ("normal",)}),
    form("magneton", ("electric", "steel"), dex=82, past={1: ("electric",)}),
    form("gengar", ("ghost", "poison"), dex=94, past={1: ("ghost", "poison")}),
    form("treecko", ("grass",), dex=252),
]


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    reference_database(data_dir, pokemon=POKEMON, games=GAMES)
    return make_client()


def _register(
    client: TestClient, game: str, completed_on: str, *members: str, notes: str | None = None
) -> dict[str, Any]:
    body = {"game": game, "completed_on": completed_on, "members": list(members), "notes": notes}
    response = client.post(HALL_OF_FAME, json=body)
    assert response.status_code == 201, response.json()
    entry: dict[str, Any] = response.json()
    return entry


def _journey(client: TestClient, **params: str) -> list[tuple[str, str, int, bool]]:
    entries = client.get(HALL_OF_FAME, params=params).json()
    return [(e["game"], e["completed_on"], e["order"], e["last"]) for e in entries]


def test_empty_at_first(client: TestClient) -> None:
    assert client.get(HALL_OF_FAME).json() == []


@pytest.mark.rn("RN-10")
def test_register_a_team(client: TestClient) -> None:
    """RF-12: the game, the date, the notes and each member's form, name and types."""
    entry = _register(client, "firered", "2026-05-01", "gengar", "magneton", notes="Sin objetos")
    assert {k: v for k, v in entry.items() if k != "id"} == {
        "game": "firered",
        "game_name": "Firered",
        "generation": 3,
        "completed_on": "2026-05-01",
        "notes": "Sin objetos",
        "order": 1,
        "last": True,
        "members": [
            {"position": 1, "pokemon": "gengar", "name": "Gengar", "types": ["ghost", "poison"]},
            {
                "position": 2,
                "pokemon": "magneton",
                "name": "Magneton",
                "types": ["electric", "steel"],
            },
        ],
    }
    assert client.get(HALL_OF_FAME).json() == [entry]


@pytest.mark.rn("RN-10")
def test_types_are_those_of_the_game(client: TestClient) -> None:
    """CA-07: Magneton was only Electric in Red; the copy keeps that."""
    entry = _register(client, "red", "2026-01-01", "magneton")
    assert entry["members"][0]["types"] == ["electric"]
    assert entry["generation"] == 1


@pytest.mark.rn("RN-16")
def test_the_journey_is_ordered_by_date_then_registration(client: TestClient) -> None:
    """RF-12: the last game completed is clear, even with two entries on the same date."""
    _register(client, "firered", "2026-05-01", "gengar")
    _register(client, "red", "2026-01-01", "clefairy")
    _register(client, "leafgreen", "2026-05-01", "magneton")
    assert _journey(client) == [
        ("red", "2026-01-01", 1, False),
        ("firered", "2026-05-01", 2, False),
        ("leafgreen", "2026-05-01", 3, True),
    ]


def test_filter_by_game_keeps_the_journey_order(client: TestClient) -> None:
    """RF-13."""
    _register(client, "firered", "2026-05-01", "gengar")
    _register(client, "red", "2026-01-01", "clefairy")
    assert _journey(client, game="firered") == [("firered", "2026-05-01", 2, True)]


@pytest.mark.parametrize(
    "body",
    [
        {"game": "pearl", "completed_on": "2026-01-01", "members": ["gengar"]},
        {"game": "firered", "completed_on": "2026-01-01", "members": ["missingno"]},
        {"game": "red", "completed_on": "2026-01-01", "members": ["treecko"]},  # 3rd generation
        {"game": "firered", "completed_on": "2026-01-01", "members": []},
        {"game": "firered", "completed_on": "2026-01-01", "members": ["gengar"] * 7},
        {"game": "firered", "completed_on": "ayer", "members": ["gengar"]},
    ],
)
def test_invalid_entries_are_rejected(client: TestClient, body: dict[str, Any]) -> None:
    assert client.post(HALL_OF_FAME, json=body).status_code == 422
    assert client.get(HALL_OF_FAME).json() == []


def test_a_form_can_be_repeated(client: TestClient) -> None:
    entry = _register(client, "firered", "2026-05-01", "gengar", "gengar")
    assert [m["position"] for m in entry["members"]] == [1, 2]


def test_correct_the_date_and_the_notes(client: TestClient) -> None:
    """RF-13: changing the date changes the order of the journey."""
    first = _register(client, "firered", "2026-05-01", "gengar", notes="Nota")
    _register(client, "leafgreen", "2026-06-01", "magneton")
    response = client.patch(
        f"{HALL_OF_FAME}/{first['id']}", json={"completed_on": "2026-07-01", "notes": None}
    )
    assert response.status_code == 200
    assert (response.json()["notes"], response.json()["last"]) == (None, True)
    assert [game for game, *_ in _journey(client)] == ["leafgreen", "firered"]


@pytest.mark.rn("RN-10")
def test_changing_the_game_or_the_team_copies_the_types_again(client: TestClient) -> None:
    entry = _register(client, "firered", "2026-05-01", "magneton")
    url = f"{HALL_OF_FAME}/{entry['id']}"
    moved = client.patch(url, json={"game": "red"}).json()
    assert moved["members"][0]["types"] == ["electric"]
    changed = client.patch(url, json={"members": ["gengar", "clefairy"]}).json()
    assert [(m["pokemon"], m["types"]) for m in changed["members"]] == [
        ("gengar", ["ghost", "poison"]),
        ("clefairy", ["normal"]),
    ]


@pytest.mark.parametrize(
    "change",
    [{}, {"game": None}, {"members": []}, {"game": "pearl"}, {"members": ["treecko"]}],
)
def test_invalid_corrections_are_rejected(client: TestClient, change: dict[str, Any]) -> None:
    entry = _register(client, "red", "2026-05-01", "magneton")
    assert client.patch(f"{HALL_OF_FAME}/{entry['id']}", json=change).status_code == 422
    assert client.get(HALL_OF_FAME).json()[0]["members"] == entry["members"]


def test_remove_an_entry(client: TestClient, data_dir: Path) -> None:
    entry = _register(client, "firered", "2026-05-01", "gengar")
    assert client.delete(f"{HALL_OF_FAME}/{entry['id']}").status_code == 204
    assert client.get(HALL_OF_FAME).json() == []
    with sqlite3.connect(data_dir / "user.sqlite") as db:  # its members go with it
        assert db.execute("SELECT count(*) FROM hall_of_fame_member").fetchone() == (0,)
    assert client.delete(f"{HALL_OF_FAME}/{entry['id']}").status_code == 404


def test_unknown_entries_are_not_found(client: TestClient) -> None:
    assert client.patch(f"{HALL_OF_FAME}/99", json={"notes": "x"}).status_code == 404
