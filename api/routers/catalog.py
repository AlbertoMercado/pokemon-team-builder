"""/api/pokemon: the catalogue of Pokémon (RF-01, RF-02)."""

from typing import Annotated

from fastapi import APIRouter, Query

from api.dependencies import ReferenceDb, UserDb
from api.schemas.catalog import CatalogOut, PokemonDetailOut
from api.services import catalog as service

router = APIRouter(prefix="/pokemon", tags=["Catálogo"])


Search = Annotated[
    str | None,
    Query(description="Parte del nombre o del identificador; sin distinguir mayúsculas ni tildes."),
]
TypeFilter = Annotated[
    str | None, Query(alias="type", description="Un tipo actual, p. ej. `fire`.")
]
FavoriteFilter = Annotated[
    bool | None,
    Query(description="Solo favoritos (`true`) o solo los que no lo son (`false`)."),
]


@router.get("", summary="Lista de Pokémon")
def list_pokemon(
    user: UserDb,
    reference: ReferenceDb,
    q: Search = None,
    type_name: TypeFilter = None,
    favorite: FavoriteFilter = None,
) -> CatalogOut:
    """Todas las formas cargadas, en orden de la Pokédex Nacional, con sus tipos actuales y si
    están en favoritos. Las formas regionales son entradas propias."""
    return service.list_pokemon(user, reference, q, type_name, favorite)


@router.get("/{pokemon}", summary="Ficha de un Pokémon")
def pokemon_detail(pokemon: str, user: UserDb, reference: ReferenceDb) -> PokemonDetailOut:
    """Número, nombre, tipos actuales, línea evolutiva completa y el mecanismo de cada
    evolución. `404` si la forma no existe."""
    return service.pokemon_detail(user, reference, pokemon)
