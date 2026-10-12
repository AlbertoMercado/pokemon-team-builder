"""Target games: only complete games can be chosen (RF-05, CA-67).

The PokeAPI source marks as target every game of a target generation (``scope``). Once every
source is stored, ``mark_incomplete_games`` leaves as target only the complete ones: those with
everything the rules need to work. An incomplete game is still loaded, because the Hall of Fame
uses it, but it cannot be chosen, and the load report says what it lacks. It never blocks the
load.

``fill_catalog`` stores, for each game of the game catalogue (RF-25), what it lacks to be
complete: what ``missing_data`` finds or, for a game that is not loaded, that its generation is
not loaded.
"""

from collections.abc import Callable

from sqlalchemy import func
from sqlmodel import Session, col, select

from db.reference import (
    CatalogGame,
    Game,
    GameMechanic,
    GamePokemon,
    GameStarter,
    KeyBattle,
    MissingData,
    ReferenceModel,
)
from ingest.sources.curated.schemas import MECHANICS

type Count = Callable[[Session, str], int]


def _rows(model: type[ReferenceModel], game_column: object) -> Count:
    def count(session: Session, game: str) -> int:
        query = select(func.count()).select_from(model).where(game_column == game)
        return session.exec(query).one()

    return count


# What a game needs, in the order of RF-05, and how many rows it needs at least.
_REQUIRED: tuple[tuple[MissingData, Count, int], ...] = (
    (MissingData.POKEMON, _rows(GamePokemon, GamePokemon.game), 1),
    (MissingData.MECHANICS, _rows(GameMechanic, GameMechanic.game), len(MECHANICS)),
    (MissingData.KEY_BATTLES, _rows(KeyBattle, KeyBattle.game), 1),
    (MissingData.STARTERS, _rows(GameStarter, GameStarter.game), 1),
)
# How the load report names each one, with the rule that needs it.
MISSING_TEXT = {
    MissingData.GENERATION_NOT_LOADED: "los datos de su generación",
    MissingData.POKEMON: "los Pokémon que existen y pueden llegar (RN-03)",
    MissingData.MECHANICS: "sus mecánicas (RN-15)",
    MissingData.KEY_BATTLES: "sus combates clave (RN-17)",
    MissingData.STARTERS: "sus iniciales (RN-21)",
}


def missing_data(session: Session, game: str) -> list[MissingData]:
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
            incomplete[game.name_es] = [MISSING_TEXT[what] for what in missing]
    return incomplete


def fill_catalog(session: Session) -> None:
    """Store what each game of the catalogue lacks to be complete (RF-25). The caller commits."""
    loaded = set(session.exec(select(Game.slug)).all())
    for entry in session.exec(select(CatalogGame)).all():
        if entry.game in loaded:
            entry.missing = missing_data(session, entry.game)
        else:
            entry.missing = [MissingData.GENERATION_NOT_LOADED]
        session.add(entry)
