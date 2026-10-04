"""Schema of user.sqlite: the Alembic migrations match the models, and the integrity
constraints reject inconsistent data (docs/02-ddt/modelo-datos.md)."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from db.sqlite import create_sqlite_engine
from db.user import (
    FactConfirmation,
    Favorite,
    HallOfFameEntry,
    HallOfFameMember,
    RuleSetting,
    UserModel,
    alembic_config,
    upgrade,
    value_hash,
)

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)


@pytest.fixture
def path(tmp_path: Path) -> Path:
    database = tmp_path / "datos" / "user.sqlite"
    upgrade(database)
    return database


@pytest.fixture
def engine(path: Path) -> Iterator[Engine]:
    created = create_sqlite_engine(path)
    yield created
    created.dispose()


def test_upgrade_creates_the_file_and_reaches_the_last_revision(engine: Engine) -> None:
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    with engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == head
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert tables == set(UserModel.metadata.tables)


def test_migrations_match_the_models(engine: Engine) -> None:
    """Nothing left for autogenerate: the models have no change without its migration."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, UserModel.metadata) == []


def test_upgrade_twice_changes_nothing(path: Path, engine: Engine) -> None:
    with Session(engine) as session:
        session.add(Favorite(pokemon="dragonite", added_at=NOW))
        session.commit()
    upgrade(path)
    with Session(engine) as session:
        assert session.exec(select(Favorite.pokemon)).all() == ["dragonite"]


def test_downgrade_removes_every_table(path: Path, engine: Engine) -> None:
    config = alembic_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}


def test_round_trip_of_every_table(engine: Engine) -> None:
    with Session(engine) as session:
        entry = HallOfFameEntry(game="leafgreen", completed_on=date(2026, 9, 1), sequence=1)
        session.add_all(
            [
                Favorite(pokemon="vulpix-alola", added_at=NOW),
                RuleSetting(rule_id="RN-17", enabled=True, weight=8),
                RuleSetting(rule_id="RN-12", enabled=False),
                entry,
                FactConfirmation(
                    fact_key="battle:firered:brock",
                    game="firered",
                    confirmed_value=["geodude", "onix"],
                    proposed_value_hash=value_hash(["geodude", "onix"]),
                    confirmed_at=NOW,
                ),
            ]
        )
        session.commit()
        assert entry.id is not None
        session.add(
            HallOfFameMember(
                entry=entry.id, position=1, pokemon="gengar", types=["ghost", "poison"]
            )
        )
        session.commit()

    with Session(engine) as session:
        member = session.exec(select(HallOfFameMember)).one()
        assert member.types == ["ghost", "poison"]
        confirmation = session.exec(select(FactConfirmation)).one()
        assert confirmation.confirmed_value == ["geodude", "onix"]
        assert session.get(RuleSetting, "RN-12") == RuleSetting(
            rule_id="RN-12", enabled=False, weight=None
        )


@pytest.mark.parametrize("weight", [-1, 11])
def test_weight_must_be_between_0_and_10(engine: Engine, weight: int) -> None:
    with Session(engine) as session:
        session.add(RuleSetting(rule_id="RN-17", weight=weight))
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("position", [0, 7])
def test_a_team_has_positions_1_to_6(engine: Engine, position: int) -> None:
    with Session(engine) as session:
        entry = HallOfFameEntry(game="firered", completed_on=date(2026, 9, 1), sequence=1)
        session.add(entry)
        session.commit()
        assert entry.id is not None
        session.add(HallOfFameMember(entry=entry.id, position=position, pokemon="a", types=[]))
        with pytest.raises(IntegrityError):
            session.commit()


def test_two_entries_cannot_share_their_sequence(engine: Engine) -> None:
    with Session(engine) as session:
        for game in ("firered", "leafgreen"):
            session.add(HallOfFameEntry(game=game, completed_on=date(2026, 9, 1), sequence=1))
        with pytest.raises(IntegrityError):
            session.commit()


def test_deleting_an_entry_deletes_its_members(engine: Engine) -> None:
    with Session(engine) as session:
        entry = HallOfFameEntry(game="firered", completed_on=date(2026, 9, 1), sequence=1)
        session.add(entry)
        session.commit()
        assert entry.id is not None
        session.add(HallOfFameMember(entry=entry.id, position=1, pokemon="a", types=["normal"]))
        session.commit()
        session.delete(entry)
        session.commit()
        assert session.exec(select(HallOfFameMember)).all() == []


def test_the_hash_of_a_proposal_is_stable_and_tells_values_apart() -> None:
    assert value_hash(True) == value_hash(True)
    assert value_hash(["geodude", "onix"]) == value_hash(["geodude", "onix"])
    hashes = {value_hash(v) for v in (True, False, None, ["geodude"], ["geodude", "onix"])}
    assert len(hashes) == 5
