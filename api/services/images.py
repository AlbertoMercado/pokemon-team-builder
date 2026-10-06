"""Images of the forms: their URL in the responses and the file behind it (RF-17, ADR-0010).

The ingest downloads each sprite to the cache of the data directory and stores its path in
``pokemon.image``. The API serves it at ``/api/pokemon/{pokemon}/image``, so the web never asks
an external server. The path comes from the database, never from the URL, and must stay inside
the data directory.
"""

from pathlib import Path

from sqlmodel import Session

from api.errors import NotFoundError
from api.repositories import reference as reference_repo

IMAGE_URL = "/api/pokemon/{pokemon}/image"
# The browser keeps each image for a day without asking again: sprites weigh about 1 KB and
# only change with a new load, so a day is a good balance.
CACHE_CONTROL = "public, max-age=86400"


def image_url(pokemon: str, has_image: bool) -> str | None:
    """The URL of the form's image, or ``None`` if it has none."""
    return IMAGE_URL.format(pokemon=pokemon) if has_image else None


def image_file(reference: Session, data_dir: Path, pokemon: str) -> Path:
    """The sprite of ``pokemon``; ``NotFoundError`` if the form does not exist, has no image or
    its file is missing or outside the data directory."""
    relative = reference_repo.pokemon_image(reference, pokemon)
    if relative is None:
        raise NotFoundError(f"El Pokémon {pokemon} no tiene imagen")
    root = data_dir.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise NotFoundError(f"La imagen de {pokemon} no está en el directorio de datos")
    return path
