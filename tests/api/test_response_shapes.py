"""The complete shape of each response schema, in one place (#77).

The other tests of the API check only the fields they are about, so adding a field to a
response does not break them. These tests fix the exact fields of each schema, so a new or a
missing field is noticed here, on purpose: this file is the only one to update. The meaning of
each field is in the API reference, generated from the code (ADR-0012).

Every response comes from the real FireRed scenario (``tests/api/scenario.py``), with a
generation and a Hall of Fame entry.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.config import Settings
from api.main import create_app
from tests.api.scenario import write_firered
from tests.core.scenario import FAVORITES

POKEMON = {"pokemon", "name", "dex_number", "types", "image_url"}


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    data_dir: Path = tmp_path_factory.mktemp("data")
    write_firered(data_dir)
    with TestClient(create_app(Settings(data_dir))) as client:
        for pokemon in FAVORITES:
            assert client.put(f"/api/favorites/{pokemon}").status_code == 200
        entry = {"game": "leafgreen", "completed_on": "2026-01-10", "members": ["gengar"]}
        assert client.post("/api/hall-of-fame", json=entry).status_code == 201
        yield client


def _get(client: TestClient, url: str) -> Any:
    response = client.get(url)
    assert response.status_code == 200, response.json()
    return response.json()


def test_meta(client: TestClient) -> None:
    body = _get(client, "/api/meta")
    assert set(body) == {"app_version", "data"}
    assert set(body["data"]) == {"pokeapi_commit", "sprites_commit", "ingested_at", "games"}


def test_game(client: TestClient) -> None:
    [game, *_] = _get(client, "/api/games?all=true")
    assert set(game) == {
        "game",
        "name",
        "generation",
        "version_group",
        "target",
        "completed",
        "cover_url",
        "cover_source_url",
    }


def test_catalogue_and_favourites(client: TestClient) -> None:
    catalogue = _get(client, "/api/pokemon")
    assert set(catalogue) == {"total", "pokemon"}
    assert set(catalogue["pokemon"][0]) == POKEMON | {"region", "favorite"}

    favorites = _get(client, "/api/favorites")
    assert set(favorites) == {"total", "favorites"}
    assert set(favorites["favorites"][0]) == POKEMON | {"added_at"}


def test_review_fact(client: TestClient) -> None:
    review = _get(client, "/api/games/firered/review")
    assert set(review["facts"][0]) == {
        "fact_key",
        "kind",
        "subject",
        "name",
        "origin",
        "proposal",
        "status",
        "value",
        "confirmed_at",
        "outdated",
        "source_url",
    }


def test_generated_pokemon(client: TestClient) -> None:
    assert client.post("/api/games/firered/review/accept-proposals").status_code == 200
    response = client.post("/api/games/firered/generations")
    assert response.status_code == 200, response.json()
    [first, *_] = response.json()["groups"][0]["positions"][0]
    assert set(first) == POKEMON


def test_hall_of_fame_entry(client: TestClient) -> None:
    [entry] = _get(client, "/api/hall-of-fame")
    assert set(entry) == {
        "id",
        "game",
        "game_name",
        "generation",
        "cover_url",
        "cover_source_url",
        "completed_on",
        "notes",
        "order",
        "last",
        "members",
    }
    assert set(entry["members"][0]) == POKEMON - {"dex_number"} | {"position"}


def test_pokedex_summary(client: TestClient) -> None:
    [pokedex] = _get(client, "/api/pokedex")
    assert set(pokedex) == {"game", "game_name", "cover_url", "hall_of_fame_entry", "progress"}
    assert set(pokedex["progress"]) == {"registered", "total", "impossible", "percent", "status"}
