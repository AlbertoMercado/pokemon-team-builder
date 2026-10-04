"""/api/games: the games that can be the target (RF-05)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.database import reference_session
from api.schemas.games import GameOut
from api.services import games as service

router = APIRouter(prefix="/games", tags=["Juegos"])


@router.get("", summary="Juegos objetivo")
def list_games(reference: Annotated[Session, Depends(reference_session)]) -> list[GameOut]:
    """Los juegos que se pueden elegir como objetivo, en orden de lanzamiento: los de la saga
    principal con datos cargados que permiten la crianza (RF-05)."""
    return service.list_target_games(reference)
