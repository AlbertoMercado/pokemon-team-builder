"""SQLModel models of reference.sqlite, the read-only reference data built by ingest.

The file is rebuilt from scratch on every load, so it has no migrations (ADR-0003). Tables
and columns are documented in docs/02-ddt/modelo-datos.md.
"""

from sqlalchemy import Engine

from db.reference.base import BattleCategory, Origin, ReferenceModel
from db.reference.battles import KeyBattle, KeyBattlePokemon
from db.reference.evolution import EvolutionStep
from db.reference.games import Game, GameMechanic, GamePokemon, Generation, VersionGroup
from db.reference.meta import IngestRun
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
    "EvolutionStep",
    "Game",
    "GameMechanic",
    "GamePokemon",
    "Generation",
    "IngestRun",
    "KeyBattle",
    "KeyBattlePokemon",
    "Origin",
    "Pokemon",
    "PokemonType",
    "ReferenceModel",
    "Species",
    "SpeciesEggGroup",
    "Type",
    "TypeEfficacy",
    "VersionGroup",
    "create_reference_schema",
]


def create_reference_schema(engine: Engine) -> None:
    """Create every reference.sqlite table in an empty database."""
    ReferenceModel.metadata.create_all(engine)
