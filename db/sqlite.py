"""SQLite engine factory shared by reference.sqlite and user.sqlite.

SQLite does not enforce foreign keys unless each connection enables them, so every engine
created here turns on ``PRAGMA foreign_keys`` when a connection is opened.
"""

from pathlib import Path

from sqlalchemy import Engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool import ConnectionPoolEntry
from sqlmodel import create_engine


def create_sqlite_engine(path: Path) -> Engine:
    """Create an engine for the SQLite file at ``path`` with foreign keys enforced."""
    engine = create_engine(f"sqlite:///{path}")
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _enable_foreign_keys(
    dbapi_connection: DBAPIConnection, _connection_record: ConnectionPoolEntry
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
