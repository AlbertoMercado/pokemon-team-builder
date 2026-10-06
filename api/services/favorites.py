"""Favourites: the single list from which teams are generated (RF-03, RF-04, RN-02)."""

from sqlmodel import Session

from api.errors import NotFoundError
from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
from api.schemas.favorites import FavoriteOut, FavoritesOut
from api.services.images import image_url


def list_favorites(user: Session, reference: Session) -> FavoritesOut:
    added = {f.pokemon: f.added_at for f in user_repo.favorites(user)}
    rows = reference_repo.pokemon_rows(reference, added)
    favorites = [
        FavoriteOut(
            pokemon=row.slug,
            name=row.name,
            dex_number=row.dex_number,
            types=list(row.types),
            image_url=image_url(row.slug, row.has_image),
            added_at=added[row.slug],
        )
        for row in rows
    ]
    return FavoritesOut(total=len(favorites), favorites=favorites)


def add_favorite(user: Session, reference: Session, pokemon: str) -> FavoriteOut:
    """Adds the form ``pokemon`` (the evolution to reach, RN-09). Idempotent."""
    if not reference_repo.pokemon_exists(reference, pokemon):
        raise NotFoundError(f"El Pokémon {pokemon} no existe en los datos cargados")
    favorite = user_repo.add_favorite(user, pokemon)
    [row] = reference_repo.pokemon_rows(reference, [pokemon])
    return FavoriteOut(
        pokemon=row.slug,
        name=row.name,
        dex_number=row.dex_number,
        types=list(row.types),
        image_url=image_url(row.slug, row.has_image),
        added_at=favorite.added_at,
    )


def remove_favorite(user: Session, pokemon: str) -> None:
    if not user_repo.remove_favorite(user, pokemon):
        raise NotFoundError(f"{pokemon} no está en favoritos")
