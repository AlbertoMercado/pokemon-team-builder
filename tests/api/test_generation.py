"""POST /api/games/{game}/generations: teams of the real FireRed scenario (RF-08 to RF-10)."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from core.engine import generate
from db.reference import Origin
from tests.api.conftest import ClientFactory
from tests.api.scenario import Load, write_firered
from tests.core.scenario import FAVORITES, firered_context

GENERATIONS = "/api/games/firered/generations"
REVIEW = "/api/games/firered/review"


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    write_firered(data_dir)
    return make_client()


def _favorites(client: TestClient, *pokemon: str) -> None:
    for slug in pokemon:
        assert client.put(f"/api/favorites/{slug}").status_code == 200


def _generate(client: TestClient) -> dict[str, Any]:
    response = client.post(GENERATIONS)
    assert response.status_code == 200, response.json()
    body: dict[str, Any] = response.json()
    return body


def _ready(client: TestClient, *pokemon: str) -> dict[str, Any]:
    """Generates with ``pokemon`` as favourites, after accepting the proposals."""
    _favorites(client, *pokemon)
    client.post(f"{REVIEW}/accept-proposals")
    return _generate(client)


def _teams(body: dict[str, Any]) -> list[tuple[str, ...]]:
    return [tuple(team["members"]) for group in body["groups"] for team in group["teams"]]


@pytest.mark.rn("RN-18")
def test_nothing_is_generated_with_unverified_data(client: TestClient) -> None:
    """RF-08: 409 with the same data the review asks for."""
    _favorites(client, "raichu")
    response = client.post(GENERATIONS)
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "confirmar" in detail["message"]
    review = client.get(REVIEW).json()
    assert detail["pending"] == review["facts"]
    assert [f["fact_key"] for f in detail["pending"]] == [
        "mechanic:firered:contests",
        "mechanic:firered:day_night_cycle",
        "pokemon:firered:raichu:arrival",
    ]


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-19")
def test_firered_gives_the_engine_teams(client: TestClient) -> None:
    """The real scenario through the API: the engine's tied teams, grouped (CA-33)."""
    body = _ready(client, *FAVORITES)
    assert (body["game"], body["status"], body["incomplete_reason"]) == (
        "firered",
        "complete",
        None,
    )
    expected = generate(firered_context())
    assert _teams(body) == [team.slugs for team in expected.teams]
    positions = [[[p["pokemon"] for p in a] for a in g["positions"]] for g in body["groups"]]
    assert positions[1][1] == ["cloyster", "lapras"]
    lapras = next(p for p in body["groups"][1]["positions"][1] if p["pokemon"] == "lapras")
    assert lapras == {
        "pokemon": "lapras",
        "name": "Lapras",
        "dex_number": 131,
        "types": ["water", "ice"],
        "image_url": None,
    }


@pytest.mark.rn("RN-04")
def test_scores_are_rounded_integers_that_add_up(client: TestClient) -> None:
    """CA-51: 223/12 is shown as 19, and RN-17 (10 · 23/24) gets the unit left over."""
    body = _ready(client, *FAVORITES)
    assert body["score"] == 19
    team = body["groups"][0]["teams"][0]
    assert (team["score"], team["dual_type_members"]) == (19, 5)
    breakdown = [
        (r["rule_id"], r["weight"], r["score"], r["contribution"]) for r in team["breakdown"]
    ]
    assert breakdown == [
        ("RN-06", 1, 100, 1),
        ("RN-15", 3, 100, 3),
        ("RN-17", 10, 96, 10),
        ("RN-20", 5, 100, 5),
    ]
    assert team["breakdown"][2]["name"] == "Tipos eficaces frente a los combates clave"
    assert team["open_slots"] == []


@pytest.mark.rn("RN-04")
def test_weights_and_disabled_rules_change_the_breakdown(client: TestClient) -> None:
    client.patch("/api/rules/RN-20", json={"enabled": False})
    client.patch("/api/rules/RN-06", json={"weight": 0})
    team = _ready(client, *FAVORITES)["groups"][0]["teams"][0]
    assert [(r["rule_id"], r["contribution"]) for r in team["breakdown"]] == [
        ("RN-06", 0),
        ("RN-15", 3),
        ("RN-17", 10),
    ]
    assert team["score"] == 13


