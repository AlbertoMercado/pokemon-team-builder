"""/api/games: the games that can be the target (RF-05), or every loaded game (RF-12)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from api.database import reference_session
from api.schemas.games import GameOut
from api.services import games as service

router = APIRouter(prefix="/games", tags=["Juegos"])


@router.get("", summary="Juegos objetivo")
def list_games(
    reference: Annotated[Session, Depends(reference_session)],
    every: Annotated[
        bool,
        Query(
            alias="all",
            description="Todos los juegos cargados, también los que no son juego objetivo, "
            "para el *Hall of Fame* (RF-12).",
        ),
    ] = False,
) -> list[GameOut]:
    """Los juegos que se pueden elegir como objetivo, en orden de lanzamiento: los de la saga
    principal con datos cargados que permiten la crianza (RF-05). Con `all=true`, todos los
    juegos cargados; `target` dice cuáles pueden ser juego objetivo."""
    return service.list_games(reference, every=every)
