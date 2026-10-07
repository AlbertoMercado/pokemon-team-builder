"""POST /api/games/{game}/generations: generate the teams (RF-08, RF-09, RF-10)."""

from fastapi import APIRouter, status

from api.dependencies import ReferenceDb, TargetGame, UserDb
from api.schemas.generation import GenerationOut, PendingDataOut
from api.schemas.hall_of_fame import CompletedGameOut
from api.services import generation as service

router = APIRouter(prefix="/games/{game}/generations", tags=["Generación"])


@router.post(
    "",
    summary="Generar equipos",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": PendingDataOut | CompletedGameOut,
            "description": "Quedan datos sin verificar que intervienen (RN-18), o el juego ya "
            "está registrado en el *Hall of Fame* (CA-68).",
        }
    },
)
def generate(game: TargetGame, user: UserDb, reference: ReferenceDb) -> GenerationOut:
    """Genera los equipos con los favoritos, las reglas y las confirmaciones actuales. No se
    guarda: es un cálculo. `409` con los datos pendientes si queda alguno sin confirmar, o con
    el registro del *Hall of Fame* si el juego ya está registrado (CA-68); `404` si el juego no
    es juego objetivo."""
    return service.generate_teams(user, reference, game)
