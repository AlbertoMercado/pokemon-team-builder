"""/api/rules: the rule catalogue and the user's settings (RF-06, RF-07)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.database import user_session
from api.schemas.rules import RuleOut, RulePatch
from api.services import rules as service

router = APIRouter(prefix="/rules", tags=["Reglas"])

UserDb = Annotated[Session, Depends(user_session)]


@router.get("", summary="Catálogo de reglas")
def list_rules(user: UserDb) -> list[RuleOut]:
    """Las 20 reglas del catálogo, en orden, con su tipo, si son configurables, si están
    activas y su peso."""
    return service.list_rules(user)


@router.patch("/{rule_id}", summary="Activar, desactivar o cambiar el peso de una regla")
def update_rule(rule_id: str, change: RulePatch, user: UserDb) -> RuleOut:
    """Cambia `enabled`, `weight` (de 0 a 10, solo en las blandas) o los dos. `404` si la regla
    no existe; `409` si no es configurable o no es blanda y se le da peso."""
    return service.update_rule(user, rule_id, change)
