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
    "ForeignKeyError",
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


class ForeignKeyError(RuntimeError):
    """The migrations left rows that point to rows that do not exist."""


def upgrade(path: Path) -> None:
    """Apply every pending migration to the user.sqlite at ``path``.

    Batch migrations rebuild a table by copying it and dropping the old one; with foreign keys
    on, that drop deletes the children of an ``ON DELETE CASCADE`` (the members of the Hall of
    Fame). So they are turned off while migrating, outside the transaction because SQLite
    ignores the pragma inside one, and checked before committing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_sqlite_engine(path)
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
            with connection.begin():
                config = alembic_config()
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
                broken = connection.exec_driver_sql("PRAGMA foreign_key_check").all()
                if broken:
                    raise ForeignKeyError(f"Claves foráneas rotas tras migrar: {broken}")
    finally:
        engine.dispose()
