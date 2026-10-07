"""/api/hall-of-fame: the teams the user completed each game with (RF-12, RF-13)."""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Response, status

from api.dependencies import ReferenceDb, UserDb
from api.schemas.hall_of_fame import HallOfFameEntryIn, HallOfFameEntryOut, HallOfFamePatch
from api.services import hall_of_fame as service

router = APIRouter(prefix="/hall-of-fame", tags=["Hall of Fame"])

EntryId = Annotated[int, Path(description="Identificador del registro (`id`).")]


@router.get("", summary="Recorrido")
def list_entries(
    user: UserDb,
    reference: ReferenceDb,
    game: Annotated[str | None, Query(description="Solo los registros de este juego.")] = None,
) -> list[HallOfFameEntryOut]:
    """Los registros en el orden del recorrido: por fecha y, a igualdad, por orden de registro.
    `last` marca el último juego completado. Con `game`, solo los de ese juego."""
    return service.list_entries(user, reference, game)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Registrar un equipo")
def add_entry(body: HallOfFameEntryIn, user: UserDb, reference: ReferenceDb) -> HallOfFameEntryOut:
    """Registra el equipo con el que se completó un juego. Guarda los tipos que tenía cada
    miembro en ese juego. `422` si el juego o algún Pokémon no existen en los datos cargados
    (o en la generación del juego)."""
    return service.add_entry(user, reference, body)


@router.patch("/{entry_id}", summary="Corregir un registro")
def update_entry(
    entry_id: EntryId, change: HallOfFamePatch, user: UserDb, reference: ReferenceDb
) -> HallOfFameEntryOut:
    """Cambia el juego, la fecha, las notas o el equipo. Si cambia el juego o el equipo, se
    vuelven a copiar los tipos. `404` si el registro no existe; `422` como al registrarlo."""
    return service.update_entry(user, reference, entry_id, change)


@router.delete(
    "/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar un registro"
)
def remove_entry(entry_id: EntryId, user: UserDb) -> Response:
    """Elimina el registro y su equipo. `404` si no existe."""
    service.remove_entry(user, entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
