"""/api/game-catalog: the game catalogue, where the user chooses their target games (RF-25)."""

from fastapi import APIRouter

from api.dependencies import GameSlug, ReferenceDb, UserDb
from api.schemas.game_catalog import CatalogGameOut, GameChoiceIn
from api.services import game_catalog as service

router = APIRouter(prefix="/game-catalog", tags=["Catálogo de juegos"])


@router.get("", summary="Catálogo de juegos")
def list_catalog(reference: ReferenceDb, user: UserDb) -> list[CatalogGameOut]:
    """Los juegos de la saga principal y los Leyendas que pueden recibir un Pokémon criado, en
    orden de lanzamiento (CA-90), también los de las generaciones que no se cargan. De cada uno:
    si está seleccionado, si es juego objetivo y, si no se puede seleccionar, por qué
    (`obstacles`) y qué datos le faltan (`missing`) (RF-25, RF-05)."""
    return service.list_catalog(reference, user)


@router.put("/{game}", summary="Elegir un juego del catálogo")
def update_choice(
    game: GameSlug, change: GameChoiceIn, reference: ReferenceDb, user: UserDb
) -> CatalogGameOut:
    """Selecciona el juego como juego objetivo o lo quita (`selected`) y guarda la respuesta del
    usuario sobre si puede jugarlo en un sistema actual de Nintendo (`playable`, CA-92). Se
    comprueba que pueda recibir un Pokémon criado, que esté completo y que sea jugable, en ese
    orden (RF-25). `404` si el juego no está en el catálogo. `409` si se selecciona y no
    cumple alguna condición: `detail.obstacles` dice por qué y `detail.missing`, qué datos le
    faltan; la respuesta sobre si es jugable se guarda igualmente. `422` si no se indica
    ninguno de los dos campos."""
    return service.update_choice(reference, user, game, change)
