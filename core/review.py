"""Unverified data that takes part in a generation and has to be confirmed first (RN-18).

Some data cannot be loaded reliably and is *inferred* (with a proposal) or *pending* (without
one). Before generating, the user confirms every such value that takes part in the
generation (RF-15, CA-30):

- the target game's data: its mechanics and, if RN-17 is active, its key battles (they are
  used nowhere else);
- the data of each favourite that is not already discarded with known data, such as whether
  it can arrive at the game before completing it (RN-03).

Known data is automatic or already confirmed. A favourite is already discarded if a candidate
filter excludes it with known data alone: it appeared in a later generation, its existence or
arrival is known to be false, its line cannot be bred (RN-11) or the journey excludes it
(RN-16). Nothing about it is asked then: Zapdos is not bred, so whether it can arrive does not
matter.

``engine.generate`` never receives unverified data: the API calls ``pending_facts`` first and
does not generate while it returns something (docs/02-ddt/api.md).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from core import breeding, journey
from core.domain import ConditionValue, GameInfo, HallOfFameEntry, PokemonData
from core.rules.catalog import RuleSettings


class Origin(StrEnum):
    """Where a reviewable value comes from (RN-18, docs/02-ddt/datos-requeridos.md)."""

    AUTOMATIC = "automatic"  # loaded from a source without ambiguity
    INFERRED = "inferred"  # proposed, without certainty
    PENDING = "pending"  # no proposal
    CONFIRMED = "confirmed"  # reviewed by the user

    @property
    def is_known(self) -> bool:
        return self in {Origin.AUTOMATIC, Origin.CONFIRMED}


class FactKind(StrEnum):
    MECHANIC = "mechanic"  # a mechanic of the game, like the day and night cycle
    KEY_BATTLE = "key_battle"  # a key battle and its team (RN-17)
    EXISTS = "exists"  # a form can be had in the game (RN-03)
    ARRIVAL = "arrival"  # a form can arrive and evolve before completing the game (RN-03)


@dataclass(frozen=True)
class Fact:
    """A reviewable value with its stable key (``fact_key``) and its origin.

    ``value`` is the proposal (inferred), the loaded value (automatic) or the user's value
    (confirmed); ``None`` only when pending.
    """

    key: str
    kind: FactKind
    origin: Origin
    value: ConditionValue | None = None

    def __post_init__(self) -> None:
        if (self.value is None) != (self.origin is Origin.PENDING):
            raise ValueError(f"{self.key}: solo un dato pendiente no tiene valor")

    @property
    def is_known(self) -> bool:
        return self.origin.is_known

    @property
    def known_false(self) -> bool:
        return self.is_known and self.value is False


@dataclass(frozen=True)
class FavoriteFacts:
    """A favourite with the reviewable values of its availability in the target game."""

    pokemon: PokemonData
    exists: Fact
    arrival: Fact


def _discarded_with_known_data(
    favorite: FavoriteFacts,
    game: GameInfo,
    settings: RuleSettings,
    entries: Sequence[HallOfFameEntry],
) -> bool:
    pokemon = favorite.pokemon
    if pokemon.generation > game.generation:
        return True
    if favorite.exists.known_false or favorite.arrival.known_false:
        return True
    if settings.is_enabled("RN-11") and not breeding.can_be_bred(pokemon):
        return True
    return settings.is_enabled("RN-16") and (
        journey.excluding_entry(pokemon, entries, game.generation) is not None
    )


def pending_facts(
    game: GameInfo,
    game_facts: Sequence[Fact],
    favorites: Sequence[FavoriteFacts],
    settings: RuleSettings,
    entries: Sequence[HallOfFameEntry] = (),
) -> tuple[Fact, ...]:
    """The inferred or pending values that take part in a generation, to confirm first.

    First the game's (in the given order; key battles only with RN-17), then each
    favourite's, existence before arrival, in canonical order of the favourites. Empty means
    the generation can go ahead.
    """
    key_battles_count = settings.is_enabled("RN-17")
    pending = [
        fact
        for fact in game_facts
        if not fact.is_known and (fact.kind is not FactKind.KEY_BATTLE or key_battles_count)
    ]
    for favorite in sorted(favorites, key=lambda f: (f.pokemon.dex_number, f.pokemon.slug)):
        if _discarded_with_known_data(favorite, game, settings, entries):
            continue
        pending.extend(f for f in (favorite.exists, favorite.arrival) if not f.is_known)
    return tuple(pending)
