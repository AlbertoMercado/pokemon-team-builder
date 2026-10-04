"""Games that can be chosen as the target game (RF-05)."""

from sqlmodel import Session

from api.repositories import reference as reference_repo
from api.schemas.games import GameOut


def list_target_games(reference: Session) -> list[GameOut]:
    return [
        GameOut(
            game=game.slug,
            name=game.name_es,
            generation=game.generation,
            version_group=game.version_group,
        )
        for game in reference_repo.target_games(reference)
    ]
