"""Images of the forms and covers of the games: their URLs in the responses and the files
behind them (RF-17, RF-18, ADR-0010, ADR-0011).

The ingest stores two images of each form in the cache of the data directory: the sprite
trimmed to its figure (``pokemon.image``), for the lists, and the official artwork
(``pokemon.artwork``), for the detail. The API serves them at ``/api/pokemon/{pokemon}/image``
and ``/api/pokemon/{pokemon}/artwork``, so the web never asks an external server. The path
comes from the database, never from the URL, and must stay inside the data directory.

The covers of the games, reduced to 256 px by the ingest (``game.cover``), are served the same way
at ``/api/games/{game}/cover``, for any loaded game.
"""

from pathlib import Path

from sqlmodel import Session

from api.errors import NotFoundError
from api.repositories import reference as reference_repo

IMAGE_URL = "/api/pokemon/{pokemon}/image"
ARTWORK_URL = "/api/pokemon/{pokemon}/artwork"
COVER_URL = "/api/games/{game}/cover"
# The browser keeps each image for a day without asking again: sprites weigh about 1 KB and
# only change with a new load, so a day is a good balance.
CACHE_CONTROL = "public, max-age=86400"


def image_url(pokemon: str, has_image: bool) -> str | None:
    """The URL of the form's image, or ``None`` if it has none."""
    return IMAGE_URL.format(pokemon=pokemon) if has_image else None


def artwork_url(pokemon: str, has_artwork: bool) -> str | None:
    """The URL of the form's official artwork, or ``None`` if it has none."""
    return ARTWORK_URL.format(pokemon=pokemon) if has_artwork else None


def cover_url(game: str, has_cover: bool) -> str | None:
    """The URL of the game's cover, or ``None`` if it has none."""
    return COVER_URL.format(game=game) if has_cover else None


def image_file(reference: Session, data_dir: Path, pokemon: str, *, artwork: bool = False) -> Path:
    """The trimmed sprite of ``pokemon`` (or its artwork); ``NotFoundError`` if the form does
    not exist, has no such image or its file is missing or outside the data directory."""
    relative = reference_repo.pokemon_image(reference, pokemon, artwork=artwork)
    if relative is None:
        raise NotFoundError(f"El Pokémon {pokemon} no tiene imagen")
    return _inside(data_dir, relative, f"La imagen de {pokemon}")


def cover_file(reference: Session, data_dir: Path, game: str) -> Path:
    """The reduced cover of ``game``; ``NotFoundError`` if the game is not loaded, has no cover
    or its file is missing or outside the data directory."""
    relative = reference_repo.game_cover(reference, game)
    if relative is None:
        raise NotFoundError(f"El juego {game} no tiene portada")
    return _inside(data_dir, relative, f"La portada de {game}")


def _inside(data_dir: Path, relative: str, what: str) -> Path:
    """``data_dir / relative`` if it is a file inside the data directory."""
    root = data_dir.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise NotFoundError(f"{what} no está en el directorio de datos")
    return path
