"""Every way of obtaining a species, from the simplest to the least (RN-24, RN-25).

A later stage starts with evolving the previous one, the least tedious method first
(RN-15); methods impossible in the game are left out. Then come the forms of RN-24 in
their order:

1. breed it from another species of its line already registered;
2. transfer it from a completed game where it is registered;
3. obtain it in the game (``core.pokedex.encounters``, RN-26);
4. breed it from another species of its line obtained in the game (form 3);
5. transfer it from a compatible game where it is obtained (form 3 there);
6. a gift that depends on the starter chosen;
7. an event.

Breeding gives the stage that hatches, from a species of its line that lays eggs, and the
incense baby too (CA-86). With no way at all and some spin-off encounter, the species is
impossible to obtain automatically (RN-25).
"""

from dataclasses import dataclass
from enum import StrEnum

from core import breeding
from core.domain import EvolutionStep
from core.evolution import Tedium, step_tedium
from core.pokedex.domain import DexSpecies, PokedexContext, TransferSource
from core.pokedex.encounters import EncounterKind, InGameWay, has_spin_off, in_game_ways


class MethodKind(StrEnum):
    """Forms of RN-24 in their order, after evolving the previous stage."""

    EVOLVE = "evolve"
    BREED_REGISTERED = "breed_registered"  # 1
    TRANSFER_REGISTERED = "transfer_registered"  # 2
    IN_GAME = "in_game"  # 3
    BREED = "breed"  # 4
    TRANSFER = "transfer"  # 5
    STARTER_GIFT = "starter_gift"  # 6
    EVENT = "event"  # 7


@dataclass(frozen=True)
class ObtentionMethod:
    """One way of obtaining a species, with its detail (RF-22).

    ``way`` is the encounter for the forms in the game, the starter gifts and the events in a
    place (CA-82), or the simplest way in ``game`` for a transfer from a game not completed.
    ``game`` is the game to transfer it from. ``pokemon`` is the species to evolve or breed
    from, and ``pokemon_registered`` whether the user has it, to link to it if not (CA-76).
    ``evolution`` is the step to evolve it, and ``incense`` says that breeding it needs an
    incense (CA-86).
    """

    kind: MethodKind
    way: InGameWay | None = None
    game: str | None = None
    pokemon: str | None = None
    pokemon_registered: bool = False
    evolution: EvolutionStep | None = None
    incense: bool = False

    @property
    def key(self) -> str:
        """Stable identifier, to keep the method the user chooses (RF-23, CA-75)."""
        match self.kind:
            case MethodKind.EVOLVE if self.evolution is not None:
                step = self.evolution
                conditions = ",".join(f"{name}={value}" for name, value in step.conditions)
                return f"evolve:{step.from_pokemon}:{step.trigger}:{conditions}"
            case MethodKind.BREED_REGISTERED | MethodKind.BREED:
                return f"breed:{self.pokemon}"
            case MethodKind.TRANSFER_REGISTERED | MethodKind.TRANSFER:
                return f"transfer:{self.game}"
            case _ if self.way is not None:
                return f"{self.kind}:{self.way.key}"
            case _:
                return str(self.kind)


@dataclass(frozen=True)
class Obtention:
    """Every way of obtaining ``species``, simplest first (RN-24).

    ``automatically_impossible`` is true when there is none and some encounter is of a
    spin-off (RN-25).
    """

    species: str
    methods: tuple[ObtentionMethod, ...]
    automatically_impossible: bool

    @property
    def recommended(self) -> ObtentionMethod | None:
        return self.methods[0] if self.methods else None


def _line(ctx: PokedexContext, species: str) -> list[DexSpecies]:
    """Every species of its evolution line in the Pokédex, in the Pokédex order."""
    linked: dict[str, set[str]] = {entry.species: set() for entry in ctx.species}
    for entry in ctx.species:
        for previous in entry.previous:
            linked[entry.species].add(previous)
            linked[previous].add(entry.species)
    seen, pending = {species}, [species]
    while pending:
        for other in linked[pending.pop()] - seen:
            seen.add(other)
            pending.append(other)
    return [entry for entry in ctx.species if entry.species in seen]


def _lays_eggs(entry: DexSpecies) -> bool:
    return bool(entry.egg_groups - breeding.NON_BREEDING_EGG_GROUPS)


