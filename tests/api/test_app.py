"""Start-up of the API, data directory, /api/meta and the OpenAPI contract."""

import json
import tomllib
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

from api import openapi
from api.config import DATA_DIR_VARIABLE, Settings
from api.database import NO_REFERENCE_DATA, OUTDATED_REFERENCE_DATA
from db.sqlite import create_sqlite_engine
from tests.api.conftest import ClientFactory
from tests.api.factories import reference_database


def _version() -> str:
    with Path("pyproject.toml").open("rb") as file:
        version: str = tomllib.load(file)["project"]["version"]
    return version


def test_startup_creates_and_migrates_user_sqlite(
    make_client: ClientFactory, data_dir: Path
) -> None:
    make_client()
    engine = create_sqlite_engine(data_dir / "user.sqlite")
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert {
        "favorite",
        "rule_setting",
        "hall_of_fame_entry",
        "hall_of_fame_member",
        "fact_confirmation",
        "alembic_version",
    } <= tables


def test_without_reference_data_meta_answers_503(make_client: ClientFactory) -> None:
    response = make_client().get("/api/meta")
    assert response.status_code == 503
    assert response.json() == {"detail": NO_REFERENCE_DATA}


def test_reference_data_of_an_older_version_answers_503(
    make_client: ClientFactory, data_dir: Path
) -> None:
    """A file built before a new column (pokemon.image) asks for a new load, not a 500."""
    data_dir.mkdir(parents=True)
    reference_database(data_dir)
    engine = create_sqlite_engine(data_dir / "reference.sqlite")
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE pokemon DROP COLUMN image"))
    engine.dispose()

    response = make_client().get("/api/meta")

    assert response.status_code == 503
    assert response.json() == {"detail": OUTDATED_REFERENCE_DATA}


def test_meta_gives_the_versions_of_the_app_and_the_data(
    make_client: ClientFactory, data_dir: Path
) -> None:
    data_dir.mkdir(parents=True)
    reference_database(data_dir)
    response = make_client().get("/api/meta")
    assert response.status_code == 200
    assert response.json() == {
        "app_version": _version(),
        "data": {
            "pokeapi_commit": "bc92d3b",
            "ingested_at": "2026-10-04T10:00:00Z",
            "games": ["firered", "leafgreen"],
        },
    }


def test_reference_data_loaded_after_startup_is_found(
    make_client: ClientFactory, data_dir: Path
) -> None:
    """The API opens reference.sqlite on demand: a first load does not need a restart."""
    client = make_client()
    assert client.get("/api/meta").status_code == 503
    reference_database(data_dir)
    assert client.get("/api/meta").status_code == 200


def test_restarting_keeps_user_sqlite(make_client: ClientFactory, data_dir: Path) -> None:
    """Migrations are applied again on every start, without changes or errors."""
    make_client()
    make_client()
    assert (data_dir / "user.sqlite").exists()


def test_openapi_and_docs_are_published(make_client: ClientFactory) -> None:
    client = make_client()
    openapi = client.get("/api/openapi.json").json()
    assert openapi["info"]["version"] == _version()
    assert "/api/meta" in openapi["paths"]
    assert client.get("/api/docs").status_code == 200


def test_data_dir_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DATA_DIR_VARIABLE, "/tmp/otros-datos")
    assert Settings.from_environment().data_dir == Path("/tmp/otros-datos")
    monkeypatch.delenv(DATA_DIR_VARIABLE)
    assert Settings.from_environment().data_dir == Path("data")


def test_openapi_export_matches_the_published_contract(
    make_client: ClientFactory, tmp_path: Path
) -> None:
    """``python -m api.openapi`` writes the same contract the API serves, for the web client."""
    target = tmp_path / "out" / "openapi.json"
    openapi.main([str(target)])
    assert json.loads(target.read_text(encoding="utf-8")) == (
        make_client().get("/api/openapi.json").json()
    )
    assert openapi.contract() == target.read_text(encoding="utf-8")
