"""Keys of user.sqlite checked before replacing reference.sqlite (ADR-0003)."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, select

from db import user
from db.reference import (
    Game,
    GameMechanic,
    GamePokemon,
    Generation,
    Origin,
    Pokemon,
    ReferenceModel,
    Species,
    VersionGroup,
)
from db.sqlite import create_sqlite_engine
from db.user import FactConfirmation, Favorite, HallOfFameEntry, HallOfFameMember, value_hash
from ingest import cli
from ingest.load import build_reference

NOW = datetime(2026, 10, 4, tzinfo=UTC)


@dataclass
class _Source:
    row_list: list[ReferenceModel]
    name: str = "reference"
    pokeapi_commit: str | None = None

    def rows(self) -> Iterable[ReferenceModel]:
        return list(self.row_list)


def _reference_rows(*pokemon: str) -> list[ReferenceModel]:
    """FireRed with the given forms, each one in the game, and a mechanic."""
    rows: list[ReferenceModel] = [
        Generation(number=3, slug="generation-iii"),
        VersionGroup(slug="firered-leafgreen", generation=3, order=11),
        Game(
            slug="firered",
            name_es="Rojo Fuego",
            version_group="firered-leafgreen",
            generation=3,
            release_order=10,
            has_breeding=True,
            is_target=True,
        ),
        GameMechanic(
            game="firered",
            mechanic="contests",
            value=False,
            origin=Origin.INFERRED,
            fact_key="mechanic:firered:contests",
        ),
    ]
    for number, slug in enumerate(pokemon, start=1):
        rows += [
            Species(
                slug=slug,
                dex_number=number,
                name_es=slug.title(),
                generation=3,
                evolution_chain=number,
                is_baby=False,
                is_legendary=False,
                is_mythical=False,
            ),
            Pokemon(
                slug=slug,
                species=slug,
                name_es=slug.title(),
                is_default=True,
                pokeapi_id=number,
            ),
            GamePokemon(
                game="firered",
                pokemon=slug,
                exists_in_game=True,
                exists_origin=Origin.AUTOMATIC,
                can_arrive=True,
                arrival_origin=Origin.INFERRED,
            ),
        ]
    return rows


def _user_database(
    path: Path,
    *,
    favorites: Iterable[str] = (),
    hall_of_fame: Iterable[tuple[str, list[str]]] = (),
    confirmations: Iterable[str] = (),
) -> Path:
    """A migrated user.sqlite with the given favourites, entries and confirmed fact keys."""
    user.upgrade(path)
    engine = create_sqlite_engine(path)
    with Session(engine) as session:
        session.add_all(Favorite(pokemon=slug, added_at=NOW) for slug in favorites)
        for sequence, (game, members) in enumerate(hall_of_fame, start=1):
            entry = HallOfFameEntry(
                game=game, completed_on=date(2026, 5, sequence), sequence=sequence
            )
            session.add(entry)
            session.flush()
            assert entry.id is not None
            session.add_all(
                HallOfFameMember(entry=entry.id, position=i, pokemon=p, types=["normal"])
                for i, p in enumerate(members, start=1)
            )
        session.add_all(
            FactConfirmation(
                fact_key=key,
                game="firered",
                confirmed_value=True,
                proposed_value_hash=value_hash(True),
                confirmed_at=NOW,
            )
            for key in confirmations
        )
        session.commit()
    engine.dispose()
    return path


def _load(tmp_path: Path, user_database: Path, *pokemon: str) -> tuple[bool, str, Path]:
    target = tmp_path / "reference.sqlite"
    report = build_reference([_Source(_reference_rows(*pokemon))], target, (), user_database)
    return report.succeeded, report.render(), target


def _forms(path: Path) -> list[str]:
    engine = create_sqlite_engine(path)
    with Session(engine) as session:
        found = list(session.exec(select(Pokemon.slug)))
    engine.dispose()
    return found


def test_a_load_without_user_database_is_accepted(tmp_path: Path) -> None:
    """Before the API has ever run there is nothing to check."""
    succeeded, _, target = _load(tmp_path, tmp_path / "user.sqlite", "gengar")
    assert succeeded
    assert target.exists()
    assert not (tmp_path / "user.sqlite").exists()  # the load does not create it


def test_a_load_that_keeps_every_key_is_accepted(tmp_path: Path) -> None:
    database = _user_database(
        tmp_path / "user.sqlite",
        favorites=["gengar"],
        hall_of_fame=[("firered", ["gengar", "haunter"])],
        confirmations=["mechanic:firered:contests", "pokemon:firered:gengar:arrival"],
    )
    succeeded, rendered, _ = _load(tmp_path, database, "gengar", "haunter")
    assert succeeded
    assert "Avisos" not in rendered


def test_a_missing_favourite_rejects_the_load(tmp_path: Path) -> None:
    """The previous database is kept, and the report says which favourites and what to do."""
    database = _user_database(tmp_path / "user.sqlite", favorites=["gengar", "vulpix-alola"])
    assert _load(tmp_path, database, "gengar", "vulpix-alola")[0]

    succeeded, rendered, target = _load(tmp_path, database, "gengar")
    assert not succeeded
    assert (
        "Datos del usuario: Favoritos que no existen en la nueva carga: vulpix-alola." in rendered
    )
    assert "Quítalos de favoritos" in rendered
    assert _forms(target) == ["gengar", "vulpix-alola"]  # the previous load
    assert not target.with_name("reference.sqlite.tmp").exists()


def test_missing_hall_of_fame_games_and_members_reject_the_load(tmp_path: Path) -> None:
    database = _user_database(
        tmp_path / "user.sqlite",
        hall_of_fame=[("firered", ["gengar", "missingno"]), ("sapphire", ["gengar"])],
    )
    succeeded, rendered, target = _load(tmp_path, database, "gengar")
    assert not succeeded
    assert "con un juego que no existe en la nueva carga: 2 (sapphire)" in rendered
    assert "con Pokémon que no existen en la nueva carga: 1 (missingno)" in rendered
    assert not target.exists()


def test_confirmations_of_missing_data_are_only_warnings(tmp_path: Path) -> None:
    """They answer a question that is no longer asked: the API ignores them."""
    database = _user_database(
        tmp_path / "user.sqlite",
        confirmations=["pokemon:firered:raichu:arrival", "battle:firered:brock"],
    )
    succeeded, rendered, _ = _load(tmp_path, database, "gengar")
    assert succeeded
    assert (
        "Confirmaciones de datos que ya no existen en la nueva carga (se ignorarán): "
        "battle:firered:brock, pokemon:firered:raichu:arrival"
    ) in rendered


def test_warnings_are_also_shown_when_the_load_fails(tmp_path: Path) -> None:
    database = _user_database(
        tmp_path / "user.sqlite", favorites=["missingno"], confirmations=["battle:firered:brock"]
    )
    succeeded, rendered, _ = _load(tmp_path, database, "gengar")
    assert not succeeded
    assert "Avisos:\n  - Confirmaciones de datos que ya no existen" in rendered


def test_long_lists_are_shortened(tmp_path: Path) -> None:
    favorites = [f"form-{i:02d}" for i in range(12)]
    database = _user_database(tmp_path / "user.sqlite", favorites=favorites)
    _, rendered, _ = _load(tmp_path, database, "gengar")
    assert "form-09 y 2 más" in rendered


def test_a_user_database_without_tables_has_nothing_to_check(tmp_path: Path) -> None:
    database = tmp_path / "user.sqlite"
    database.touch()
    assert _load(tmp_path, database, "gengar")[0]


def test_the_cli_checks_the_user_database_of_the_data_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _user_database(data_dir / "user.sqlite", favorites=["vulpix-alola"])
    monkeypatch.setattr(cli, "FIRST_LOAD_CHECKS", ())
    monkeypatch.setattr(
        cli, "default_sources", lambda data_dir, offline: [_Source(_reference_rows("gengar"))]
    )
    monkeypatch.setattr(cli, "default_sprites", lambda data_dir, offline: None)
    monkeypatch.setattr(cli, "default_covers", lambda data_dir, offline: None)
    assert cli.main(["--data-dir", str(data_dir)]) == 1
    assert "Favoritos que no existen en la nueva carga: vulpix-alola" in capsys.readouterr().out
    assert not (data_dir / "reference.sqlite").exists()