def _breeding_parents(ctx: PokedexContext, entry: DexSpecies) -> list[DexSpecies]:
    """The species of its line that lay eggs from which it hatches (CA-25, CA-36, CA-86).

    It hatches if it is the first stage of its line, or the second when the first is an
    incense baby. Empty in a game without breeding (RN-24).
    """
    if not ctx.has_breeding:
        return []
    line = _line(ctx, entry.species)
    first = next(e for e in line if not e.previous)
    second = [e for e in line if e.previous == {first.species}]
    hatches = entry is first or (first.requires_incense and entry in second)
    if not hatches:
        return []
    return [e for e in line if e is not entry and _lays_eggs(e)]


def _evolutions(ctx: PokedexContext, entry: DexSpecies) -> list[ObtentionMethod]:
    """Evolving the previous stage, least tedious first, without the impossible ones."""
    assessed = [(step, step_tedium(step, ctx.game)) for step in entry.evolutions]
    possible = [(step, r) for step, r in assessed if Tedium.IMPOSSIBLE not in r]
    possible.sort(key=lambda item: (Tedium.RANDOM in item[1], len(item[1]), sorted(item[1])))
    return [
        ObtentionMethod(
            MethodKind.EVOLVE,
            pokemon=step.from_pokemon,
            pokemon_registered=step.from_pokemon in ctx.registered,
            evolution=step,
        )
        for step, _ in possible
    ]


def _ways(ctx: PokedexContext, entry: DexSpecies) -> tuple[InGameWay, ...]:
    return in_game_ways(entry.encounters, entry.species, ctx.starters, ctx.gift_choices)


def _obtained_in(ways: tuple[InGameWay, ...]) -> list[InGameWay]:
    """The ways of form 3 of RN-24: neither starter gifts nor events."""
    return [
        way for way in ways if way.kind not in {EncounterKind.STARTER_GIFT, EncounterKind.EVENT}
    ]


def _transfers(
    sources: tuple[TransferSource, ...], entry: DexSpecies
) -> tuple[list[ObtentionMethod], list[ObtentionMethod]]:
    """Transfers from completed games where it is registered and from games where it is
    obtained (forms 2 and 5, RN-25)."""
    registered, obtained = [], []
    for source in sources:
        if not source.can_send(entry):
            continue
        if source.completed and entry.species in source.registered:
            registered.append(ObtentionMethod(MethodKind.TRANSFER_REGISTERED, game=source.game))
            continue
        rows = source.encounters.get(entry.species, ())
        ways = in_game_ways(rows, entry.species, source.starters, source.gift_choices)
        there = _obtained_in(ways)
        if there:
            obtained.append(ObtentionMethod(MethodKind.TRANSFER, way=there[0], game=source.game))
    return registered, obtained


def obtention_methods(ctx: PokedexContext, species: str) -> Obtention:
    """Every way of obtaining ``species`` in the game of ``ctx``, simplest first (RN-24)."""
    entry = ctx.entry(species)
    ways = _ways(ctx, entry)
    in_game = _obtained_in(ways)
    parents = _breeding_parents(ctx, entry)
    incense = entry.requires_incense

    def breed(kind: MethodKind, parent: DexSpecies) -> ObtentionMethod:
        registered = parent.species in ctx.registered
        return ObtentionMethod(
            kind, pokemon=parent.species, pokemon_registered=registered, incense=incense
        )

    from_registered = [p for p in parents if p.species in ctx.registered]
    from_game = [
        p for p in parents if p.species not in ctx.registered and _obtained_in(_ways(ctx, p))
    ]
    transfer_registered, transfer = _transfers(ctx.sources, entry)
    methods = [
        *_evolutions(ctx, entry),
        *(breed(MethodKind.BREED_REGISTERED, p) for p in from_registered),
        *transfer_registered,
        *(ObtentionMethod(MethodKind.IN_GAME, way=way) for way in in_game),
        *(breed(MethodKind.BREED, p) for p in from_game),
        *transfer,
        *(
            ObtentionMethod(MethodKind.STARTER_GIFT, way=way)
            for way in ways
            if way.kind is EncounterKind.STARTER_GIFT
        ),
        *(
            ObtentionMethod(MethodKind.EVENT, way=way)
            for way in ways
            if way.kind is EncounterKind.EVENT
        ),
    ]
    if entry.is_event:
        methods.append(ObtentionMethod(MethodKind.EVENT))
    spin_off = has_spin_off(entry.encounters) or any(
        has_spin_off(source.encounters.get(species, ())) for source in ctx.sources
    )
    return Obtention(species, tuple(methods), not methods and spin_off)
