"""Target games: only complete games can be chosen (RF-05, CA-67).

The PokeAPI source marks as target every game of a target generation (``scope``). Once every
source is stored, ``mark_incomplete_games`` leaves as target only the complete ones: those with
everything the rules need to work. An incomplete game is still loaded, because the Hall of Fame
uses it, but it cannot be chosen, and the load report says what it lacks. It never blocks the
load.
"""

from collections.abc import Callable

from sqlalchemy import func
from sqlmodel import Session, col, select

from db.reference import Game, GameMechanic, GamePokemon, GameStarter, KeyBattle, ReferenceModel
from ingest.sources.curated.schemas import MECHANICS

type Count = Callable[[Session, str], int]


def _rows(model: type[ReferenceModel], game_column: object) -> Count:
    def count(session: Session, game: str) -> int:
        query = select(func.count()).select_from(model).where(game_column == game)
        return session.exec(query).one()

    return count


# What a game needs, with the rule that needs it, in the order of RF-05.
_REQUIRED: tuple[tuple[str, Count, int], ...] = (
    ("los Pokémon que existen y pueden llegar (RN-03)", _rows(GamePokemon, GamePokemon.game), 1),
    ("sus mecánicas (RN-15)", _rows(GameMechanic, GameMechanic.game), len(MECHANICS)),
    ("sus combates clave (RN-17)", _rows(KeyBattle, KeyBattle.game), 1),
    ("sus iniciales (RN-21)", _rows(GameStarter, GameStarter.game), 1),
)


def missing_data(session: Session, game: str) -> list[str]:
    """What ``game`` lacks to be complete, in the order of RF-05; empty if it is complete."""
    return [what for what, count, needed in _REQUIRED if count(session, game) < needed]


def mark_incomplete_games(session: Session) -> dict[str, list[str]]:
    """Leave as target only the complete games; returns the others with what they lack.

    In release order. The caller commits.
    """
    incomplete = {}
    targets = session.exec(
        select(Game).where(col(Game.is_target)).order_by(col(Game.release_order))
    ).all()
    for game in targets:
        missing = missing_data(session, game.slug)
        if missing:
            game.is_target = False
            incomplete[game.name_es] = missing
    return incomplete
