"""Games that can be chosen as the target game (RF-05), or every loaded game (RF-12)."""

from sqlmodel import Session

from api.repositories import reference as reference_repo
from api.schemas.games import GameOut


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
        )
        for game in games
    ]
