"""/api/pokemon: the catalogue of Pokémon (RF-01, RF-02)."""

from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from api.dependencies import DataDir, ReferenceDb, UserDb
from api.schemas.catalog import CatalogOut, PokemonDetailOut
from api.services import catalog as service
from api.services import images

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


@router.get(
    "/{pokemon}/image",
    summary="Imagen de un Pokémon",
    response_class=FileResponse,
    responses={200: {"content": {"image/png": {}}, "description": "La imagen, en PNG."}},
)
def pokemon_image(pokemon: str, reference: ReferenceDb, data_dir: DataDir) -> FileResponse:
    """La imagen de la forma (su *sprite* de PokeAPI, recortado a la figura), que la carga de
    datos guarda en la caché local. Es la URL que dan las respuestas en `image_url`. `404` si
    la forma no existe o no tiene imagen."""
    path = images.image_file(reference, data_dir, pokemon)
    return FileResponse(
        path, media_type="image/png", headers={"Cache-Control": images.CACHE_CONTROL}
    )


@router.get(
    "/{pokemon}/artwork",
    summary="Ilustración de un Pokémon",
    response_class=FileResponse,
    responses={200: {"content": {"image/png": {}}, "description": "La ilustración, en PNG."}},
)
def pokemon_artwork(pokemon: str, reference: ReferenceDb, data_dir: DataDir) -> FileResponse:
    """La ilustración oficial de la forma, de hasta 256 px, para la ficha. La carga de datos la
    guarda en la caché local. Es la URL que da la ficha en `artwork_url`. `404` si la forma no
    existe o no tiene ilustración."""
    path = images.image_file(reference, data_dir, pokemon, artwork=True)
    return FileResponse(
        path, media_type="image/png", headers={"Cache-Control": images.CACHE_CONTROL}
    )
