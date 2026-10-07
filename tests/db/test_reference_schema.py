"""Schema of reference.sqlite: tables, round trip of a minimal FireRed dataset and the
integrity constraints that reject inconsistent data (docs/02-ddt/modelo-datos.md)."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from db.reference import (
    BattleCategory,
    EvolutionStep,
    Game,
    GameMechanic,
    GamePokemon,
    Generation,
    IngestRun,
    KeyBattle,
    KeyBattlePokemon,
    Origin,
    Pokemon,
    PokemonType,
    ReferenceModel,
    Species,
    SpeciesEggGroup,
    Type,
    TypeEfficacy,
    VersionGroup,
    create_reference_schema,
    missing_columns,
)
from db.sqlite import create_sqlite_engine

DOCUMENTED_TABLES = {
    "generation",
    "version_group",
    "game",
    "game_mechanic",
    "game_pokemon",
    "game_starter",
    "type",
    "type_efficacy",
    "species",
    "species_egg_group",
    "pokemon",
    "pokemon_type",
    "evolution_step",
    "key_battle",
    "key_battle_pokemon",
    "ingest_run",
}


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    engine = create_sqlite_engine(tmp_path / "reference.sqlite")
    create_reference_schema(engine)
    return engine


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        _insert(session, *_firered_base())
        session.commit()
        yield session


def _insert(session: Session, *rows: ReferenceModel) -> None:
    """Insert rows in the given order.

    The models declare foreign keys but no relationships, so SQLAlchemy does not reorder
    inserts by dependency: parents must come first.
    """
    for row in rows:
        session.add(row)
        session.flush()


def _firered_base() -> list[ReferenceModel]:
    """Minimal consistent data: FireRed with Bulbasaur, Ivysaur and two types."""
    return [
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
        Type(slug="grass", name_es="Planta", generation=3),
        Type(slug="poison", name_es="Veneno", generation=3),
        Species(
            slug="bulbasaur",
            dex_number=1,
            name_es="Bulbasaur",
            generation=3,
            evolution_chain=1,
            is_baby=False,
            is_legendary=False,
            is_mythical=False,
        ),
        Species(
            slug="ivysaur",
            dex_number=2,
            name_es="Ivysaur",
            generation=3,
            evolves_from="bulbasaur",
            evolution_chain=1,
            is_baby=False,
            is_legendary=False,
            is_mythical=False,
        ),
        Pokemon(
            slug="bulbasaur",
            species="bulbasaur",
            name_es="Bulbasaur",
            is_default=True,
            pokeapi_id=1,
        ),
        Pokemon(
            slug="ivysaur", species="ivysaur", name_es="Ivysaur", is_default=True, pokeapi_id=2
        ),
    ]


def test_schema_has_the_documented_tables(engine: Engine) -> None:
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'"))
        assert {row[0] for row in rows} == DOCUMENTED_TABLES


def test_a_current_schema_misses_no_column(engine: Engine) -> None:
    assert missing_columns(engine) == []


def test_missing_tables_and_columns_of_an_older_file_are_listed(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE pokemon DROP COLUMN image"))
        connection.execute(text("ALTER TABLE ingest_run DROP COLUMN sprites_commit"))
        connection.execute(text("DROP TABLE key_battle_pokemon"))

    assert sorted(missing_columns(engine)) == [
        "ingest_run.sprites_commit",
        "key_battle_pokemon",
        "pokemon.image",
    ]


def test_reference_tables_are_not_in_the_default_metadata() -> None:
    """user.sqlite models will use their own metadata: creating one schema never creates
    the tables of the other (ADR-0003)."""
    assert not set(SQLModel.metadata.tables) & DOCUMENTED_TABLES


def test_round_trip_of_a_minimal_firered_dataset(session: Session) -> None:
    _insert(
        session,
        *[
            SpeciesEggGroup(species="bulbasaur", egg_group="monster"),
            PokemonType(pokemon="bulbasaur", generation=3, slot=1, type="grass"),
            PokemonType(pokemon="bulbasaur", generation=3, slot=2, type="poison"),
            TypeEfficacy(generation=3, attacking="grass", defending="poison", factor=50),
            EvolutionStep(
                version_group="firered-leafgreen",
                from_pokemon="bulbasaur",
                to_pokemon="ivysaur",
                trigger="level-up",
                conditions={"minimum_level": 16},
            ),
            GameMechanic(
                game="firered",
                mechanic="day_night_cycle",
                value=False,
                origin=Origin.INFERRED,
                fact_key="mechanic:firered:day_night_cycle",
            ),
            GamePokemon(
                game="firered",
                pokemon="bulbasaur",
                exists_in_game=True,
                exists_origin=Origin.AUTOMATIC,
                can_arrive=None,
                arrival_origin=Origin.PENDING,
            ),
            KeyBattle(
                slug="firered-brock",
                game="firered",
                category=BattleCategory.GYM_LEADER,
                trainer_name="Brock",
                order=1,
                origin=Origin.AUTOMATIC,
                fact_key="battle:firered:brock",
            ),
            KeyBattlePokemon(battle="firered-brock", position=1, pokemon="bulbasaur", level=12),
            IngestRun(
                started_at=datetime(2026, 10, 4, tzinfo=UTC),
                finished_at=datetime(2026, 10, 4, tzinfo=UTC),
                pokeapi_commit="bc92d3b",
                games=["firered"],
                summary={"species": 2},
            ),
        ],
    )
    session.commit()

    step = session.exec(select(EvolutionStep)).one()
    assert step.conditions == {"minimum_level": 16}
    assert session.exec(select(GamePokemon)).one().can_arrive is None
    battle = session.exec(select(KeyBattle)).one()
    assert battle.category is BattleCategory.GYM_LEADER
    assert session.exec(select(IngestRun)).one().games == ["firered"]

    # Enums are stored as their text value, which is what fact keys and the API use.
    stored = session.connection().execute(text("SELECT category, origin FROM key_battle"))
    assert stored.one() == ("gym_leader", "automatic")


def test_foreign_keys_are_enforced(session: Session) -> None:
    session.add(
        Pokemon(slug="missingno", species="missingno", name_es="?", is_default=True, pokeapi_id=0)
    )
    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize(
    ("value", "origin"),
    [
        (None, Origin.INFERRED),  # a proposal needs a value
        (None, Origin.AUTOMATIC),
        (True, Origin.PENDING),  # a pending fact has no value yet
    ],
)
def test_value_is_missing_exactly_when_pending(
    session: Session, value: bool | None, origin: Origin
) -> None:
    session.add(
        GameMechanic(
            game="firered",
            mechanic="day_night_cycle",
            value=value,
            origin=origin,
            fact_key="mechanic:firered:day_night_cycle",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_type_efficacy_factor_is_a_known_value(session: Session) -> None:
    session.add(TypeEfficacy(generation=3, attacking="grass", defending="poison", factor=300))
    with pytest.raises(IntegrityError):
        session.flush()


def test_pokemon_type_has_at_most_two_slots(session: Session) -> None:
    session.add(PokemonType(pokemon="bulbasaur", generation=3, slot=3, type="grass"))
    with pytest.raises(IntegrityError):
        session.flush()
