"""Reads and writes of user.sqlite: favourites, rule settings and confirmations."""

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

from sqlmodel import Session, select

from db.user import ConfirmedValue, FactConfirmation, Favorite, RuleSetting


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
