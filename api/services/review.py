"""Review of the unverified data of a target game: see, confirm or correct it (RF-15, RN-18).

Only inferred or pending values that take part in a generation are shown
(``core.review.involved_facts``). Automatic values are not reviewed. A confirmation keeps the
hash of the proposal it answered: if a later load proposes something else, the value is
pending again.
"""

from sqlmodel import Session

from api.errors import ConflictError, InvalidValueError, NotFoundError
from api.repositories import user as user_repo
from api.schemas.review import (
    LoadedOrigin,
    ReviewFactOut,
    ReviewOut,
    ReviewStatus,
    ReviewValue,
)
from api.services import hall_of_fame
from api.services.context import (
    Confirmations,
    GameReference,
    Reviewable,
    to_stored,
)
from api.services.rules import current_settings
from core.domain import GameInfo
from core.review import FactKind, Origin, involved_facts
from db.user import ConfirmedValue

MECHANIC_NAMES = {"day_night_cycle": "Ciclo de día y noche", "contests": "Concursos"}


def involved_values(user: Session, reference: Session, game: GameReference) -> list[Reviewable]:
    """The values that take part in a generation for the user's favourites, settings and
    journey."""
    confirmations = user_repo.confirmations(user, game.slug)
    favorites = [favorite.pokemon for favorite in user_repo.favorites(user)]
    facts = involved_facts(
        GameInfo(game.slug, game.generation),
        game.game_facts(confirmations),
        game.favorite_facts(favorites, confirmations),
        current_settings(user),
        hall_of_fame.journey(user, reference, game),
    )
    values = [game.reviewable(fact.key) for fact in facts]
    return [value for value in values if value is not None]


def review(user: Session, reference: Session, game: GameReference) -> ReviewOut:
    confirmations = user_repo.confirmations(user, game.slug)
    facts = [
        _out(game, value, confirmations)
        for value in involved_values(user, reference, game)
        if value.origin is not Origin.AUTOMATIC
    ]
    pending = sum(fact.status is ReviewStatus.PENDING for fact in facts)
    return ReviewOut(game=game.slug, pending=pending, facts=facts)


def confirm(user: Session, game: GameReference, fact_key: str, value: ReviewValue) -> ReviewFactOut:
    """Confirms ``fact_key`` with the proposed value or a corrected one."""
    found = game.reviewable(fact_key)
    if found is None:
        raise NotFoundError(f"El dato {fact_key} no existe en {game.slug}")
    if found.origin is Origin.AUTOMATIC:
        raise ConflictError(f"El dato {fact_key} se cargó sin ambigüedad: no hace falta revisarlo")
    stored = _valid_value(game, found, value)
    user_repo.save_confirmations(user, game.slug, [(fact_key, stored, found.proposal_hash)])
    return _out(game, found, user_repo.confirmations(user, game.slug))


def accept_proposals(user: Session, reference: Session, game: GameReference) -> ReviewOut:
    """Confirms at once every inferred proposal still unconfirmed; pending ones stay as they are."""
    confirmations = user_repo.confirmations(user, game.slug)
    accepted: list[tuple[str, ConfirmedValue, str]] = []
    for value in involved_values(user, reference, game):
        proposal = to_stored(value.proposal)
        if (
            value.origin is Origin.INFERRED
            and proposal is not None
            and value.confirmation(confirmations) is None
        ):
            accepted.append((value.key, proposal, value.proposal_hash))
    if accepted:
        user_repo.save_confirmations(user, game.slug, accepted)
    return review(user, reference, game)


def _valid_value(game: GameReference, fact: Reviewable, value: ReviewValue) -> ConfirmedValue:
    """``InvalidValueError`` if ``value`` does not fit the kind of value."""
    if fact.kind is not FactKind.KEY_BATTLE:
        if not isinstance(value, bool):
            raise InvalidValueError(f"{fact.key} es un dato de sí o no: indica true o false")
        return value
    if not isinstance(value, list) or not value:
        raise InvalidValueError(f"{fact.key} es un combate clave: indica la lista de su equipo")
    unknown = sorted({pokemon for pokemon in value if pokemon not in game.types})
    if unknown:
        raise InvalidValueError(
            f"Pokémon que no existen en la {game.generation}.ª generación: {', '.join(unknown)}"
        )
    return value


def fact_name(game: GameReference, value: Reviewable) -> str:
    if value.kind is FactKind.MECHANIC:
        return MECHANIC_NAMES.get(value.subject, value.subject)
    if value.kind is FactKind.KEY_BATTLE:
        return next(b.trainer for b in game.key_battles if b.slug == value.subject)
    return game.forms[value.subject].name


def _out(game: GameReference, value: Reviewable, confirmations: Confirmations) -> ReviewFactOut:
    confirmation = value.confirmation(confirmations)
    stale = confirmations.get(value.key)
    return ReviewFactOut(
        fact_key=value.key,
        kind=value.kind,
        subject=value.subject,
        name=fact_name(game, value),
        origin=LoadedOrigin(value.origin),
        proposal=to_stored(value.proposal),
        status=ReviewStatus.PENDING if confirmation is None else ReviewStatus.CONFIRMED,
        value=None if confirmation is None else confirmation.confirmed_value,
        confirmed_at=None if confirmation is None else confirmation.confirmed_at,
        outdated=confirmation is None and stale is not None,
    )
