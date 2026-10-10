"""What each encounter of PokeAPI is, and the ways of obtaining a species in the game (RN-26).

Each encounter becomes a way with its kind, in the order of RN-26. Those that depend on an
event (CA-82) or on the starter chosen (RN-24) are kinds of their own, because RN-24 puts
them almost last, and those of spin-offs are left out (RN-25). The conditions that do not
change the kind are kept to show them (CA-85): story progress is dropped, the time of day
becomes ``times`` (CA-81) and the starter or the TV option becomes ``choice`` (CA-80).

A gift where one of several Pokémon is chosen depends on the context (CA-87): the game's own
starters are gifts that depend on the starter chosen, and the others say among which ones
the choice is (``shared_gifts``).

An encounter method this module does not know raises an error: the load checks that every
method of the loaded games is one of these (``ingest/checks.py``).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from itertools import groupby


class EncounterKind(StrEnum):
    """Kinds of RN-26 in their order, then the two that RN-24 puts almost last."""

    GIFT = "gift"
    NPC_TRADE = "npc_trade"
    FOSSIL = "fossil"
    STATIC = "static"
    WILD = "wild"
    SWARM = "swarm"  # CA-85
    ROAMING = "roaming"
    STARTER_GIFT = "starter_gift"  # form 6 of RN-24
    EVENT = "event"  # form 7 of RN-24: a place reached with an event item, Virtual Console


IN_GAME_KINDS = (
    EncounterKind.GIFT,
    EncounterKind.NPC_TRADE,
    EncounterKind.FOSSIL,
    EncounterKind.STATIC,
    EncounterKind.WILD,
    EncounterKind.SWARM,
    EncounterKind.ROAMING,
)

SPIN_OFF_METHODS = frozenset(
    {"colosseum-bonus-disc-us", "colosseum-bonus-disc-jpn", "pokemon-channel-pal"}
)
GIFT_METHODS = frozenset({"gift", "gift-egg"})
NPC_TRADE_METHODS = frozenset({"npc-trade"})
# Always there, at 100 % (CA-84: Sudowoodo with the Squirt Bottle or the Wailmer Pail).
STATIC_METHODS = frozenset({"static", "pokeflute", "devon-scope", "squirt-bottle", "wailmer-pail"})
ROAMING_METHODS = frozenset({"roaming-grass", "roaming-water"})
# Wild methods in the order that breaks ties of probability (RN-26, CA-84).
WILD_METHOD_ORDER = {
    "walk": 0,
    "surf": 1,
    "seaweed": 2,
    "old-rod": 3,
    "good-rod": 4,
    "super-rod": 5,
    "feebas-tile-fishing": 6,
    "rock-smash": 7,
    "headbutt-low": 7,
    "headbutt-normal": 7,
    "headbutt-high": 7,
}

FOSSIL_CONDITIONS = frozenset(
    {
        "item-helix-fossil",
        "item-dome-fossil",
        "item-old-amber",
        "item-root-fossil",
        "item-claw-fossil",
    }
)
CHOICE_PREFIXES = ("starter-", "tv-option-")  # CA-80, CA-85
TIME_PREFIX = "time-"  # CA-81
IGNORED_PREFIXES = ("story-progress-",)  # RN-26: the game is completed
NO_SWARM = "swarm-no"
SWARM = "swarm-yes"
VIRTUAL_CONSOLE = "other-virtual-console"  # CA-82
ALL_TIMES = frozenset({"morning", "day", "night"})


# The kind of each method before its conditions (CA-82 to CA-85).
METHOD_KINDS = {
    **dict.fromkeys(GIFT_METHODS, EncounterKind.GIFT),
    **dict.fromkeys(NPC_TRADE_METHODS, EncounterKind.NPC_TRADE),
    **dict.fromkeys(STATIC_METHODS, EncounterKind.STATIC),
    **dict.fromkeys(ROAMING_METHODS, EncounterKind.ROAMING),
    **dict.fromkeys(WILD_METHOD_ORDER, EncounterKind.WILD),
}


@dataclass(frozen=True)
class Encounter:
    """A way of obtaining a species in a place of a game, as PokeAPI gives it (RN-26).

    ``conditions`` are PokeAPI's (``time-night``, ``starter-squirtle``…). ``event_item`` is
    the event item without which the place cannot be reached (CA-82).
    """

    location: str
    method: str
    rarity: int = 100
    conditions: tuple[str, ...] = ()
    area: str | None = None
    event_item: str | None = None


# A place where a gift is given: location, area and method.
type GiftPlace = tuple[str, str | None, str]


class UnknownEncounterMethodError(ValueError):
    """An encounter method that RN-26 does not classify yet."""


@dataclass(frozen=True)
class InGameWay:
    """One way of obtaining a species in a game, from its encounters (RN-26).

    ``rarity`` is the probability in percent; with ``times``, the highest of those moments of
    the day (CA-81). ``choice`` is the starter or TV option it depends on (``starter-squirtle``,
    ``tv-option-red``). ``item`` is the fossil to revive or the event item that reaches the
    place. ``conditions`` are the rest of PokeAPI's conditions, to show them with the way
    (``coins-9999``, ``trade-abra``, ``weekday-friday``…). ``alternatives`` are the other
    Pokémon of a gift where only one is chosen (CA-87).
    """

    kind: EncounterKind
    location: str
    method: str
    rarity: int
    area: str | None = None
    times: tuple[str, ...] = ()
    choice: str | None = None
    item: str | None = None
    conditions: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        """Stable identifier of the way, to keep the one the user chooses (RF-23)."""
        place = f"{self.location}/{self.area}" if self.area else self.location
        extra = [c for c in (self.choice, self.item, *self.conditions) if c is not None]
        return "+".join([f"{self.method}@{place}", *extra])


@dataclass(frozen=True)
class _Classified:
    kind: EncounterKind
    choice: str | None
    item: str | None
    time: str | None
    conditions: tuple[str, ...]
    alternatives: tuple[str, ...] = ()


def _kind(encounter: Encounter, choice: str | None, swarm: bool) -> EncounterKind | None:
    """The kind of ``encounter``; ``None`` for a spin-off (RN-25)."""
    if encounter.method in SPIN_OFF_METHODS:
        return None
    if encounter.method not in METHOD_KINDS:
        raise UnknownEncounterMethodError(f"método de aparición sin clasificar: {encounter.method}")
    kind = METHOD_KINDS[encounter.method]
    if encounter.event_item is not None or VIRTUAL_CONSOLE in encounter.conditions:
        kind = EncounterKind.EVENT
    elif kind in {EncounterKind.GIFT, EncounterKind.NPC_TRADE} and choice is not None:
        kind = EncounterKind.STARTER_GIFT
    elif kind is EncounterKind.GIFT and FOSSIL_CONDITIONS & set(encounter.conditions):
        kind = EncounterKind.FOSSIL
    elif kind is EncounterKind.WILD and swarm:
        kind = EncounterKind.SWARM
    return kind


def _classify(
    encounter: Encounter,
    species: str,
    starters: frozenset[str],
    shared: Mapping[GiftPlace, tuple[str, ...]],
) -> _Classified | None:
    choice = item = time = None
    rest: list[str] = []
    for condition in encounter.conditions:
        if condition.startswith(CHOICE_PREFIXES):
            choice = condition
        elif condition in FOSSIL_CONDITIONS:
            item = condition.removeprefix("item-")
        elif condition.startswith(TIME_PREFIX):
            time = condition.removeprefix(TIME_PREFIX)
        elif condition.startswith(IGNORED_PREFIXES) or condition in {NO_SWARM, SWARM}:
            continue
        else:
            rest.append(condition)
    kind = _kind(encounter, choice, SWARM in encounter.conditions)
    if kind is None:
        return None
    if encounter.event_item is not None:
        item = encounter.event_item
    alternatives: tuple[str, ...] = ()
    if kind is EncounterKind.GIFT and not encounter.conditions:
        if species in starters:
            kind, choice = EncounterKind.STARTER_GIFT, f"starter-{species}"
        else:
            place = (encounter.location, encounter.area, encounter.method)
            alternatives = tuple(s for s in shared.get(place, ()) if s != species)
    return _Classified(kind, choice, item, time, tuple(rest), alternatives)


def _merge(group: list[tuple[Encounter, _Classified]]) -> InGameWay:
    """One way from the rows of a place that differ only in the time of day (CA-81)."""
    best = max(encounter.rarity for encounter, _ in group)
    times = {c.time for encounter, c in group if encounter.rarity == best}
    shown = () if None in times or times >= ALL_TIMES else tuple(sorted(t for t in times if t))
    encounter, classified = group[0]
    return InGameWay(
        kind=classified.kind,
        location=encounter.location,
        method=encounter.method,
        rarity=best,
        area=encounter.area,
        times=shown,
        choice=classified.choice,
        item=classified.item,
        conditions=classified.conditions,
        alternatives=classified.alternatives,
    )


def _order(way: InGameWay) -> tuple[int, int, int, str, str]:
    kinds = list(EncounterKind)
    return (
        kinds.index(way.kind),
        -way.rarity,
        WILD_METHOD_ORDER.get(way.method, 0),
        way.location,
        way.area or "",
    )


def shared_gifts(
    encounters: Mapping[str, Iterable[Encounter]],
) -> dict[GiftPlace, tuple[str, ...]]:
    """Places where one of several Pokémon is given, from the encounters of a game by species.

    Only gifts without conditions: those with conditions (prizes, fossils) can all be
    obtained (CA-87). The Pokémon keep the order of ``encounters``.
    """
    places: dict[GiftPlace, list[str]] = {}
    for species, rows in encounters.items():
        for e in rows:
            if METHOD_KINDS.get(e.method) is EncounterKind.GIFT and not e.conditions:
                given = places.setdefault((e.location, e.area, e.method), [])
                if species not in given:
                    given.append(species)
    return {place: tuple(given) for place, given in places.items() if len(given) > 1}


def in_game_ways(
    encounters: Iterable[Encounter],
    species: str = "",
    starters: frozenset[str] = frozenset(),
    shared: Mapping[GiftPlace, tuple[str, ...]] | None = None,
) -> tuple[InGameWay, ...]:
    """Every way of obtaining ``species`` from its encounters, in the order of RN-26.

    The ways of the starter gifts and the events go last, in that order (RN-24). Spin-offs
    are left out (RN-25). ``starters`` are the species received as the game's starter and
    ``shared``, the places where one of several gifts is chosen (CA-87).
    """
    shared = shared or {}
    classified = [
        (e, c) for e in encounters if (c := _classify(e, species, starters, shared)) is not None
    ]

    def place(item: tuple[Encounter, _Classified]) -> tuple[str, ...]:
        encounter, c = item
        return (
            c.kind,
            encounter.location,
            encounter.area or "",
            encounter.method,
            c.choice or "",
            c.item or "",
            *c.conditions,
        )

    ways = [_merge(list(group)) for _, group in groupby(sorted(classified, key=place), key=place)]
    return tuple(sorted(ways, key=_order))


def has_spin_off(encounters: Iterable[Encounter]) -> bool:
    """Some encounter is of a spin-off (RN-25)."""
    return any(encounter.method in SPIN_OFF_METHODS for encounter in encounters)
