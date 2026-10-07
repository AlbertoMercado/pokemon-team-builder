"""Games that can be chosen as the target game (RF-05), or every loaded game (RF-12)."""

from sqlmodel import Session

from api.repositories import reference as reference_repo
from api.schemas.games import GameOut
from api.services import wikidex
from api.services.images import cover_url
from db.reference import Game


def list_games(reference: Session, *, every: bool = False) -> list[GameOut]:
    """The target games or, with ``every``, all the loaded ones, in release order.

    Any loaded game can be recorded in the Hall of Fame, also those that are not a target.
    """
    targets = {game.slug for game in reference_repo.target_games(reference)}
    games = (
        sorted(reference_repo.all_games(reference).values(), key=lambda g: g.release_order)
        if every
        else reference_repo.target_games(reference)
    )
    return [
        GameOut(
            game=game.slug,
            name=game.name_es,
            generation=game.generation,
            version_group=game.version_group,
            target=game.slug in targets,
            cover_url=cover_url(game.slug, game.cover is not None),
            cover_source_url=cover_source_url(game),
        )
        for game in games
    ]


def cover_source_url(game: Game | None) -> str | None:
    """The WikiDex page of the game's cover, or ``None`` if it has none (CA-56, ADR-0011)."""
    if game is None or game.cover is None or game.cover_source is None:
        return None
    return wikidex.page_url(game.cover_source)
