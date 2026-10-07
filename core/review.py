"""Unverified data that takes part in a generation and has to be confirmed first (RN-18).

Some data cannot be loaded reliably and is *inferred* (with a proposal) or *pending* (without
one). Before generating, the user confirms every such value that takes part in the
generation (RF-15, CA-30):

- the target game's data: its mechanics and, if RN-17 is active, its key battles (they are
  used nowhere else);
- the data of each favourite that is not already discarded with known data, such as whether
  it can arrive at the game before completing it (RN-03);
- if RN-21 is active, the same data of the game's starters that are not favourites, because
  the rule can choose one as a member of the team (CA-65, CA-66): ``with_starters`` adds
  them to the favourites.

Known data is automatic or already confirmed. A favourite is already discarded if a candidate
filter excludes it with known data alone: it appeared in a later generation, its existence or
arrival is known to be false, its line cannot be bred (RN-11) or the journey excludes it
(RN-16). Nothing about it is asked then: Zapdos is not bred, so whether it can arrive does not
matter.

``involved_facts`` returns every value that takes part, whatever its origin, so the API can
show the reviewable ones with their state and say which confirmed data a generation used
(RF-09). ``engine.generate`` never receives unverified data: the API calls ``pending_facts``
first and does not generate while it returns something (docs/02-ddt/api.md).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from core import breeding, journey
from core.domain import GameInfo, HallOfFameEntry, PokemonData
from core.rules.catalog import RuleSettings

# A yes/no value (a mechanic, whether a form exists or can arrive) or the Pokémon of a key
# battle, in the order of its team.
type FactValue = bool | tuple[str, ...]


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
    value: FactValue | None = None

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


def _favorite_facts(
    favorite: FavoriteFacts,
    game: GameInfo,
    settings: RuleSettings,
    entries: Sequence[HallOfFameEntry],
) -> tuple[Fact, ...]:
    """The values of a favourite that take part: none if known data already discards it.

    Mirrors the order of the candidate filters: when its existence or its arrival is known to
    be false, that value is what discards it, so it takes part (and so does the existence
    checked before the arrival).
    """
    pokemon = favorite.pokemon
    if pokemon.generation > game.generation:
        return ()
    if favorite.exists.known_false:
        return (favorite.exists,)
    if favorite.arrival.known_false:
        return (favorite.exists, favorite.arrival)
    if settings.is_enabled("RN-11") and not breeding.can_be_bred(pokemon):
        return ()
    if settings.is_enabled("RN-16") and (
        journey.excluding_entry(pokemon, entries, game.generation) is not None
    ):
        return ()
    return (favorite.exists, favorite.arrival)


def with_starters(
    favorites: Sequence[FavoriteFacts], starters: Sequence[FavoriteFacts], settings: RuleSettings
) -> list[FavoriteFacts]:
    """The favourites and, if RN-21 is active, the game's ``starters`` that are not
    favourites: the rule can choose one as a member of the team (CA-65, CA-66)."""
    if not settings.is_enabled("RN-21"):
        return list(favorites)
    chosen = {favorite.pokemon.slug for favorite in favorites}
    return [*favorites, *(s for s in starters if s.pokemon.slug not in chosen)]


def involved_facts(
    game: GameInfo,
    game_facts: Sequence[Fact],
    favorites: Sequence[FavoriteFacts],
    settings: RuleSettings,
    entries: Sequence[HallOfFameEntry] = (),
) -> tuple[Fact, ...]:
    """Every reviewable value that takes part in a generation, whatever its origin.

    First the game's (in the given order; key battles only with RN-17), then each
    favourite's, existence before arrival, in canonical order of the favourites. A favourite
    already discarded with known data only brings the known value that discards it, if any.
    """
    key_battles_count = settings.is_enabled("RN-17")
    involved = [
        fact for fact in game_facts if fact.kind is not FactKind.KEY_BATTLE or key_battles_count
    ]
    for favorite in sorted(favorites, key=lambda f: (f.pokemon.dex_number, f.pokemon.slug)):
        involved.extend(_favorite_facts(favorite, game, settings, entries))
    return tuple(involved)


def pending_facts(
    game: GameInfo,
    game_facts: Sequence[Fact],
    favorites: Sequence[FavoriteFacts],
    settings: RuleSettings,
    entries: Sequence[HallOfFameEntry] = (),
) -> tuple[Fact, ...]:
    """The inferred or pending values that take part in a generation, to confirm first.

    The unknown values of ``involved_facts``, in the same order. Empty means the generation
    can go ahead.
    """
    involved = involved_facts(game, game_facts, favorites, settings, entries)
    return tuple(fact for fact in involved if not fact.is_known)
