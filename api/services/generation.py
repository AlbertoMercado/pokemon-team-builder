"""Generation of teams: build the context, call the engine and translate its result (RF-08).

Also the check of a team chosen in the result (RF-12, CA-53), with the same context.

Nothing is generated nor checked while some data that takes part is unverified (RN-18): the
answer is a ``409`` with the values to confirm, the same the review shows. The result is not
stored: it is a calculation without state. Scores are sent as rounded integers whose
contributions add up to the total (CA-51, ``api.services.rounding``).
"""

from sqlmodel import Session

from api.errors import ConflictError, InvalidValueError
from api.repositories import meta as meta_repo
from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
from api.schemas.generation import (
    ConfirmedFactOut,
    DiscardOut,
    GenerationOut,
    GroupOut,
    OpenSlotsOut,
    PokemonOut,
    PresenceOut,
    RuleScoreOut,
    SuggestionOut,
    TeamOut,
)
from api.schemas.review import ReviewStatus
from api.schemas.team_check import TeamCheckOut, TeamProblemOut
from api.services import hall_of_fame
from api.services import review as review_service
from api.services.context import GameReference, build_context, to_stored
from api.services.images import image_url
from api.services.meta import data_version
from api.services.rounding import largest_remainder, percentage, round_half_up
from api.services.rules import current_settings
from core.domain import GameContext, PokemonData
from core.engine import OpenSlots, RankedTeam, generate
from core.review import Origin
from core.rules.candidate import Discard
from core.rules.catalog import CATALOG
from core.rules.check import UnknownMemberError, check_team
from core.rules.team import PresenceRequirement

PENDING_MESSAGE = "Antes de generar hay que confirmar los datos sin verificar que intervienen"


def _ready_context(user: Session, reference: Session, game: GameReference) -> GameContext:
    """The engine's context; ``ConflictError`` (409) with the pending data if some value that
    takes part is still unverified."""
    review = review_service.review(user, reference, game)
    if review.pending:
        pending = [f for f in review.facts if f.status is ReviewStatus.PENDING]
        raise ConflictError(
            PENDING_MESSAGE, {"pending": [f.model_dump(mode="json") for f in pending]}
        )
    confirmations = user_repo.confirmations(user, game.slug)
    favorites = [favorite.pokemon for favorite in user_repo.favorites(user)]
    journey = hall_of_fame.journey(user, reference, game)
    return build_context(game, favorites, current_settings(user), confirmations, journey)


def check_chosen_team(
    user: Session, reference: Session, game: GameReference, members: list[str]
) -> TeamCheckOut:
    """The problems of a team chosen in the result with the active rules.

    ``InvalidValueError`` (422) if a member is repeated or is not a Pokémon of the game's
    generation; ``ConflictError`` (409) as when generating.
    """
    repeated = sorted({slug for slug in members if members.count(slug) > 1})
    if repeated:
        raise InvalidValueError(f"Pokémon repetidos en el equipo: {', '.join(repeated)}")
    ctx = _ready_context(user, reference, game)
    try:
        check = check_team(ctx, members)
    except UnknownMemberError as error:
        raise InvalidValueError(
            f"Pokémon que no existen en la {game.generation}.ª generación: "
            f"{', '.join(error.members)}"
        ) from error
    return TeamCheckOut(
        valid=check.valid,
        problems=[
            TeamProblemOut(rule_id=p.rule_id, members=list(p.members), detail=p.detail)
            for p in check.problems
        ],
        unverified=list(check.unverified),
    )


def generate_teams(user: Session, reference: Session, game: GameReference) -> GenerationOut:
    """``ConflictError`` (409) with the pending data if some value is still unverified."""
    ctx = _ready_context(user, reference, game)
    confirmations = user_repo.confirmations(user, game.slug)
    result = generate(ctx)

    confirmed = []
    for value in review_service.involved_values(user, reference, game):
        fact = value.fact(confirmations)
        stored = to_stored(fact.value)
        if fact.origin is Origin.CONFIRMED and stored is not None:
            name = review_service.fact_name(game, value)
            confirmed.append(
                ConfirmedFactOut(fact_key=fact.key, kind=fact.kind, name=name, value=stored)
            )
    confirmed_keys = {fact.fact_key for fact in confirmed}

    with_image = reference_repo.forms_with_image(reference)
    return GenerationOut(
        game=game.slug,
        status=result.status,
        incomplete_reason=result.incomplete_reason,
        score=round_half_up(result.teams[0].score.total),
        groups=[
            GroupOut(
                positions=[
                    [_pokemon(p, with_image) for p in alternatives]
                    for alternatives in group.positions
                ],
                teams=[_team(team, with_image) for team in group.teams],
            )
            for group in result.groups
        ],
        discards=[_discard(game, d, confirmed_keys) for d in result.discards],
        presence=[_presence(p) for p in result.presence],
        confirmed_facts=confirmed,
        data_version=data_version(meta_repo.ingest_run(reference)),
    )


def _pokemon(pokemon: PokemonData, with_image: set[str]) -> PokemonOut:
    return PokemonOut(
        pokemon=pokemon.slug,
        name=pokemon.name,
        dex_number=pokemon.dex_number,
        types=list(pokemon.types),
        image_url=image_url(pokemon.slug, pokemon.slug in with_image),
    )


def _team(team: RankedTeam, with_image: set[str]) -> TeamOut:
    breakdown = team.score.breakdown
    contributions = largest_remainder([rule.contribution for rule in breakdown])
    return TeamOut(
        members=list(team.slugs),
        score=sum(contributions),
        dual_type_members=team.score.dual_types,
        breakdown=[
            RuleScoreOut(
                rule_id=rule.rule_id,
                name=CATALOG[rule.rule_id].name,
                weight=rule.weight,
                score=percentage(rule.score),
                contribution=contribution,
                penalized=list(rule.penalized),
            )
            for rule, contribution in zip(breakdown, contributions, strict=True)
        ],
        open_slots=[_slots(slots, with_image) for slots in team.open_slots],
    )


def _slots(slots: OpenSlots, with_image: set[str]) -> OpenSlotsOut:
    return OpenSlotsOut(
        count=slots.count,
        rule_id=slots.rule_id,
        suggestions=[
            SuggestionOut(
                pokemon=_pokemon(s.pokemon, with_image),
                gain=round_half_up(s.gain),
                verified=s.verified,
            )
            for s in slots.suggestions
        ],
    )


def _discard(game: GameReference, discard: Discard, confirmed: set[str]) -> DiscardOut:
    return DiscardOut(
        pokemon=discard.pokemon,
        name=game.forms[discard.pokemon].name,
        rule_id=discard.rule_id,
        reason=discard.reason,
        detail=discard.detail,
        fact_key=discard.fact_key if discard.fact_key in confirmed else None,
    )


def _presence(requirement: PresenceRequirement) -> PresenceOut:
    return PresenceOut(
        rule_id=requirement.rule_id,
        level=requirement.level,
        status=requirement.status,
        options=list(requirement.options),
        detail=requirement.detail,
    )
