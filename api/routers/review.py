"""/api/games/{game}/review: the unverified data to confirm before generating (RF-15)."""

from fastapi import APIRouter

from api.dependencies import ReferenceDb, TargetGame, UserDb
from api.schemas.review import ConfirmationIn, ReviewFactOut, ReviewOut
from api.services import review as service

router = APIRouter(prefix="/games/{game}/review", tags=["Revisión de datos"])


@router.get("", summary="Datos sin verificar del juego")
def get_review(game: TargetGame, user: UserDb, reference: ReferenceDb) -> ReviewOut:
    """Los datos inferidos o pendientes que intervienen en la generación con los favoritos y
    las reglas actuales, con su propuesta y su estado (RN-18). Con `pending` a 0 se puede
    generar. `404` si el juego no es juego objetivo."""
    return service.review(user, reference, game)


@router.put("/{fact_key}", summary="Confirmar o corregir un dato")
def confirm(fact_key: str, body: ConfirmationIn, game: TargetGame, user: UserDb) -> ReviewFactOut:
    """Confirma el dato con el valor propuesto o con uno corregido: un booleano o, en un
    combate clave, la lista de Pokémon de su equipo. `404` si el dato no existe en el juego;
    `409` si se cargó sin ambigüedad (automático); `422` si el valor no es del tipo del dato o
    el equipo incluye Pokémon que no existen en la generación del juego."""
    return service.confirm(user, game, fact_key, body.value)


@router.post("/accept-proposals", summary="Aceptar todas las propuestas")
def accept_proposals(game: TargetGame, user: UserDb, reference: ReferenceDb) -> ReviewOut:
    """Confirma de una vez todas las propuestas inferidas que intervienen y aún no están
    confirmadas. Los datos pendientes, sin propuesta, se confirman uno a uno. Devuelve la
    revisión actualizada."""
    return service.accept_proposals(user, reference, game)
