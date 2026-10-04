"""Load phase of the ingest: build reference.sqlite, report it and replace the previous file
only when everything is consistent (RF-11, docs/05-operacion/ingesta.md)."""

import shutil
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from sqlmodel import Session, select

from db.reference import (
    Game,
    GamePokemon,
    Generation,
    IngestRun,
    Origin,
    Pokemon,
    ReferenceModel,
    Species,
    VersionGroup,
)
from db.sqlite import create_sqlite_engine
from ingest import cli
from ingest.load import build_reference

POKEAPI_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "pokeapi"


@dataclass
class FakeSource:
    """In-memory source that yields the given rows, or fails if ``error`` is set."""

    row_list: list[ReferenceModel]
    name: str = "fake"
    pokeapi_commit: str | None = None
    error: Exception | None = field(default=None)

    def rows(self) -> Iterable[ReferenceModel]:
        if self.error is not None:
            raise self.error
        return list(self.row_list)


def _species(slug: str, number: int, evolves_from: str | None = None) -> Species:
    return Species(
        slug=slug,
        dex_number=number,
        name_es=slug.capitalize(),
        generation=3,
        evolves_from=evolves_from,
        evolution_chain=1,
        is_baby=False,
        is_legendary=False,
        is_mythical=False,
    )


def _firered_rows() -> list[ReferenceModel]:
    """Rows deliberately out of dependency order: the loader must not care."""
    return [
        GamePokemon(
            game="firered",
            pokemon="ivysaur",
            exists_in_game=True,
            exists_origin=Origin.AUTOMATIC,
            can_arrive=None,
            arrival_origin=Origin.PENDING,
        ),
        Pokemon(slug="ivysaur", species="ivysaur", name_es="Ivysaur", is_default=True),
        _species("ivysaur", 2, evolves_from="bulbasaur"),
        _species("bulbasaur", 1),
        Game(
            slug="firered",
            name_es="Rojo Fuego",
            version_group="firered-leafgreen",
            generation=3,
            release_order=10,
            has_breeding=True,
            is_target=True,
        ),
        VersionGroup(slug="firered-leafgreen", generation=3, order=11),
        Generation(number=3, slug="generation-iii"),
    ]


def _read_ingest_run(path: Path) -> IngestRun:
    engine = create_sqlite_engine(path)
    try:
        with Session(engine) as session:
            return session.exec(select(IngestRun)).one()
    finally:
        engine.dispose()


def test_builds_the_database_from_rows_in_any_order(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    source = FakeSource(_firered_rows(), pokeapi_commit="bc92d3b")

    report = build_reference([source], target)

    assert report.succeeded, report.errors
    assert target.exists()
    assert not (tmp_path / "reference.sqlite.tmp").exists()
    assert report.rows_by_table["species"] == 2
    assert report.rows_by_table["game"] == 1
    assert "ingest_run" not in report.rows_by_table


def test_records_the_ingest_run(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    build_reference([FakeSource(_firered_rows(), pokeapi_commit="bc92d3b")], target)

    run = _read_ingest_run(target)
    assert run.pokeapi_commit == "bc92d3b"
    assert run.games == ["firered"]
    assert run.summary["species"] == 2
    assert run.started_at <= run.finished_at


def test_reports_reviewable_values_by_origin(tmp_path: Path) -> None:
    """The administrator sees how much the user will have to confirm (RN-18)."""
    report = build_reference([FakeSource(_firered_rows())], tmp_path / "reference.sqlite")

    assert report.origins_by_table == {"game_pokemon": {"automatic": 1, "pending": 1}}
    rendered = report.render()
    assert "game_pokemon" in rendered
    assert "pending 1" in rendered


def _build_previous(target: Path) -> bytes:
    report = build_reference([FakeSource(_firered_rows())], target)
    assert report.succeeded
    return target.read_bytes()


def test_dangling_reference_keeps_the_previous_database(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    previous = _build_previous(target)
    orphan = Pokemon(slug="missingno", species="missingno", name_es="?", is_default=True)

    report = build_reference([FakeSource([*_firered_rows(), orphan])], target)

    assert not report.succeeded
    assert "pokemon.species → species: missingno" in report.errors[0]
    assert target.read_bytes() == previous
    assert not (tmp_path / "reference.sqlite.tmp").exists()


def test_failing_source_keeps_the_previous_database(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    previous = _build_previous(target)
    broken = FakeSource([], error=ValueError("CSV sin la columna identifier"))

    report = build_reference([FakeSource(_firered_rows()), broken], target)

    assert report.errors == ["ValueError: CSV sin la columna identifier"]
    assert target.read_bytes() == previous
    assert "se conserva la base de datos anterior" in report.render()


def test_sources_from_different_pokeapi_commits_are_rejected(tmp_path: Path) -> None:
    sources = [
        FakeSource(_firered_rows(), pokeapi_commit="aaaaaaa"),
        FakeSource([], pokeapi_commit="bbbbbbb"),
    ]

    report = build_reference(sources, tmp_path / "reference.sqlite")

    assert not report.succeeded
    assert "varios commits de PokeAPI" in report.errors[0]


def _data_dir_with_fixture_cache(tmp_path: Path) -> Path:
    """Data directory whose PokeAPI cache already has the test extract (no download)."""
    data_dir = tmp_path / "data"
    shutil.copytree(POKEAPI_FIXTURES, data_dir / "cache" / "pokeapi")
    return data_dir


def test_cli_builds_reference_in_the_data_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # The extract has ~45 species, so the checks of the full first load are disabled here.
    monkeypatch.setattr(cli, "FIRST_LOAD_CHECKS", ())
    data_dir = _data_dir_with_fixture_cache(tmp_path)

    exit_code = cli.main(["--data-dir", str(data_dir), "--offline"])

    assert exit_code == 0
    assert (data_dir / "reference.sqlite").exists()
    assert "Carga completada." in capsys.readouterr().out


def test_cli_fails_when_the_checks_fail(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data_dir = _data_dir_with_fixture_cache(tmp_path)

    exit_code = cli.main(["--data-dir", str(data_dir), "--offline"])

    assert exit_code == 1
    assert not (data_dir / "reference.sqlite").exists()
    assert "Comprobación fallida: species" in capsys.readouterr().out


def test_cli_offline_without_cache_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(["--data-dir", str(tmp_path / "data"), "--offline"])

    assert exit_code == 1
    assert "no está en la caché" in capsys.readouterr().out
