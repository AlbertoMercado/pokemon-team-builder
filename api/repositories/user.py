"""Reads and writes of user.sqlite: favourites, rule settings, confirmations and the Hall of
Fame."""

from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime

from sqlmodel import Session, col, func, select

from db.user import (
    ConfirmedValue,
    FactConfirmation,
    Favorite,
    HallOfFameEntry,
    HallOfFameMember,
    RuleSetting,
)


def favorites(user: Session) -> Sequence[Favorite]:
    return user.exec(select(Favorite)).all()


def add_favorite(user: Session, pokemon: str) -> Favorite:
    """Adds ``pokemon`` if it is not a favourite yet, and returns it either way."""
    found = user.get(Favorite, pokemon)
    if found is None:
        found = Favorite(pokemon=pokemon, added_at=datetime.now(UTC))
        user.add(found)
        user.commit()
        user.refresh(found)
    return found


def remove_favorite(user: Session, pokemon: str) -> bool:
    """Removes ``pokemon``; false if it was not a favourite."""
    found = user.get(Favorite, pokemon)
    if found is None:
        return False
    user.delete(found)
    user.commit()
    return True


def rule_settings(user: Session) -> Sequence[RuleSetting]:
    return user.exec(select(RuleSetting)).all()


def save_rule_setting(user: Session, rule_id: str, enabled: bool, weight: int | None) -> None:
    row = user.get(RuleSetting, rule_id) or RuleSetting(rule_id=rule_id)
    row.enabled = enabled
    row.weight = weight
    user.add(row)
    user.commit()


def confirmations(user: Session, game: str) -> dict[str, FactConfirmation]:
    """The confirmations of ``game``'s reviewable values, by ``fact_key``."""
    rows = user.exec(select(FactConfirmation).where(FactConfirmation.game == game))
    return {row.fact_key: row for row in rows}


def save_confirmations(
    user: Session, game: str, values: Iterable[tuple[str, ConfirmedValue, str]]
) -> datetime:
    """Saves each ``(fact_key, confirmed_value, proposed_value_hash)``, replacing any earlier
    confirmation, in one transaction. Returns when they were confirmed."""
    now = datetime.now(UTC)
    for fact_key, value, proposal_hash in values:
        row = user.get(FactConfirmation, fact_key) or FactConfirmation(
            fact_key=fact_key,
            game=game,
            confirmed_value=value,
            proposed_value_hash=proposal_hash,
            confirmed_at=now,
        )
        row.game = game
        row.confirmed_value = value
        row.proposed_value_hash = proposal_hash
        row.confirmed_at = now
        user.add(row)
    user.commit()
    return now


# A member to save: its form and its types in the entry's game, in team order.
type MemberRow = tuple[str, tuple[str, ...]]


def hall_of_fame(user: Session) -> list[tuple[HallOfFameEntry, list[HallOfFameMember]]]:
    """Every entry with its members by position, in order of registration."""
    entries = user.exec(select(HallOfFameEntry).order_by(col(HallOfFameEntry.sequence))).all()
    members: dict[int, list[HallOfFameMember]] = {}
    for member in user.exec(select(HallOfFameMember).order_by(col(HallOfFameMember.position))):
        members.setdefault(member.entry, []).append(member)
    return [(entry, members.get(entry.id or 0, [])) for entry in entries]


def hall_of_fame_entry(user: Session, entry_id: int) -> HallOfFameEntry | None:
    return user.get(HallOfFameEntry, entry_id)


def add_hall_of_fame_entry(
    user: Session, game: str, completed_on: date, notes: str | None, members: list[MemberRow]
) -> HallOfFameEntry:
    """Registers an entry after the others: its ``sequence`` is the next one."""
    last = user.exec(select(func.max(HallOfFameEntry.sequence))).one()
    entry = HallOfFameEntry(
        game=game, completed_on=completed_on, sequence=(last or 0) + 1, notes=notes
    )
    user.add(entry)
    user.flush()
    _add_members(user, entry, members)
    user.commit()
    user.refresh(entry)
    return entry


def update_hall_of_fame_entry(
    user: Session, entry: HallOfFameEntry, members: list[MemberRow] | None
) -> None:
    """Saves the changed fields of ``entry`` and, if given, replaces its members."""
    user.add(entry)
    if members is not None:
        for member in user.exec(select(HallOfFameMember).where(HallOfFameMember.entry == entry.id)):
            user.delete(member)
        user.flush()
        _add_members(user, entry, members)
    user.commit()


def remove_hall_of_fame_entry(user: Session, entry: HallOfFameEntry) -> None:
    """Removes the entry; the database removes its members (``ON DELETE CASCADE``)."""
    user.delete(entry)
    user.commit()


def _add_members(user: Session, entry: HallOfFameEntry, members: list[MemberRow]) -> None:
    assert entry.id is not None
    user.add_all(
        HallOfFameMember(entry=entry.id, position=position, pokemon=pokemon, types=list(types))
        for position, (pokemon, types) in enumerate(members, start=1)
    )
