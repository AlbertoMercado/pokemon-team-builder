"""/api/rules: the rule catalogue and the user's settings (RF-06, RF-07, CA-41)."""

import pytest
from fastapi.testclient import TestClient

from core.rules.catalog import CATALOG
from tests.api.conftest import ClientFactory


@pytest.fixture
def client(make_client: ClientFactory) -> TestClient:
    """The rules do not need reference.sqlite."""
    return make_client()


def _rule(client: TestClient, rule_id: str) -> dict[str, object]:
    rules: list[dict[str, object]] = client.get("/api/rules").json()
    [rule] = [r for r in rules if r["rule_id"] == rule_id]
    return rule


@pytest.mark.rn("RN-04")
def test_every_rule_of_the_catalogue_in_order(client: TestClient) -> None:
    rules = client.get("/api/rules").json()
    assert [r["rule_id"] for r in rules] == list(CATALOG)
    assert all(r["description"] for r in rules)


@pytest.mark.rn("RN-04")
def test_defaults_every_rule_active_with_its_weight(client: TestClient) -> None:
    """CA-41: every configurable rule is active by default, with the weights of CA-05."""
    rules = client.get("/api/rules").json()
    assert all(r["enabled"] for r in rules)
    weights = {r["rule_id"]: r["weight"] for r in rules if r["kind"] == "soft"}
    assert weights == {"RN-06": 1, "RN-15": 3, "RN-17": 10, "RN-20": 5}
    assert _rule(client, "RN-12")["weight"] is None


@pytest.mark.rn("RN-12")
def test_switch_off_a_hard_rule(client: TestClient) -> None:
    response = client.patch("/api/rules/RN-12", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert _rule(client, "RN-12")["enabled"] is False


@pytest.mark.rn("RN-17")
def test_change_the_weight_of_a_soft_rule(client: TestClient) -> None:
    response = client.patch("/api/rules/RN-17", json={"weight": 7})
    assert (response.json()["weight"], response.json()["default_weight"]) == (7, 10)
    assert _rule(client, "RN-17")["weight"] == 7


def test_changing_one_thing_keeps_the_other(client: TestClient) -> None:
    client.patch("/api/rules/RN-15", json={"weight": 0})
    client.patch("/api/rules/RN-15", json={"enabled": False})
    rule = _rule(client, "RN-15")
    assert (rule["enabled"], rule["weight"]) == (False, 0)


def test_settings_are_kept_between_sessions(client: TestClient, make_client: ClientFactory) -> None:
    client.patch("/api/rules/RN-07", json={"enabled": False})
    assert _rule(make_client(), "RN-07")["enabled"] is False


@pytest.mark.rn("RN-01")
def test_a_structural_rule_cannot_be_switched_off(client: TestClient) -> None:
    response = client.patch("/api/rules/RN-01", json={"enabled": False})
    assert response.status_code == 409
    assert "RN-01" in response.json()["detail"]


def test_a_hard_rule_has_no_weight(client: TestClient) -> None:
    assert client.patch("/api/rules/RN-12", json={"weight": 3}).status_code == 409


@pytest.mark.parametrize("weight", [-1, 11])
def test_weight_out_of_range_is_422(client: TestClient, weight: int) -> None:
    assert client.patch("/api/rules/RN-17", json={"weight": weight}).status_code == 422


def test_an_empty_change_is_422(client: TestClient) -> None:
    assert client.patch("/api/rules/RN-17", json={}).status_code == 422


def test_unknown_rule_is_404(client: TestClient) -> None:
    assert client.patch("/api/rules/RN-99", json={"enabled": False}).status_code == 404
