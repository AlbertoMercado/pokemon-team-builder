"""Dependencies shared by the routers: the database sessions, the data directory, the cache of
game data and the path parameters used by several routers, with their description for the
OpenAPI contract (the reference of the API, ADR-0012)."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from fastapi import Path as PathParam
from sqlmodel import Session

from api.database import databases, reference_session, user_session
from api.errors import ConflictError
from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
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


COMPLETED_GAME_MESSAGE = (
    "{name} ya está registrado en el Hall of Fame: cada juego se completa una sola vez. Para "
    "volver a jugarlo, elimina antes su registro"
)


def target_game(
    game: GameSlug,
    reference: ReferenceDb,
    user: UserDb,
    references: Annotated[GameReferences, Depends(game_references)],
) -> GameReference:
    """The reference data of the path's ``{game}``: ``404`` if it is not a target game and
    ``409`` if it is already recorded in the Hall of Fame (CA-68)."""
    target = reference_repo.target_game(reference, game)
    entry = user_repo.completed_games(user).get(game)
    if target is not None and entry is not None:
        raise ConflictError(
            COMPLETED_GAME_MESSAGE.format(name=target.name_es), {"hall_of_fame_entry": entry}
        )
    return references.get(reference, game)


TargetGame = Annotated[GameReference, Depends(target_game)]
