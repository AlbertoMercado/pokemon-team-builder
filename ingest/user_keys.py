"""Keys of user.sqlite that must still exist in a new reference.sqlite (ADR-0003).

user.sqlite points to reference.sqlite with natural keys (``vulpix-alola``, ``firered``,
``pokemon:firered:raichu:arrival``), and there cannot be foreign keys between two files. So
before replacing reference.sqlite, the load checks the new one against user.sqlite:

- **Errors** (the load is rejected and the previous database is kept): favourites, games of
  the Hall of Fame and members of its teams that the new load no longer has. They are the
  user's own data: generating without them would silently change the teams.
- **Warnings** (the load goes ahead): confirmations of reviewable values that no longer
  exist. They only answered a question that is no longer asked, so the API ignores them.

Without user.sqlite (the API has never run), or without one of its tables, there is nothing
to check. user.sqlite is only read.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import inspect
from sqlmodel import Session, select

from db.reference import Game, GameMechanic, GamePokemon, KeyBattle, Pokemon
from db.sqlite import create_sqlite_engine
from db.user import FactConfirmation, Favorite, HallOfFameEntry, HallOfFameMember

MAX_LISTED = 10
FIX_RENAMES = (
    "Si es un cambio de identificador en las fuentes, hay que corregir user.sqlite con una "
    "migración de datos (ADR-0003)."
)


@dataclass
class UserKeyProblems:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _ReferenceKeys:
    pokemon: frozenset[str]
    games: frozenset[str]
    facts: frozenset[str]


def _listed(values: Iterable[str]) -> str:
    ordered = sorted(set(values))
    shown = ", ".join(ordered[:MAX_LISTED])
    return shown + (f" y {len(ordered) - MAX_LISTED} más" if len(ordered) > MAX_LISTED else "")


def _reference_keys(reference: Session) -> _ReferenceKeys:
    facts = set(reference.exec(select(GameMechanic.fact_key)))
    facts |= set(reference.exec(select(KeyBattle.fact_key)))
    for game, pokemon in reference.exec(select(GamePokemon.game, GamePokemon.pokemon)):
        facts |= {f"pokemon:{game}:{pokemon}:exists", f"pokemon:{game}:{pokemon}:arrival"}
    return _ReferenceKeys(
        pokemon=frozenset(reference.exec(select(Pokemon.slug))),
        games=frozenset(reference.exec(select(Game.slug))),
        facts=frozenset(facts),
    )


def check_user_keys(reference: Session, user_database: Path) -> UserKeyProblems:
    """What user.sqlite at ``user_database`` uses and the ``reference`` session no longer has."""
    problems = UserKeyProblems()
    if not user_database.exists():
        return problems
    keys = _reference_keys(reference)
    engine = create_sqlite_engine(user_database)
    try:
        tables = set(inspect(engine).get_table_names())
        with Session(engine) as user:
            if Favorite.__tablename__ in tables:
                _check_favorites(user, keys, problems)
            if {HallOfFameEntry.__tablename__, HallOfFameMember.__tablename__} <= tables:
                _check_hall_of_fame(user, keys, problems)
            if FactConfirmation.__tablename__ in tables:
                _check_confirmations(user, keys, problems)
    finally:
        engine.dispose()
    return problems


def _check_favorites(user: Session, keys: _ReferenceKeys, problems: UserKeyProblems) -> None:
    missing = [slug for slug in user.exec(select(Favorite.pokemon)) if slug not in keys.pokemon]
    if missing:
        problems.errors.append(
            f"Favoritos que no existen en la nueva carga: {_listed(missing)}. Quítalos de "
            f"favoritos y repite la carga. {FIX_RENAMES}"
        )


def _check_hall_of_fame(user: Session, keys: _ReferenceKeys, problems: UserKeyProblems) -> None:
    entries = {entry.id: entry for entry in user.exec(select(HallOfFameEntry))}
    games = [f"{e.id} ({e.game})" for e in entries.values() if e.game not in keys.games]
    if games:
        problems.errors.append(
            f"Registros del Hall of Fame con un juego que no existe en la nueva carga: "
            f"{_listed(games)}. Corrígelos o elimínalos y repite la carga. {FIX_RENAMES}"
        )
    members = [
        f"{member.entry} ({member.pokemon})"
        for member in user.exec(select(HallOfFameMember))
        if member.pokemon not in keys.pokemon
    ]
    if members:
        problems.errors.append(
            f"Registros del Hall of Fame con Pokémon que no existen en la nueva carga: "
            f"{_listed(members)}. Corrige sus equipos y repite la carga. {FIX_RENAMES}"
        )


def _check_confirmations(user: Session, keys: _ReferenceKeys, problems: UserKeyProblems) -> None:
    missing = [key for key in user.exec(select(FactConfirmation.fact_key)) if key not in keys.facts]
    if missing:
        problems.warnings.append(
            f"Confirmaciones de datos que ya no existen en la nueva carga (se ignorarán): "
            f"{_listed(missing)}"
        )
