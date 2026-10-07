"""Dependencies shared by the routers: the database sessions, the data directory, the cache of
game data and the path parameters used by several routers, with their description for the
OpenAPI contract (the reference of the API, ADR-0012)."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from fastapi import Path as PathParam
from sqlmodel import Session

from api.database import databases, reference_session, user_session
from api.services.context import GameReference, GameReferences

UserDb = Annotated[Session, Depends(user_session)]
ReferenceDb = Annotated[Session, Depends(reference_session)]
PokemonSlug = Annotated[
    str, PathParam(description="Identificador de la forma, p. ej. `vulpix-alola` (RN-05).")
]
GameSlug = Annotated[str, PathParam(description="Identificador del juego, p. ej. `firered`.")]


def data_dir(request: Request) -> Path:
    """The data directory: reference.sqlite, user.sqlite and the cache of the images."""
    return databases(request).settings.data_dir


DataDir = Annotated[Path, Depends(data_dir)]


def game_references(request: Request) -> GameReferences:
    """The application's cache, created at startup (``api.main``)."""
    found: GameReferences = request.app.state.game_references
    return found


def target_game(
    game: GameSlug,
    reference: ReferenceDb,
    references: Annotated[GameReferences, Depends(game_references)],
) -> GameReference:
    """The reference data of the path's ``{game}``: ``404`` if it is not a target game."""
    return references.get(reference, game)


TargetGame = Annotated[GameReference, Depends(target_game)]
