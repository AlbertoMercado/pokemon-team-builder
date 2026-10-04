"""FastAPI application: ``create_app(settings)`` and the ``app`` that uvicorn serves.

    uv run uvicorn api.main:app --reload

Every route is under ``/api``; the OpenAPI contract is at ``/api/openapi.json`` and the
interactive documentation at ``/api/docs`` (docs/02-ddt/api.md).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import errors
from api.config import Settings
from api.database import Databases
from api.routers import favorites, games, meta, review, rules
from api.services.context import GameReferences
from api.services.meta import app_version


def create_app(settings: Settings | None = None) -> FastAPI:
    """The application, with its data directory taken from ``settings`` or the environment."""
    chosen = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.databases = Databases(chosen)
        app.state.game_references = GameReferences()
        yield
        app.state.databases.dispose()

    app = FastAPI(
        title="pokemon-team-builder",
        version=app_version(),
        description="Genera equipos de 6 Pokémon a partir de tus favoritos y de reglas "
        "configurables.",
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
    )
    errors.register(app)
    for router in (favorites.router, rules.router, games.router, review.router, meta.router):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
