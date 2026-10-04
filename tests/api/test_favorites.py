"""/api/favorites: add, list and remove favourites (RF-03, RF-04, RN-05, RN-09)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import ClientFactory
from tests.api.factories import form, reference_database

POKEMON = [
    form("vulpix", ("fire",), dex=37),
    form("vulpix-alola", ("ice",), dex=37, species="vulpix", region="alola"),
    form("magneton", ("electric", "steel"), dex=82, past={1: ("electric",)}),
    form("dragonite", ("dragon", "flying"), dex=149),
]


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    reference_database(data_dir, pokemon=POKEMON)
    return make_client()


def _slugs(client: TestClient) -> list[str]:
    return [f["pokemon"] for f in client.get("/api/favorites").json()["favorites"]]


def test_no_favourites_at_first(client: TestClient) -> None:
    assert client.get("/api/favorites").json() == {"total": 0, "favorites": []}


@pytest.mark.rn("RN-09")
def test_add_a_favourite(client: TestClient) -> None:
    """What is added is the form and evolution to reach."""
    response = client.put("/api/favorites/dragonite")
    assert response.status_code == 200
    body = response.json()
    assert (body["pokemon"], body["name"], body["dex_number"], body["types"]) == (
        "dragonite",
        "Dragonite",
        149,
        ["dragon", "flying"],
    )
    assert _slugs(client) == ["dragonite"]


def test_adding_twice_changes_nothing(client: TestClient) -> None:
    first = client.put("/api/favorites/dragonite").json()
    second = client.put("/api/favorites/dragonite").json()
    assert first == second
    assert client.get("/api/favorites").json()["total"] == 1


@pytest.mark.rn("RN-05")
def test_regional_forms_are_separate_favourites(client: TestClient) -> None:
    client.put("/api/favorites/vulpix-alola")
    client.put("/api/favorites/vulpix")
    body = client.get("/api/favorites").json()
    assert body["total"] == 2
    assert [(f["pokemon"], f["types"]) for f in body["favorites"]] == [
        ("vulpix", ["fire"]),
        ("vulpix-alola", ["ice"]),
    ]


def test_list_in_pokedex_order_with_current_types(client: TestClient) -> None:
    """Magneton is Electric/Steel now, though only Electric in the 1st generation."""
    for slug in ("dragonite", "magneton", "vulpix"):
        client.put(f"/api/favorites/{slug}")
    favorites = client.get("/api/favorites").json()["favorites"]
    assert [f["pokemon"] for f in favorites] == ["vulpix", "magneton", "dragonite"]
    assert favorites[1]["types"] == ["electric", "steel"]


def test_unknown_form_is_not_added(client: TestClient) -> None:
    response = client.put("/api/favorites/missingno")
    assert response.status_code == 404
    assert "missingno" in response.json()["detail"]


def test_remove_a_favourite(client: TestClient) -> None:
    client.put("/api/favorites/dragonite")
    assert client.delete("/api/favorites/dragonite").status_code == 204
    assert _slugs(client) == []


def test_removing_what_is_not_a_favourite_is_404(client: TestClient) -> None:
    assert client.delete("/api/favorites/dragonite").status_code == 404


def test_favourites_are_kept_between_sessions(
    client: TestClient, make_client: ClientFactory
) -> None:
    """RF-04: the list lives in user.sqlite, not in the application."""
    client.put("/api/favorites/dragonite")
    assert _slugs(make_client()) == ["dragonite"]


def test_without_reference_data_favourites_answer_503(make_client: ClientFactory) -> None:
    assert make_client().get("/api/favorites").status_code == 503
