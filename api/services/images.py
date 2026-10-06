"""Images of the forms: their URLs in the responses and the files behind them (RF-17,
ADR-0010).

The ingest stores two images of each form in the cache of the data directory: the sprite
trimmed to its figure (``pokemon.image``), for the lists, and the official artwork
(``pokemon.artwork``), for the detail. The API serves them at ``/api/pokemon/{pokemon}/image``
and ``/api/pokemon/{pokemon}/artwork``, so the web never asks an external server. The path
comes from the database, never from the URL, and must stay inside the data directory.
"""

from pathlib import Path

from sqlmodel import Session

from api.errors import NotFoundError
from api.repositories import reference as reference_repo

IMAGE_URL = "/api/pokemon/{pokemon}/image"
ARTWORK_URL = "/api/pokemon/{pokemon}/artwork"
# The browser keeps each image for a day without asking again: sprites weigh about 1 KB and
# only change with a new load, so a day is a good balance.
CACHE_CONTROL = "public, max-age=86400"


def image_url(pokemon: str, has_image: bool) -> str | None:
    """The URL of the form's image, or ``None`` if it has none."""
    return IMAGE_URL.format(pokemon=pokemon) if has_image else None


def artwork_url(pokemon: str, has_artwork: bool) -> str | None:
    """The URL of the form's official artwork, or ``None`` if it has none."""
    return ARTWORK_URL.format(pokemon=pokemon) if has_artwork else None


def image_file(reference: Session, data_dir: Path, pokemon: str, *, artwork: bool = False) -> Path:
    """The trimmed sprite of ``pokemon`` (or its artwork); ``NotFoundError`` if the form does
    not exist, has no such image or its file is missing or outside the data directory."""
    relative = reference_repo.pokemon_image(reference, pokemon, artwork=artwork)
    if relative is None:
        raise NotFoundError(f"El Pokémon {pokemon} no tiene imagen")
    root = data_dir.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise NotFoundError(f"La imagen de {pokemon} no está en el directorio de datos")
    return path
