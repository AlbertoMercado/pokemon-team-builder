"""Dependencies shared by the routers: the database sessions and the cache of game data."""

from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from api.database import reference_session, user_session
from api.services.context import GameReference, GameReferences

UserDb = Annotated[Session, Depends(user_session)]
ReferenceDb = Annotated[Session, Depends(reference_session)]


def game_references(request: Request) -> GameReferences:
    """The application's cache, created at startup (``api.main``)."""
    found: GameReferences = request.app.state.game_references
    return found


def target_game(
    game: str,
    reference: ReferenceDb,
    references: Annotated[GameReferences, Depends(game_references)],
) -> GameReference:
    """The reference data of the path's ``{game}``: ``404`` if it is not a target game."""
    return references.get(reference, game)


TargetGame = Annotated[GameReference, Depends(target_game)]
