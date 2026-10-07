"""POST /api/games/{game}/team-checks: check a team chosen in the result (RF-12, CA-53)."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import ClientFactory
from tests.api.scenario import write_firered
from tests.core.scenario import FAVORITES

GENERATIONS = "/api/games/firered/generations"
CHECKS = "/api/games/firered/team-checks"
REVIEW = "/api/games/firered/review"


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    write_firered(data_dir)
    return make_client()


def _ready(client: TestClient, *pokemon: str) -> dict[str, Any]:
    """Generates with ``pokemon`` as favourites, after accepting the proposals."""
    for slug in pokemon:
        assert client.put(f"/api/favorites/{slug}").status_code == 200
    client.post(f"{REVIEW}/accept-proposals")
    response = client.post(GENERATIONS)
    assert response.status_code == 200, response.json()
    body: dict[str, Any] = response.json()
    return body


def _check(client: TestClient, *members: str) -> dict[str, Any]:
    response = client.post(CHECKS, json={"members": list(members)})
    assert response.status_code == 200, response.json()
    body: dict[str, Any] = response.json()
    return body


def test_a_generated_team_is_valid(client: TestClient) -> None:
    body = _ready(client, *FAVORITES)
    team = body["groups"][0]["teams"][1]["members"]  # the group of «Cloyster o Lapras»
    assert _check(client, *team) == {"valid": True, "problems": [], "unverified": []}


@pytest.mark.rn("RN-12")
def test_two_suggestions_that_clash_are_reported(client: TestClient) -> None:
    """With several free slots, each suggestion fits the team, but not necessarily the rest.

    RN-21 adds Blastoise, the only starter that fits with Gengar and Flareon (CA-65).
    """
    body = _ready(client, "gengar", "dragonite", "flareon")
    team = body["groups"][0]["teams"][0]
    assert "blastoise" in team["members"]
    [free] = [slot for slot in team["open_slots"] if slot["rule_id"] is None]
    suggestions = [s["pokemon"] for s in free["suggestions"]]
    grass = ["exeggutor", "tangela"]  # two suggestions of the same type, of different lines
    assert set(grass) <= {s["pokemon"] for s in suggestions}

    check = _check(client, *team["members"], *grass)

    assert check["valid"] is False
    assert [(p["rule_id"], p["members"]) for p in check["problems"]] == [("RN-12", grass)]
    assert check["problems"][0]["detail"].endswith("comparten tipo")
    # The suggestions of the pool have unconfirmed data in the scenario (CA-31); Blastoise's
    # were confirmed with the starters (CA-66).
    assert check["unverified"] == grass


@pytest.mark.rn("RN-13")
def test_a_presence_rule_that_is_not_met_is_reported(client: TestClient) -> None:
    body = _ready(client, *FAVORITES)
    team = [m for m in body["groups"][0]["teams"][0]["members"] if m != "dragonite"]

    check = _check(client, *team)

    assert check["valid"] is False
    [problem] = check["problems"]
    assert (problem["rule_id"], problem["members"]) == ("RN-13", [])
    assert problem["detail"].startswith("El equipo tiene que incluir a Dragonite")


@pytest.mark.rn("RN-11")
def test_a_member_that_does_not_pass_a_filter_is_reported(client: TestClient) -> None:
    body = _ready(client, *FAVORITES)
    team = body["groups"][0]["teams"][0]["members"][:5]
    check = _check(client, *team, "zapdos")
    # The filters come first; Zapdos may also clash with a member.
    assert (check["problems"][0]["rule_id"], check["problems"][0]["members"]) == (
        "RN-11",
        ["zapdos"],
    )


@pytest.mark.rn("RN-18")
def test_nothing_is_checked_with_unverified_data(client: TestClient) -> None:
    client.put("/api/favorites/raichu")
    response = client.post(CHECKS, json={"members": ["raichu"]})
    assert response.status_code == 409
    assert response.json()["detail"]["pending"]


def test_repeated_and_unknown_members_are_422(client: TestClient) -> None:
    _ready(client, "gengar")
    repeated = client.post(CHECKS, json={"members": ["gengar", "gengar"]})
    assert repeated.status_code == 422
    assert repeated.json() == {"detail": "Pokémon repetidos en el equipo: gengar"}
    unknown = client.post(CHECKS, json={"members": ["gengar", "missingno"]})
    assert unknown.status_code == 422
    assert unknown.json() == {"detail": "Pokémon que no existen en la 3.ª generación: missingno"}
    assert client.post(CHECKS, json={"members": []}).status_code == 422
    assert client.post(CHECKS, json={"members": ["a"] * 7}).status_code == 422


def test_only_target_games(client: TestClient) -> None:
    assert (
        client.post("/api/games/red/team-checks", json={"members": ["gengar"]}).status_code == 404
    )
