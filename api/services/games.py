"""Games that can be chosen as the target game (RF-05), or every loaded game (RF-12).

A game already recorded in the Hall of Fame is completed: it is no longer a target game (CA-68).
"""

from sqlmodel import Session

from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
from api.schemas.games import GameOut
from api.services import wikidex
from api.services.images import cover_url
from db.reference import Game


def list_games(reference: Session, user: Session, *, every: bool = False) -> list[GameOut]:
    """The target games or, with ``every``, all the loaded ones, in release order.

    Any loaded game that is not completed can be recorded in the Hall of Fame, also those that
    are not a target.
    """
    completed = user_repo.completed_games(user)
    targets = {
        game.slug for game in reference_repo.target_games(reference) if game.slug not in completed
    }
    games = sorted(reference_repo.all_games(reference).values(), key=lambda g: g.release_order)
    if not every:
        games = [game for game in games if game.slug in targets]
    return [
        GameOut(
            game=game.slug,
            name=game.name_es,
            generation=game.generation,
            version_group=game.version_group,
            target=game.slug in targets,
            completed=game.slug in completed,
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
