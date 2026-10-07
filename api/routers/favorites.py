"""/api/favorites: the list of favourites (RF-03, RF-04)."""

from fastapi import APIRouter, Response, status

from api.dependencies import PokemonSlug, ReferenceDb, UserDb
from api.schemas.favorites import FavoriteOut, FavoritesOut
from api.services import favorites as service

router = APIRouter(prefix="/favorites", tags=["Favoritos"])


@router.get("", summary="Lista de favoritos")
def list_favorites(user: UserDb, reference: ReferenceDb) -> FavoritesOut:
    """Los favoritos, en orden de la Pokédex Nacional, y cuántos hay."""
    return service.list_favorites(user, reference)


@router.put("/{pokemon}", summary="Añadir un favorito")
def add_favorite(pokemon: PokemonSlug, user: UserDb, reference: ReferenceDb) -> FavoriteOut:
    """Añade la forma `pokemon`, la evolución hasta la que se quiere llegar (RN-09). Si ya era
    favorito, no cambia nada. `404` si la forma no existe en los datos cargados."""
    return service.add_favorite(user, reference, pokemon)


@router.delete("/{pokemon}", status_code=status.HTTP_204_NO_CONTENT, summary="Quitar un favorito")
def remove_favorite(pokemon: PokemonSlug, user: UserDb) -> Response:
    """Quita `pokemon` de favoritos. `404` si no estaba."""
    service.remove_favorite(user, pokemon)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
