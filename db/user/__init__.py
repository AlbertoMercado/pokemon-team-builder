"""SQLModel models and Alembic migrations of user.sqlite, written only by the API (ADR-0003).

``upgrade(path)`` brings a database to the latest migration, creating the file if needed.
Tables and columns are documented in docs/02-ddt/modelo-datos.md.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

from db.sqlite import create_sqlite_engine
from db.user.models import (
    FactConfirmation,
    Favorite,
    HallOfFameEntry,
    HallOfFameMember,
    RuleSetting,
    UserModel,
)
from db.user.values import ConfirmedValue, value_hash

MIGRATIONS = Path(__file__).resolve().parent / "migrations"

__all__ = [
    "MIGRATIONS",
    "ConfirmedValue",
    "FactConfirmation",
    "Favorite",
    "HallOfFameEntry",
    "HallOfFameMember",
    "RuleSetting",
    "UserModel",
    "alembic_config",
    "upgrade",
    "value_hash",
]


def alembic_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    return config


def upgrade(path: Path) -> None:
    """Apply every pending migration to the user.sqlite at ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_sqlite_engine(path)
    try:
        with engine.begin() as connection:
            config = alembic_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
    finally:
        engine.dispose()
