"""/api/games: the games that can be the target (RF-05), or every loaded game (RF-12), and
their covers (RF-18)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlmodel import Session

from api.database import reference_session
from api.dependencies import DataDir, GameSlug, ReferenceDb, UserDb
from api.schemas.games import GameOut
from api.services import games as service
from api.services import images

router = APIRouter(prefix="/games", tags=["Juegos"])


@router.get("", summary="Juegos objetivo")
def list_games(
    reference: Annotated[Session, Depends(reference_session)],
    user: UserDb,
    every: Annotated[
        bool,
        Query(
            alias="all",
            description="Todos los juegos cargados, también los que no son juego objetivo, "
            "para el *Hall of Fame* (RF-12).",
        ),
    ] = False,
) -> list[GameOut]:
    """Los juegos que se pueden elegir como objetivo, en orden de lanzamiento: los juegos
    completos, que permiten la crianza y tienen todos los datos que necesitan las reglas, y que
    no están ya registrados en el *Hall of Fame* (RF-05, CA-68). Con `all=true`, todos los
    juegos cargados; `target` dice cuáles pueden ser juego objetivo y `completed`, cuáles ya
    están registrados."""
    return service.list_games(reference, user, every=every)


@router.get(
    "/{game}/cover",
    summary="Portada de un juego",
    response_class=FileResponse,
    responses={200: {"content": {"image/png": {}}, "description": "La portada, en PNG."}},
)
def game_cover(game: GameSlug, reference: ReferenceDb, data_dir: DataDir) -> FileResponse:
    """La portada del juego, de hasta 256 px, que la carga de datos descarga de WikiDex y guarda
    en la caché local (ADR-0011). Vale para cualquier juego cargado, también los que no son
    juego objetivo. Es la URL que dan las respuestas en `cover_url`. `404` si el juego no está
    cargado o no tiene portada."""
    path = images.cover_file(reference, data_dir, game)
    return FileResponse(
        path, media_type="image/png", headers={"Cache-Control": images.CACHE_CONTROL}
    )
