"""/api/games/{game}/review: see, confirm and correct the unverified data (RF-15, RN-18)."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from db.reference import Origin
from tests.api.conftest import ClientFactory
from tests.api.scenario import Load, write_firered

REVIEW = "/api/games/firered/review"
RAICHU_ARRIVAL = "pokemon:firered:raichu:arrival"
MECHANICS = ["mechanic:firered:contests", "mechanic:firered:day_night_cycle"]


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    write_firered(data_dir)
    return make_client()


def _review(client: TestClient) -> dict[str, Any]:
    response = client.get(REVIEW)
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def _facts(client: TestClient) -> dict[str, dict[str, Any]]:
    return {fact["fact_key"]: fact for fact in _review(client)["facts"]}


def _favorites(client: TestClient, *pokemon: str) -> None:
    for slug in pokemon:
        assert client.put(f"/api/favorites/{slug}").status_code == 200


@pytest.mark.rn("RN-18")
def test_without_favourites_only_the_game_mechanics_are_asked(client: TestClient) -> None:
    """The key battles of a real load are automatic: they are not reviewed."""
    body = _review(client)
    assert body["game"] == "firered"
    assert body["pending"] == 2
    assert [fact["fact_key"] for fact in body["facts"]] == MECHANICS
    contests = body["facts"][0]
    assert contests == {
        "fact_key": "mechanic:firered:contests",
        "kind": "mechanic",
        "subject": "contests",
        "name": "Concursos",
        "origin": "inferred",
        "proposal": False,
        "status": "pending",
        "value": None,
        "confirmed_at": None,
        "outdated": False,
    }


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-03")
def test_raichu_arrival_is_proposed_and_confirmed(client: TestClient) -> None:
    """The DDF example: the load proposes that Raichu cannot arrive; the user confirms it."""
    _favorites(client, "raichu")
    raichu = _facts(client)[RAICHU_ARRIVAL]
    assert (raichu["name"], raichu["proposal"], raichu["status"]) == ("Raichu", False, "pending")

    response = client.put(f"{REVIEW}/{RAICHU_ARRIVAL}", json={"value": False})
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["value"], body["outdated"]) == ("confirmed", False, False)
    assert body["confirmed_at"] is not None
    assert _review(client)["pending"] == 2  # the mechanics


@pytest.mark.rn("RN-18")
def test_a_value_can_be_corrected(client: TestClient) -> None:
    _favorites(client, "raichu")
    client.put(f"{REVIEW}/{RAICHU_ARRIVAL}", json={"value": True})
    raichu = _facts(client)[RAICHU_ARRIVAL]
    assert (raichu["proposal"], raichu["value"], raichu["status"]) == (False, True, "confirmed")


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-11")
def test_favourites_discarded_with_known_data_are_not_asked(client: TestClient) -> None:
    """Zapdos cannot be bred, so whether it can arrive does not matter."""
    _favorites(client, "zapdos", "gengar")
    assert [fact["subject"] for fact in _review(client)["facts"]][2:] == ["gengar"]


@pytest.mark.rn("RN-18")
def test_facts_follow_the_order_of_the_game_and_the_pokedex(client: TestClient) -> None:
    _favorites(client, "raichu", "gengar", "dragonite", "charizard")
    subjects = [fact["subject"] for fact in _review(client)["facts"]]
    assert subjects == ["contests", "day_night_cycle", "charizard", "raichu", "gengar", "dragonite"]


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-17")
def test_an_unverified_key_battle_is_asked_only_with_rn17(
    make_client: ClientFactory, data_dir: Path
) -> None:
    write_firered(data_dir, load=Load(battle_origins={"firered-misty": Origin.INFERRED}))
    client = make_client()
    misty = _facts(client)["battle:firered:misty"]
    assert (misty["kind"], misty["name"], misty["proposal"]) == (
        "key_battle",
        "Misty",
        ["staryu", "starmie"],
    )
    client.patch("/api/rules/RN-17", json={"enabled": False})
    assert "battle:firered:misty" not in _facts(client)


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-17")
def test_a_pending_key_battle_gets_its_team_from_the_user(
    make_client: ClientFactory, data_dir: Path
) -> None:
    write_firered(data_dir, load=Load(battle_origins={"firered-misty": Origin.PENDING}))
    client = make_client()
    key = "battle:firered:misty"
    assert _facts(client)[key]["proposal"] is None
    team = ["staryu", "starmie"]
    response = client.put(f"{REVIEW}/{key}", json={"value": team})
    assert response.status_code == 200
    assert (response.json()["status"], response.json()["value"]) == ("confirmed", team)


@pytest.mark.rn("RN-18")
def test_accepting_the_proposals_leaves_the_pending_values(
    make_client: ClientFactory, data_dir: Path
) -> None:
    """Inferred values are accepted at once; a pending one, without proposal, is not."""
    write_firered(data_dir, load=Load(battle_origins={"firered-misty": Origin.PENDING}))
    client = make_client()
    _favorites(client, "raichu", "gengar")
    client.put(f"{REVIEW}/{RAICHU_ARRIVAL}", json={"value": True})

    response = client.post(f"{REVIEW}/accept-proposals")
    assert response.status_code == 200
    body = response.json()
    assert body["pending"] == 1
    states = {fact["subject"]: (fact["status"], fact["value"]) for fact in body["facts"]}
    assert states == {
        "contests": ("confirmed", False),
        "day_night_cycle": ("confirmed", False),
        "firered-misty": ("pending", None),
        "raichu": ("confirmed", True),  # the user's correction is kept
        "gengar": ("confirmed", True),
    }


@pytest.mark.rn("RN-18")
def test_a_confirmation_stops_applying_when_a_load_changes_the_proposal(
    make_client: ClientFactory, data_dir: Path
) -> None:
    write_firered(data_dir)
    client = make_client()
    _favorites(client, "raichu", "gengar")
    client.post(f"{REVIEW}/accept-proposals")

    write_firered(data_dir, load=Load(arrival={"raichu": True}))  # a new load, then a restart
    restarted = make_client()
    facts = _facts(restarted)
    assert _review(restarted)["pending"] == 1
    raichu = facts[RAICHU_ARRIVAL]
    assert (raichu["proposal"], raichu["status"], raichu["outdated"]) == (True, "pending", True)
    assert facts["pokemon:firered:gengar:arrival"]["status"] == "confirmed"


def test_an_automatic_value_is_not_reviewed(client: TestClient) -> None:
    response = client.put(f"{REVIEW}/battle:firered:brock", json={"value": ["onix"]})
    assert response.status_code == 409


@pytest.mark.parametrize(
    ("fact_key", "value"),
    [
        (RAICHU_ARRIVAL, ["raichu"]),  # a yes/no value
        (RAICHU_ARRIVAL, "yes"),
        (RAICHU_ARRIVAL, None),
        ("battle:firered:misty", True),  # a key battle's team
        ("battle:firered:misty", []),
        ("battle:firered:misty", ["staryu", "togepi-unknown"]),
    ],
)
def test_invalid_values_are_rejected(
    make_client: ClientFactory, data_dir: Path, fact_key: str, value: object
) -> None:
    write_firered(data_dir, load=Load(battle_origins={"firered-misty": Origin.INFERRED}))
    client = make_client()
    response = client.put(f"{REVIEW}/{fact_key}", json={"value": value})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "path",
    [
        f"{REVIEW}/pokemon:firered:missingno:arrival",
        f"{REVIEW}/{RAICHU_ARRIVAL.replace('firered', 'leafgreen')}",  # another game's
        "/api/games/gold/review/pokemon:gold:raichu:arrival",  # not a target game
    ],
)
def test_unknown_facts_and_games_are_not_found(client: TestClient, path: str) -> None:
    assert client.put(path, json={"value": True}).status_code == 404


def test_review_of_a_game_that_is_not_a_target(client: TestClient) -> None:
    assert client.get("/api/games/gold/review").status_code == 404
    assert client.post("/api/games/gold/review/accept-proposals").status_code == 404


def test_without_reference_data_the_review_is_unavailable(make_client: ClientFactory) -> None:
    assert make_client().get(REVIEW).status_code == 503
