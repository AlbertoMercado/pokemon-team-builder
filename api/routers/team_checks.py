"""POST /api/games/{game}/team-checks: check a team chosen in the result (RF-12, CA-53)."""

from fastapi import APIRouter, status

from api.dependencies import ReferenceDb, TargetGame, UserDb
from api.schemas.generation import PendingDataOut
from api.schemas.team_check import TeamCheckIn, TeamCheckOut
from api.services import generation as service

router = APIRouter(prefix="/games/{game}/team-checks", tags=["Generación"])


@router.post(
    "",
    summary="Comprobar un equipo elegido",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": PendingDataOut,
            "description": "Quedan datos sin verificar que intervienen (RN-18).",
        }
    },
)
def check_team(
    body: TeamCheckIn, game: TargetGame, user: UserDb, reference: ReferenceDb
) -> TeamCheckOut:
    """Comprueba el equipo elegido en el resultado (favoritos y sugerencias) con las reglas
    activas: que cada miembro pase los filtros (RN-03, RN-11, RN-16), que no haya dos
    incompatibles (RN-07, RN-12, RN-14) y que se cumplan las reglas de presencia (RN-13,
    RN-14). No se guarda. `409` si quedan datos sin confirmar, como al generar; `422` si un
    miembro se repite o no existe en la generación del juego; `404` si el juego no es juego
    objetivo."""
    return service.check_chosen_team(user, reference, game, body.members)
