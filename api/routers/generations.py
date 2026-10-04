"""POST /api/games/{game}/generations: generate the teams (RF-08, RF-09, RF-10)."""

from fastapi import APIRouter, status

from api.dependencies import ReferenceDb, TargetGame, UserDb
from api.schemas.generation import GenerationOut, PendingDataOut
from api.services import generation as service

router = APIRouter(prefix="/games/{game}/generations", tags=["Generación"])


@router.post(
    "",
    summary="Generar equipos",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": PendingDataOut,
            "description": "Quedan datos sin verificar que intervienen (RN-18).",
        }
    },
)
def generate(game: TargetGame, user: UserDb, reference: ReferenceDb) -> GenerationOut:
    """Genera los equipos con los favoritos, las reglas y las confirmaciones actuales. No se
    guarda: es un cálculo. `409` con los datos pendientes si queda alguno sin confirmar; `404`
    si el juego no es juego objetivo."""
    return service.generate_teams(user, reference, game)
