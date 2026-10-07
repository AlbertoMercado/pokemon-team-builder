"""Only complete games stay as target games after the load (RF-05, CA-67): ``ingest/targets.py``."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlmodel import Session, select

from db.reference import (
    BattleCategory,
    Game,
    GameMechanic,
    GamePokemon,
    GameStarter,
    Generation,
    KeyBattle,
    Origin,
    Pokemon,
    ReferenceModel,
    Species,
    VersionGroup,
    create_reference_schema,
)
from db.sqlite import create_sqlite_engine
from ingest.report import LoadReport
from ingest.sources.curated.schemas import MECHANICS
from ingest.targets import mark_incomplete_games, missing_data


def _game(slug: str, name: str, order: int, *, target: bool = True) -> Game:
    return Game(
        slug=slug,
        name_es=name,
        version_group="group",
        generation=3,
        release_order=order,
        has_breeding=True,
        is_target=target,
    )


def _rows() -> list[ReferenceModel]:
    """FireRed with everything; Ruby with only its Pokémon; Gold, not a target."""
    rows: list[ReferenceModel] = [
        Generation(number=3, slug="generation-iii"),
        VersionGroup(slug="group", generation=3, order=1),
        _game("ruby", "Rubí", 7),
        _game("firered", "Rojo Fuego", 10),
        _game("gold", "Oro", 4, target=False),
        Species(
            slug="venusaur",
            dex_number=3,
            name_es="Venusaur",
            generation=3,
            evolution_chain=1,
            is_baby=False,
            is_legendary=False,
            is_mythical=False,
        ),
        Pokemon(
            slug="venusaur", species="venusaur", name_es="Venusaur", is_default=True, pokeapi_id=3
        ),
    ]
    rows += [
        GamePokemon(
            game=game,
            pokemon="venusaur",
            exists_in_game=True,
            exists_origin=Origin.AUTOMATIC,
            can_arrive=True,
            arrival_origin=Origin.INFERRED,
        )
        for game in ("ruby", "firered")
    ]
    rows += [
        GameMechanic(
            game="firered",
            mechanic=mechanic,
            value=False,
            origin=Origin.INFERRED,
            fact_key=f"mechanic:firered:{mechanic}",
        )
        for mechanic in MECHANICS
    ]
    rows += [
        KeyBattle(
            slug="firered-brock",
            game="firered",
            category=BattleCategory.GYM_LEADER,
            trainer_name="Brock",
            order=1,
            origin=Origin.AUTOMATIC,
            fact_key="battle:firered:brock",
        ),
        GameStarter(game="firered", pokemon="venusaur"),
    ]
    return rows


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_sqlite_engine(tmp_path / "reference.sqlite")
    create_reference_schema(engine)
    with Session(engine) as session:
        for row in _rows():
            session.add(row)
            session.flush()
        session.commit()
        yield session
    engine.dispose()


def _targets(session: Session) -> set[str]:
    return {game.slug for game in session.exec(select(Game)).all() if game.is_target}


def test_a_complete_game_lacks_nothing(session: Session) -> None:
    assert missing_data(session, "firered") == []


def test_an_incomplete_game_says_what_it_lacks_in_the_order_of_rf05(session: Session) -> None:
    assert missing_data(session, "ruby") == [
        "sus mecánicas (RN-15)",
        "sus combates clave (RN-17)",
        "sus iniciales (RN-21)",
    ]


def test_a_game_with_some_mechanics_is_not_complete(session: Session) -> None:
    session.delete(session.exec(select(GameMechanic)).first())
    session.flush()
    assert missing_data(session, "firered") == ["sus mecánicas (RN-15)"]


def test_only_the_complete_games_stay_as_target(session: Session) -> None:
    """CA-67: Ruby stays loaded but cannot be chosen; Gold was never a target."""
    incomplete = mark_incomplete_games(session)
    session.commit()

    assert _targets(session) == {"firered"}
    assert list(incomplete) == ["Rubí"]
    assert session.get(Game, "ruby") is not None


def test_the_report_lists_the_incomplete_games() -> None:
    report = LoadReport(target=Path("reference.sqlite"))
    report.incomplete_games = {"Rubí": ["sus combates clave (RN-17)", "sus iniciales (RN-21)"]}
    assert "  Rubí: faltan sus combates clave (RN-17) y sus iniciales (RN-21)" in report.render()
