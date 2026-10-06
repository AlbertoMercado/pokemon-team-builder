"""Engines and sessions of the two databases, shared by every request.

user.sqlite is migrated when the application starts. reference.sqlite is only opened when a
request needs it: if it does not exist yet, or was built by an older version of the code (it
lacks tables or columns), those requests answer 503 and point to the data load, while the
rest of the API keeps working.
"""

from collections.abc import Iterator
from pathlib import Path

from fastapi import HTTPException, Request, status
from sqlalchemy import Engine
from sqlmodel import Session

from api.config import Settings
from db import user
from db.reference import missing_columns
from db.sqlite import create_sqlite_engine

NO_REFERENCE_DATA = (
    "No hay datos de referencia: ejecuta la carga de datos (uv run python -m ingest) y "
    "reinicia la API"
)
OUTDATED_REFERENCE_DATA = (
    "Los datos de referencia son de una versión anterior de la aplicación: vuelve a ejecutar "
    "la carga de datos (uv run python -m ingest) y reinicia la API"
)


class Databases:
    """The engines of one application. Created at startup; disposed at shutdown."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        user.upgrade(settings.user_path)
        self.user = create_sqlite_engine(settings.user_path)
        self._reference: Engine | None = None

    def reference(self) -> Engine:
        """The engine of reference.sqlite; ``503`` if it has not been loaded or is outdated."""
        if self._reference is None:
            path: Path = self.settings.reference_path
            if not path.exists():
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, NO_REFERENCE_DATA)
            engine = create_sqlite_engine(path)
            if missing_columns(engine):
                engine.dispose()
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, OUTDATED_REFERENCE_DATA)
            self._reference = engine
        return self._reference

    def dispose(self) -> None:
        self.user.dispose()
        if self._reference is not None:
            self._reference.dispose()


def databases(request: Request) -> Databases:
    found: Databases = request.app.state.databases
    return found


def reference_session(request: Request) -> Iterator[Session]:
    """A read-only session of reference.sqlite for one request."""
    with Session(databases(request).reference()) as session:
        yield session


def user_session(request: Request) -> Iterator[Session]:
    """A session of user.sqlite for one request."""
    with Session(databases(request).user) as session:
        yield session
