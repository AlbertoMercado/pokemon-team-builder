"""/api/pokedex: the Pokédex of the completed games (RF-20 to RF-24, RN-22 to RN-26)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, Response, status

from api.dependencies import ReferenceDb, UserDb
from api.schemas.pokedex import (
    InitialListIn,
    ObjectiveOut,
    PokedexGameOut,
    PokedexMarkIn,
    PokedexOut,
    PokedexPokemonOut,
)
from api.services import pokedex as service
from api.services.pokedex import PokedexData
from api.services.pokedex_reference import PokedexReferences

router = APIRouter(prefix="/pokedex", tags=["Pokédex"])

CompletedGame = Annotated[
    str, Path(description="Identificador de un juego registrado en el *Hall of Fame*.")
]
SpeciesSlug = Annotated[
    str, Path(description="Identificador de la especie, p. ej. `pikachu` (no de la forma).")
]


def pokedex_data(request: Request, user: UserDb, reference: ReferenceDb) -> PokedexData:
    """Both databases and the cache of the Pokédex reference data, created at startup."""
    references: PokedexReferences = request.app.state.pokedex_references
    return PokedexData(user, reference, references)


Data = Annotated[PokedexData, Depends(pokedex_data)]


@router.get("", summary="Pokédex de los juegos superados")
def list_pokedexes(data: Data) -> list[PokedexGameOut]:
    """Los juegos registrados en el *Hall of Fame*, en el orden del recorrido, con el progreso
    de su Pokédex (RF-20, RN-22). Los juegos que ya no están cargados no aparecen."""
    return service.list_pokedexes(data)


@router.get("/{game}", summary="Pokédex de un juego")
def get_pokedex(game: CompletedGame, data: Data) -> PokedexOut:
    """Todos los Pokémon de la Pokédex del juego, en su orden, con lo que ha marcado el usuario:
    la lista inicial (RF-21) y el detalle de registrados e imposibles (RF-24). `404` si el
    juego no está en el *Hall of Fame*."""
    return service.get_pokedex(data, game)


@router.put(
    "/{game}/initial",
    summary="Confirmar la lista inicial",
    responses={status.HTTP_409_CONFLICT: {"description": "La lista inicial ya está confirmada."}},
)
def start_pokedex(game: CompletedGame, body: InitialListIn, data: Data) -> PokedexOut:
    """Guarda los Pokémon que el usuario ya tiene registrados y empieza la Pokédex (RF-21).
    Solo una vez: después se corrige con cada Pokémon. `404` si el juego no está en el *Hall of
    Fame*; `409` si ya estaba confirmada; `422` si alguna especie no está en la Pokédex."""
    return service.start_pokedex(data, game, body)


@router.get("/{game}/objective", summary="Pokémon objetivo")
def get_objective(
    game: CompletedGame,
    data: Data,
    skipped: Annotated[
        list[str] | None,
        Query(
            description="Especies saltadas de momento; no se guardan, y al volver a entrar el "
            "objetivo vuelve a ser el primero sin registrar (CA-77)."
        ),
    ] = None,
) -> ObjectiveOut:
    """La ficha del primer Pokémon de la Pokédex que no está registrado, ni es imposible, ni se
    ha saltado (RN-23, RF-22), con todas sus formas de obtención. Nula si no queda ninguno.
    `404` si el juego no está en el *Hall of Fame*."""
    return service.get_objective(data, game, skipped or [])


@router.get("/{game}/pokemon/{species}", summary="Ficha de un Pokémon")
def get_pokemon(game: CompletedGame, species: SpeciesSlug, data: Data) -> PokedexPokemonOut:
    """El Pokémon con todas sus formas de obtención, de la más sencilla a la menos, la
    recomendada y la elegida por el usuario marcadas (RF-22, RF-23, RN-24 a RN-26). `404` si
    el juego no está en el *Hall of Fame* o la especie no está en su Pokédex."""
    return service.get_pokemon(data, game, species)


@router.put(
    "/{game}/pokemon/{species}",
    summary="Marcar un Pokémon",
    responses={status.HTTP_409_CONFLICT: {"description": "La lista inicial no está confirmada."}},
)
def mark_pokemon(
    game: CompletedGame, species: SpeciesSlug, change: PokedexMarkIn, data: Data
) -> PokedexPokemonOut:
    """Lo registra, lo marca como imposible o lo desmarca (`status`), y elige su forma de
    obtención (`chosen_method`). Solo cambian los campos indicados (RF-22 a RF-24). `404` como
    en la ficha; `409` si no se ha confirmado la lista inicial; `422` si la forma no es suya."""
    return service.mark_pokemon(data, game, species, change)


@router.delete(
    "/{game}/pokemon/{species}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desmarcar un Pokémon",
    responses={status.HTTP_409_CONFLICT: {"description": "La lista inicial no está confirmada."}},
)
def unmark_pokemon(game: CompletedGame, species: SpeciesSlug, data: Data) -> Response:
    """Quita su marca y la forma elegida, para corregir un error (RF-24). `404` como en la
    ficha; `409` si no se ha confirmado la lista inicial."""
    service.unmark_pokemon(data, game, species)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
