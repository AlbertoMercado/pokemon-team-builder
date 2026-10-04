"""Catalogue of rules and the user's settings (CA-10, RF-06, RF-07, RN-04)."""

import pytest

from core.rules.catalog import CATALOG, RuleKind, RuleSettings, SettingsError

CONFIGURABLE = {
    "RN-06",
    "RN-07",
    "RN-11",
    "RN-12",
    "RN-13",
    "RN-14",
    "RN-15",
    "RN-16",
    "RN-17",
    "RN-20",
}


def test_catalog_has_every_rule_of_the_ddf() -> None:
    assert list(CATALOG) == [f"RN-{n:02d}" for n in range(1, 21)]


def test_configurable_rules_are_the_ones_of_the_ddf() -> None:
    """RF-06 and RF-07: optional hard rules and soft rules."""
    assert {r.rule_id for r in CATALOG.values() if r.configurable} == CONFIGURABLE


@pytest.mark.rn("RN-04")
def test_default_weights() -> None:
    """CA-05 and CA-37: RN-17 = 10, RN-20 = 5, RN-15 = 3 and RN-06 = 1."""
    settings = RuleSettings.defaults()
    soft = {r.rule_id for r in CATALOG.values() if r.kind is RuleKind.SOFT}
    assert soft == {"RN-06", "RN-15", "RN-17", "RN-20"}
    assert {rule: settings.weight(rule) for rule in soft} == {
        "RN-17": 10,
        "RN-20": 5,
        "RN-15": 3,
        "RN-06": 1,
    }


def test_every_rule_is_active_by_default() -> None:
    """CA-41."""
    settings = RuleSettings.defaults()
    assert all(settings.is_enabled(rule_id) for rule_id in CATALOG)
    assert settings.active_soft_rules() == ("RN-06", "RN-15", "RN-17", "RN-20")


def test_switching_rules_off_and_on() -> None:
    defaults = RuleSettings.defaults()
    changed = defaults.with_changes(enabled={"RN-12": False, "RN-17": False})

    assert not changed.is_enabled("RN-12")
    assert changed.active_soft_rules() == ("RN-06", "RN-15", "RN-20")
    assert changed.with_changes(enabled={"RN-12": True}).is_enabled("RN-12")
    assert defaults.is_enabled("RN-12")  # the original is not modified


@pytest.mark.rn("RN-04")
def test_changing_weights() -> None:
    settings = RuleSettings.defaults().with_changes(weights={"RN-15": 0, "RN-17": 7})
    assert (settings.weight("RN-15"), settings.weight("RN-17")) == (0, 7)


@pytest.mark.parametrize(
    ("enabled", "message"),
    [({"RN-01": False}, "no se puede desactivar"), ({"RN-99": False}, "no existe")],
)
def test_invalid_activation_changes_are_rejected(enabled: dict[str, bool], message: str) -> None:
    with pytest.raises(SettingsError, match=message):
        RuleSettings.defaults().with_changes(enabled=enabled)


@pytest.mark.parametrize(
    ("weights", "message"),
    [
        ({"RN-12": 5}, "no es blanda"),
        ({"RN-17": 11}, "entre 0 y 10"),
        ({"RN-17": -1}, "entre 0 y 10"),
    ],
)
def test_invalid_weight_changes_are_rejected(weights: dict[str, int], message: str) -> None:
    with pytest.raises(SettingsError, match=message):
        RuleSettings.defaults().with_changes(weights=weights)
