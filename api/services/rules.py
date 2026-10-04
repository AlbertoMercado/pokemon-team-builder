"""Rule settings: which configurable rules are active and the weights (RF-06, RF-07).

user.sqlite only keeps the rules the user has changed; the rest use the catalogue's
defaults (CA-41). ``core.rules.catalog.RuleSettings`` validates every change.
"""

from sqlmodel import Session

from api.errors import ConflictError, NotFoundError
from api.repositories import user as user_repo
from api.schemas.rules import RuleOut, RulePatch
from core.rules.catalog import CATALOG, RuleKind, RuleSettings, SettingsError


def current_settings(user: Session) -> RuleSettings:
    """The user's settings: the defaults with the stored changes applied."""
    rows = user_repo.rule_settings(user)
    return RuleSettings.defaults().with_changes(
        enabled={row.rule_id: row.enabled for row in rows},
        weights={row.rule_id: row.weight for row in rows if row.weight is not None},
    )


def _out(rule_id: str, settings: RuleSettings) -> RuleOut:
    rule = CATALOG[rule_id]
    soft = rule.kind is RuleKind.SOFT
    return RuleOut(
        rule_id=rule.rule_id,
        name=rule.name,
        description=rule.description,
        kind=rule.kind,
        configurable=rule.configurable,
        enabled=settings.is_enabled(rule_id),
        weight=settings.weight(rule_id) if soft else None,
        default_weight=rule.default_weight,
    )


def list_rules(user: Session) -> list[RuleOut]:
    """Every rule of the catalogue, in its order, with its current state."""
    settings = current_settings(user)
    return [_out(rule_id, settings) for rule_id in CATALOG]


def update_rule(user: Session, rule_id: str, change: RulePatch) -> RuleOut:
    if rule_id not in CATALOG:
        raise NotFoundError(f"La regla {rule_id} no existe en el catálogo")
    try:
        settings = current_settings(user).with_changes(
            enabled=None if change.enabled is None else {rule_id: change.enabled},
            weights=None if change.weight is None else {rule_id: change.weight},
        )
    except SettingsError as error:
        raise ConflictError(str(error)) from error
    soft = CATALOG[rule_id].kind is RuleKind.SOFT
    user_repo.save_rule_setting(
        user,
        rule_id,
        settings.is_enabled(rule_id),
        settings.weight(rule_id) if soft else None,
    )
    return _out(rule_id, settings)
