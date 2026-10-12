"""The game catalogue (RF-25): the games, the user's choices and which ones are target games.

Joins the catalogue of reference.sqlite with the choices of user.sqlite and the Hall of Fame,
and leaves the decision to ``core.game_catalog`` (RF-05, CA-91 to CA-93). Selecting a game that
cannot be a target game is a ``409`` with the reasons; the user's answer about whether it is
playable is kept anyway, because it is still their answer.
"""

from dataclasses import dataclass

from sqlmodel import Session

from api.errors import ConflictError, NotFoundError
from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
from api.schemas.game_catalog import CatalogGameOut, GameChoiceIn, ReasonOut
from api.services.images import cover_url
from core.game_catalog import CatalogEntry, GameChoice, Obstacle, is_target, obstacles, playable
from db.reference import CatalogGame, MissingData, Playability

MISSING_TEXT = {
    MissingData.GENERATION_NOT_LOADED: "Su generación todavía no se carga",
    MissingData.POKEMON: "Qué Pokémon existen en el juego y pueden llegar a él (RN-03)",
    MissingData.MECHANICS: "Sus mecánicas, como el ciclo de día y noche (RN-15)",
    MissingData.KEY_BATTLES: "Sus combates clave (RN-17)",
    MissingData.STARTERS: "Sus iniciales (RN-21)",
}
OBSTACLE_TEXT = {
    Obstacle.CANNOT_RECEIVE_BRED: "No puede recibir un Pokémon criado en otro juego (CA-29)",
    Obstacle.MISSING_DATA: "Le faltan datos que necesitan las reglas (RF-05)",
    Obstacle.PLAYABILITY_UNKNOWN: (
        "No se sabe si se puede jugar en un sistema actual de Nintendo: indica si puedes "
        "jugarlo (CA-92)"
    ),
    Obstacle.NOT_PLAYABLE: "No se puede jugar en un sistema actual de Nintendo (CA-92)",
}


@dataclass(frozen=True)
class _Game:
    """A game of the catalogue with what the user chose about it."""

    row: CatalogGame
    entry: CatalogEntry
    choice: GameChoice
    completed: bool
    has_cover: bool

    @property
    def target(self) -> bool:
        return is_target(self.entry, self.choice, completed=self.completed)


def _games(reference: Session, user: Session) -> list[_Game]:
    choices = user_repo.game_choices(user)
    completed = user_repo.completed_games(user)
    loaded = reference_repo.all_games(reference)
    games = []
    for row in reference_repo.catalog_games(reference):
        stored = choices.get(row.game)
        choice = GameChoice(stored.selected, stored.playable) if stored else GameChoice()
        entry = CatalogEntry(
            row.game,
            row.receives_bred,
            tuple(row.missing),
            row.playable_now == Playability.YES,
        )
        cover = loaded.get(row.game)
        games.append(
            _Game(
                row,
                entry,
                choice,
                row.game in completed,
                cover is not None and cover.cover is not None,
            )
        )
    return games


def _out(game: _Game) -> CatalogGameOut:
    row = game.row
    return CatalogGameOut(
        game=row.game,
        name=row.name_es,
        generation=row.generation,
        platform=row.platform,
        receives_bred=row.receives_bred,
        known_playable=game.entry.known_playable,
        playable=playable(game.entry, game.choice),
        selected=game.choice.selected,
        target=game.target,
        completed=game.completed,
        obstacles=[
            ReasonOut(code=o.value, text=OBSTACLE_TEXT[o])
            for o in obstacles(game.entry, game.choice)
        ],
        missing=[ReasonOut(code=m, text=MISSING_TEXT[MissingData(m)]) for m in row.missing],
        cover_url=cover_url(row.game, game.has_cover),
    )


def list_catalog(reference: Session, user: Session) -> list[CatalogGameOut]:
    """Every game of the catalogue, in release order, with the user's choices (RF-25)."""
    return [_out(game) for game in _games(reference, user)]


def target_games(reference: Session, user: Session) -> set[str]:
    """The target games: selected, with no obstacle and not completed (RF-05, CA-93)."""
    return {game.row.game for game in _games(reference, user) if game.target}


def update_choice(
    reference: Session, user: Session, game: str, change: GameChoiceIn
) -> CatalogGameOut:
    """Select a game or not, and answer whether it is playable (RF-25).

    ``NotFoundError`` if it is not in the catalogue. ``ConflictError`` with the reasons if it
    is selected but cannot be a target game; the answer about playability is kept anyway.
    """
    if reference_repo.catalog_game(reference, game) is None:
        raise NotFoundError(f"El juego {game} no está en el catálogo de juegos")
    if change.playable is not None:
        user_repo.save_game_choice(user, game, selected=None, playable=change.playable)
    [current] = [found for found in _games(reference, user) if found.row.game == game]
    if change.selected:
        found = obstacles(current.entry, GameChoice(True, current.choice.playable))
        if found:
            raise ConflictError(
                f"{current.row.name_es} no se puede seleccionar como juego objetivo",
                {
                    "obstacles": [{"code": o.value, "text": OBSTACLE_TEXT[o]} for o in found],
                    "missing": [
                        {"code": m, "text": MISSING_TEXT[MissingData(m)]}
                        for m in current.row.missing
                    ],
                },
            )
    if change.selected is not None:
        user_repo.save_game_choice(user, game, selected=change.selected, playable=None)
    [updated] = [found for found in _games(reference, user) if found.row.game == game]
    return _out(updated)
