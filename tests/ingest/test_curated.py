"""Curated data (data/curated/*.yaml): schemas, the real files and the curated source
(ADR-0005, docs/02-ddt/datos-curados.md)."""

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from db.reference import BattleCategory, GameMechanic, KeyBattle, Origin
from ingest import cli
from ingest.sources.curated import CuratedDataError, CuratedSource, read_curated
from ingest.sources.curated.schemas import (
    ArrivalRule,
    BreedingFile,
    GamesFile,
    KeyBattlesFile,
    MechanicValue,
)

CURATED_DIR = Path(__file__).resolve().parents[2] / "data" / "curated"


def test_repository_curated_files_are_valid() -> None:
    curated = read_curated(CURATED_DIR)

    assert curated.breeding.incense_babies == {"azurill": "sea-incense", "wynaut": "lax-incense"}
    assert set(curated.games.games) == {"firered", "leafgreen"}
    assert set(curated.arrival.games) == {"firered", "leafgreen"}
    [firered_leafgreen] = curated.key_battles
    assert firered_leafgreen.games == ["firered", "leafgreen"]
    assert len(firered_leafgreen.battles) == 15


# --- Schemas -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "origin"),
    [(None, "inferred"), (None, "automatic"), (True, "pending")],
)
def test_mechanic_value_is_missing_exactly_when_pending(value: bool | None, origin: str) -> None:
    with pytest.raises(ValidationError, match="pending"):
        MechanicValue.model_validate({"value": value, "origin": origin})


def test_unknown_mechanic_is_rejected() -> None:
    entry = {"value": True, "origin": "inferred"}
    with pytest.raises(ValidationError):
        GamesFile.model_validate({"games": {"firered": {"weather": entry}}})


def test_unknown_keys_are_rejected() -> None:
    """A typo in a curated file must not be silently ignored."""
    with pytest.raises(ValidationError):
        BreedingFile.model_validate({"incense_babies": {}, "incence_babies": {}})


@pytest.mark.parametrize(
    "rule",
    [
        {"origin": "inferred"},  # a proposal needs a Pokédex
        {"regional_pokedex": "kanto", "origin": "pending"},
    ],
)
def test_arrival_rule_pokedex_matches_its_origin(rule: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="pending"):
        ArrivalRule.model_validate(rule)


def test_key_battle_ids_are_unique_and_valid() -> None:
    battle = {"id": "brock", "category": "gym_leader", "trainer": "Brock", "wikidex_page": "Brock"}
    with pytest.raises(ValidationError, match="repetidos"):
        KeyBattlesFile.model_validate({"games": ["firered"], "battles": [battle, battle]})
    with pytest.raises(ValidationError):
        KeyBattlesFile.model_validate(
            {"games": ["firered"], "battles": [{**battle, "id": "Brock Pewter"}]}
        )


def test_invalid_file_names_the_file(tmp_path: Path) -> None:
    shutil.copytree(CURATED_DIR, tmp_path / "curated")
    (tmp_path / "curated" / "breeding.yaml").write_text("incense_babies: [azurill]\n")

    with pytest.raises(CuratedDataError, match=r"breeding\.yaml"):
        read_curated(tmp_path / "curated")


# --- Curated source ------------------------------------------------------------------------


def test_curated_source_rows() -> None:
    rows = list(CuratedSource(read_curated(CURATED_DIR)).rows())
    mechanics = [row for row in rows if isinstance(row, GameMechanic)]
    battles = [row for row in rows if isinstance(row, KeyBattle)]

    assert len(mechanics) == 4
    day_night = next(m for m in mechanics if m.fact_key == "mechanic:firered:day_night_cycle")
    assert (day_night.value, day_night.origin) == (False, Origin.INFERRED)

    assert len(battles) == 30
    firered = sorted((b for b in battles if b.game == "firered"), key=lambda b: b.order)
    assert [b.order for b in firered] == list(range(1, 16))
    assert (firered[0].slug, firered[0].fact_key) == ("firered-brock", "battle:firered:brock")
    assert firered[-1].category is BattleCategory.CHAMPION
    # Teams are read from WikiDex in phase 5: until then every battle is pending (RN-18).
    assert all(b.origin is Origin.PENDING for b in battles)


def test_cli_reports_invalid_curated_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    curated = tmp_path / "curated"
    shutil.copytree(CURATED_DIR, curated)
    (curated / "arrival.yaml").write_text("games:\n  firered:\n    origin: inferred\n")
    monkeypatch.setattr(cli, "CURATED_DIR", curated)

    exit_code = cli.main(["--data-dir", str(tmp_path / "data"), "--offline"])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "ERROR en los datos curados" in output
    assert "arrival.yaml" in output