@pytest.mark.rn("RN-11")
@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-14")
def test_discards_and_presence_rules(client: TestClient) -> None:
    body = _ready(client, *FAVORITES)
    assert [
        (d["pokemon"], d["name"], d["rule_id"], d["reason"], d["fact_key"])
        for d in body["discards"]
    ] == [
        ("zapdos", "Zapdos", "RN-11", "breeding", None),
        ("mewtwo", "Mewtwo", "RN-11", "breeding", None),
    ]
    assert [(p["rule_id"], p["level"], p["status"], p["options"]) for p in body["presence"]] == [
        ("RN-13", 1, "candidates", ["dragonite"]),
        ("RN-14", 1, "candidates", ["vaporeon", "jolteon", "flareon"]),
    ]


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-03")
def test_confirmed_data_used_is_listed(client: TestClient) -> None:
    """RF-09: the DDF example; Raichu's confirmed arrival decides its discard."""
    _favorites(client, "raichu", "gengar")
    client.put(f"{REVIEW}/pokemon:firered:raichu:arrival", json={"value": False})
    body = _ready(client)
    used = [(f["fact_key"], f["value"]) for f in body["confirmed_facts"]]
    assert used == [
        ("mechanic:firered:contests", False),
        ("mechanic:firered:day_night_cycle", False),
        ("pokemon:firered:raichu:arrival", False),
        ("pokemon:firered:gengar:arrival", True),
    ]
    [raichu] = body["discards"]
    assert (raichu["reason"], raichu["fact_key"]) == ("arrival", "pokemon:firered:raichu:arrival")


@pytest.mark.rn("RN-08")
@pytest.mark.rn("RN-18")
def test_an_incomplete_team_has_suggestions(client: TestClient) -> None:
    """RF-10: with 4 favourites the team has 2 free slots; suggestions whose own data was not
    confirmed are marked as unverified (CA-31)."""
    client.patch("/api/rules/RN-13", json={"enabled": False})
    client.patch("/api/rules/RN-14", json={"enabled": False})
    client.put(f"{REVIEW}/pokemon:firered:jolteon:arrival", json={"value": True})
    body = _ready(client, "venusaur", "charizard", "blastoise", "pikachu")
    assert (body["status"], body["incomplete_reason"]) == ("incomplete", "not_enough_candidates")
    assert [d["pokemon"] for d in body["discards"]] == ["pikachu"]  # it hatches as Pichu
    team = body["groups"][0]["teams"][0]
    assert team["members"] == ["venusaur", "charizard", "blastoise"]
    [slots] = team["open_slots"]
    assert (slots["count"], slots["rule_id"]) == (3, None)
    suggestions = {s["pokemon"]["pokemon"]: s for s in slots["suggestions"]}
    assert suggestions["jolteon"]["verified"]
    assert not suggestions["alakazam"]["verified"]
    gains = [s["gain"] for s in slots["suggestions"]]
    assert gains == sorted(gains, reverse=True)
    assert all(isinstance(g, int) for g in gains)


@pytest.mark.rn("RN-08")
@pytest.mark.rn("RN-13")
def test_a_reserved_slot_says_which_rule_reserves_it(client: TestClient) -> None:
    body = _ready(client, "venusaur", "charizard", "blastoise", "jolteon", "alakazam", "machamp")
    assert body["incomplete_reason"] == "reserved_slot"
    slots = body["groups"][0]["teams"][0]["open_slots"]
    assert [(s["count"], s["rule_id"]) for s in slots] == [(1, "RN-13")]
    assert {s["pokemon"]["pokemon"] for s in slots[0]["suggestions"]} <= {
        "dratini",
        "dragonair",
        "dragonite",
    }


