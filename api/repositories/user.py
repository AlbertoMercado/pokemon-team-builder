"""Reads and writes of user.sqlite: favourites and rule settings."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel import Session, select

from db.user import Favorite, RuleSetting


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
