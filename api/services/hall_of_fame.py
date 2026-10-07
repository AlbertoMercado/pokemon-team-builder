"""The Hall of Fame: the teams the user completed each game with, i.e. the journey (RF-12,
RF-13, RN-16).

Entries are ordered by date and, on equal dates, by order of registration (``sequence``):
the last one is the last game completed. Each member keeps a copy of its types in that game
(CA-07). ``journey`` turns the entries into the engine's ``HallOfFameEntry``, so a generation
excludes the lines already used.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlmodel import Session

from api.errors import InvalidValueError, NotFoundError
from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
from api.repositories.user import MemberRow
from api.schemas.hall_of_fame import (
    HallOfFameEntryIn,
    HallOfFameEntryOut,
    HallOfFameMemberOut,
    HallOfFamePatch,
)
from api.services.context import GameReference
from api.services.games import cover_source_url
from api.services.images import cover_url, image_url
from core.domain import HallOfFameEntry, JourneyMember
from db import user as user_db
from db.reference import Game

type Entry = tuple[user_db.HallOfFameEntry, list[user_db.HallOfFameMember]]


def _in_journey_order(entries: Sequence[Entry]) -> list[Entry]:
    return sorted(entries, key=lambda e: (e[0].completed_on, e[0].sequence))


def list_entries(
    user: Session, reference: Session, game: str | None = None
) -> list[HallOfFameEntryOut]:
    """The entries in journey order, only those of ``game`` if given."""
    ordered = _in_journey_order(user_repo.hall_of_fame(user))
    games = reference_repo.all_games(reference)
    slugs = {member.pokemon for _, members in ordered for member in members}
    rows = reference_repo.pokemon_rows(reference, slugs)
    names = {row.slug: row.name for row in rows}
    with_image = {row.slug for row in rows if row.has_image}
    return [
        _out(entry, members, order, order == len(ordered), _Names(games, names, with_image))
        for order, (entry, members) in enumerate(ordered, start=1)
        if game is None or entry.game == game
    ]


def _one(user: Session, reference: Session, entry_id: int) -> HallOfFameEntryOut:
    return next(e for e in list_entries(user, reference) if e.id == entry_id)


def add_entry(user: Session, reference: Session, body: HallOfFameEntryIn) -> HallOfFameEntryOut:
    game = _game(reference, body.game)
    members = _members(reference, game, body.members)
    entry = user_repo.add_hall_of_fame_entry(
        user, game.slug, body.completed_on, body.notes, members
    )
    assert entry.id is not None
    return _one(user, reference, entry.id)


def update_entry(
    user: Session, reference: Session, entry_id: int, change: HallOfFamePatch
) -> HallOfFameEntryOut:
    """Changes the given fields; the types are copied again if the game or the team change."""
    entry = _entry(user, entry_id)
    fields = change.model_fields_set
    game = _game(reference, change.game if change.game is not None else entry.game)
    members = None
    if change.members is not None or "game" in fields:
        slugs = change.members
        if slugs is None:
            [stored] = [ms for e, ms in user_repo.hall_of_fame(user) if e.id == entry_id]
            slugs = [member.pokemon for member in stored]
        members = _members(reference, game, slugs)
    entry.game = game.slug
    if change.completed_on is not None:
        entry.completed_on = change.completed_on
    if "notes" in fields:
        entry.notes = change.notes
    user_repo.update_hall_of_fame_entry(user, entry, members)
    return _one(user, reference, entry_id)


def remove_entry(user: Session, entry_id: int) -> None:
    user_repo.remove_hall_of_fame_entry(user, _entry(user, entry_id))


def journey(user: Session, reference: Session, game: GameReference) -> tuple[HallOfFameEntry, ...]:
    """The entries as the engine sees them, ``sequence`` being their order in the journey.

    Each member brings its evolution line and region (CA-18). Entries of games and members of
    forms that are no longer loaded are left out.
    """
    games = reference_repo.all_games(reference)
    result = []
    for order, (entry, members) in enumerate(_in_journey_order(user_repo.hall_of_fame(user)), 1):
        if entry.game not in games:
            continue
        team = tuple(
            JourneyMember(
                m.pokemon,
                game.forms[m.pokemon].evolution_chain,
                game.forms[m.pokemon].region,
                game.forms[m.pokemon].name,
            )
            for m in members
            if m.pokemon in game.forms
        )
        found = games[entry.game]
        result.append(
            HallOfFameEntry(entry.game, found.generation, order, team, game_name=found.name_es)
        )
    return tuple(result)


def _entry(user: Session, entry_id: int) -> user_db.HallOfFameEntry:
    found = user_repo.hall_of_fame_entry(user, entry_id)
    if found is None:
        raise NotFoundError(f"El registro {entry_id} no existe en el Hall of Fame")
    return found


def _game(reference: Session, slug: str) -> Game:
    found = reference_repo.all_games(reference).get(slug)
    if found is None:
        raise InvalidValueError(f"El juego {slug} no existe en los datos cargados")
    return found


def _members(reference: Session, game: Game, slugs: Sequence[str]) -> list[MemberRow]:
    """Each form with its types in the game's generation (RN-10), copied (CA-07)."""
    types = reference_repo.types_in_generation(reference, slugs, game.generation)
    missing = sorted({slug for slug in slugs if slug not in types})
    if missing:
        raise InvalidValueError(
            f"Pokémon que no existen en {game.name_es} ({game.generation}.ª generación): "
            f"{', '.join(missing)}"
        )
    return [(slug, types[slug]) for slug in slugs]


@dataclass(frozen=True)
class _Names:
    """The loaded games, and the Spanish names of the forms and those with image, to show the
    entries."""

    games: dict[str, Game]
    pokemon: dict[str, str]
    with_image: set[str]


def _out(
    entry: user_db.HallOfFameEntry,
    members: list[user_db.HallOfFameMember],
    order: int,
    last: bool,
    names: _Names,
) -> HallOfFameEntryOut:
    assert entry.id is not None
    game = names.games.get(entry.game)
    return HallOfFameEntryOut(
        id=entry.id,
        game=entry.game,
        game_name=game.name_es if game else entry.game,
        generation=game.generation if game else None,
        cover_url=cover_url(entry.game, game is not None and game.cover is not None),
        cover_source_url=cover_source_url(game),
        completed_on=entry.completed_on,
        notes=entry.notes,
        order=order,
        last=last,
        members=[
            HallOfFameMemberOut(
                position=m.position,
                pokemon=m.pokemon,
                name=names.pokemon.get(m.pokemon, m.pokemon),
                types=list(m.types),
                image_url=image_url(m.pokemon, m.pokemon in names.with_image),
            )
            for m in members
        ],
    )