@pytest.mark.rn("RN-17")
def test_a_pending_key_battle_does_not_block_without_rn17(
    make_client: ClientFactory, data_dir: Path
) -> None:
    write_firered(data_dir, load=Load(battle_origins={"firered-misty": Origin.PENDING}))
    client = make_client()
    _favorites(client, *FAVORITES)
    client.post(f"{REVIEW}/accept-proposals")
    assert client.post(GENERATIONS).status_code == 409
    client.patch("/api/rules/RN-17", json={"enabled": False})
    body = _generate(client)
    assert "RN-17" not in [r["rule_id"] for r in body["groups"][0]["teams"][0]["breakdown"]]


def test_the_same_input_gives_the_same_answer(client: TestClient) -> None:
    """RF-08: the generation is deterministic and is not stored."""
    first = _ready(client, *FAVORITES)
    assert _generate(client) == first


def test_the_answer_says_which_data_was_used(client: TestClient) -> None:
    version = _ready(client, *FAVORITES)["data_version"]
    assert version["pokeapi_commit"].startswith("bc92d3b")
    assert version["games"] == ["firered"]


def test_without_favourites_the_team_is_empty_with_suggestions(client: TestClient) -> None:
    body = _ready(client)
    assert (body["status"], body["incomplete_reason"]) == ("incomplete", "reserved_slot")
    team = body["groups"][0]["teams"][0]
    assert (team["members"], team["score"]) == ([], body["score"])
    assert sum(slot["count"] for slot in team["open_slots"]) == 6


def test_a_game_that_is_not_a_target_is_not_found(client: TestClient) -> None:
    assert client.post("/api/games/gold/generations").status_code == 404


def test_without_reference_data_nothing_is_generated(make_client: ClientFactory) -> None:
    assert make_client().post(GENERATIONS).status_code == 503


def test_the_409_is_in_the_openapi_contract(client: TestClient) -> None:
    operation = client.get("/api/openapi.json").json()["paths"]["/api/games/{game}/generations"]
    assert operation["post"]["responses"]["409"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PendingDataOut"
    }


def _register_leafgreen(client: TestClient, *members: str) -> int:
    body = {"game": "leafgreen", "completed_on": "2026-05-01", "members": list(members)}
    response = client.post("/api/hall-of-fame", json=body)
    assert response.status_code == 201
    entry_id: int = response.json()["id"]
    return entry_id


@pytest.mark.rn("RN-16")
def test_a_registered_team_excludes_its_lines(client: TestClient) -> None:
    """The DDF example: after Leaf Green, Gengar's line and Vaporeon are excluded in Fire Red,
    but not Dragonite (CA-21) nor the other Eevee evolutions."""
    _register_leafgreen(client, "dragonite", "vaporeon", "gengar", "charizard")
    body = _ready(client, *FAVORITES)
    journey = {d["pokemon"]: d["detail"] for d in body["discards"] if d["reason"] == "journey"}
    assert sorted(journey) == ["charizard", "gengar", "vaporeon"]
    # The names, not the identifiers (#42); the scenario names Leaf Green «Leafgreen».
    assert journey["gengar"] == "Gengar queda excluido porque se usó Gengar en Leafgreen"
    members = {slug for team in _teams(body) for slug in team}
    assert {"dragonite", "flareon"} <= members
    assert not members & set(journey)


@pytest.mark.rn("RN-16")
def test_without_rn16_the_journey_excludes_nothing(client: TestClient) -> None:
    _register_leafgreen(client, "gengar")
    client.patch("/api/rules/RN-16", json={"enabled": False})
    body = _ready(client, *FAVORITES)
    assert "journey" not in [d["reason"] for d in body["discards"]]


@pytest.mark.rn("RN-16")
@pytest.mark.rn("RN-18")
def test_the_journey_changes_what_has_to_be_confirmed(client: TestClient) -> None:
    """A favourite excluded by the journey is not asked about; removing the entry asks again."""
    _favorites(client, "gengar")
    entry_id = _register_leafgreen(client, "haunter")  # same line, same form (CA-18)
    subjects = [f["subject"] for f in client.get(REVIEW).json()["facts"]]
    assert "gengar" not in subjects
    client.delete(f"/api/hall-of-fame/{entry_id}")
    subjects = [f["subject"] for f in client.get(REVIEW).json()["facts"]]
    assert "gengar" in subjects
