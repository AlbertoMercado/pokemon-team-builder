"""SQLModel models of reference.sqlite, the read-only reference data built by ingest.

The file is rebuilt from scratch on every load, so it has no migrations (ADR-0003). A file
built by an older version may lack tables or columns: ``missing_columns`` tells, so that the
API can ask for a new load instead of failing. Tables and columns are documented in
docs/02-ddt/modelo-datos.md.
"""

from sqlalchemy import Engine, inspect

from db.reference.base import BattleCategory, Origin, ReferenceModel
from db.reference.battles import KeyBattle, KeyBattlePokemon
from db.reference.evolution import EvolutionStep
from db.reference.games import (
    Game,
    GameMechanic,
    GamePokemon,
    GameStarter,
    Generation,
    VersionGroup,
)
from db.reference.meta import IngestRun
from db.reference.pokedex import (
    Encounter,
    EventPokemon,
    GamePokedex,
    GameTransfer,
    Location,
    Pokedex,
    PokedexNumber,
)
from db.reference.pokemon import (
    Pokemon,
    PokemonType,
    Species,
    SpeciesEggGroup,
    Type,
    TypeEfficacy,
)

__all__ = [
    "BattleCategory",
    "Encounter",
    "EventPokemon",
    "EvolutionStep",
    "Game",
    "GameMechanic",
    "GamePokedex",
    "GamePokemon",
    "GameStarter",
    "GameTransfer",
    "Generation",
    "IngestRun",
    "KeyBattle",
    "KeyBattlePokemon",
    "Location",
    "Origin",
    "Pokedex",
    "PokedexNumber",
    "Pokemon",
    "PokemonType",
    "ReferenceModel",
    "Species",
    "SpeciesEggGroup",
    "Type",
    "TypeEfficacy",
    "VersionGroup",
    "create_reference_schema",
    "missing_columns",
]


def create_reference_schema(engine: Engine) -> None:
    """Create every reference.sqlite table in an empty database."""
    ReferenceModel.metadata.create_all(engine)


def missing_columns(engine: Engine) -> list[str]:
    """Tables and columns of the models that the database lacks, as ``table.column``.

    Empty if the file was built by this version of the code (or a compatible one).
    """
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing: list[str] = []
    for table in ReferenceModel.metadata.sorted_tables:
        if table.name not in existing:
            missing.append(table.name)
            continue
        columns = {column["name"] for column in inspector.get_columns(table.name)}
        missing.extend(f"{table.name}.{c.name}" for c in table.columns if c.name not in columns)
    return missing
