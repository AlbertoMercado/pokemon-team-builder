"""The category of each evolution trigger and condition, as data (RN-15, RN-20, CA-42).

Deciding what is tedious depends on how the game is played, so it is curated data
(``data/curated/evolution_methods.yaml``), not code. The engine receives it in its context:
a trigger or condition without category is an error, since the load blocks before storing one
(ADR-0008).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class Tedium(StrEnum):
    """Why an evolution step is tedious (RN-15, CA-20, CA-35)."""

    TRADE = "trade"  # trade, with or without an item or a given Pokémon
    SHED = "shed"  # Nincada → Shedinja: a free slot and a Poké Ball
    RANDOM = "random"  # the result cannot be chosen (Wurmple); also RN-20
    STATS = "stats"  # comparing Attack and Defense (Tyrogue)
    TIME_OF_DAY = "time_of_day"  # day or night (Eevee → Espeon)
    BEAUTY = "beauty"  # a contest condition (Feebas → Milotic)
    LOCATION = "location"  # level up in a given place or region (Magneton → Magnezone)
    PARTY = "party"  # a given Pokémon or type in the party (Mantyke → Mantine)
    MOVE = "move"  # knowing a move or a move type
    OTHER = "other"  # any other unusual requirement
    IMPOSSIBLE = "impossible"  # the game lacks the mechanic: evolve it in another game


class MethodCategory(StrEnum):
    EASY = "easy"
    TEDIOUS = "tedious"
    RANDOM = "random"  # a random method is tedious too


class EvolutionCatalogError(ValueError):
    """The catalog is not consistent, or a step uses a method it does not have."""


@dataclass(frozen=True)
class EvolutionMethod:
    """The category of a trigger or condition.

    A tedious one has its ``reason``, which cannot be random or impossible: those come from the
    category and from ``requires_mechanic``, the mechanic without which the step is impossible
    in the game. ``unless_learnt_by_level``: it is not tedious if the Pokémon that evolves learns
    the move by level from level 2 in the game (CA-32).
    """

    category: MethodCategory
    reason: Tedium | None = None
    requires_mechanic: str | None = None
    unless_learnt_by_level: bool = False

    def __post_init__(self) -> None:
        if (self.category is MethodCategory.TEDIOUS) != (self.reason is not None):
            raise EvolutionCatalogError("solo un método tedioso lleva motivo, y debe llevarlo")
        if self.reason in (Tedium.RANDOM, Tedium.IMPOSSIBLE):
            raise EvolutionCatalogError(f"el motivo {self.reason} no se cataloga")

    @property
    def tedium(self) -> Tedium | None:
        """Why the method is tedious; ``None`` if it is easy."""
        if self.category is MethodCategory.RANDOM:
            return Tedium.RANDOM
        return self.reason


@dataclass(frozen=True)
class EvolutionCatalog:
    """The category of every trigger and condition, by PokeAPI identifier."""

    triggers: Mapping[str, EvolutionMethod]
    conditions: Mapping[str, EvolutionMethod]

    def trigger(self, name: str) -> EvolutionMethod:
        return _method(self.triggers, name, "disparador")

    def condition(self, name: str) -> EvolutionMethod:
        return _method(self.conditions, name, "condición")


def _method(methods: Mapping[str, EvolutionMethod], name: str, what: str) -> EvolutionMethod:
    try:
        return methods[name]
    except KeyError:
        raise EvolutionCatalogError(f"{what} de evolución sin catalogar: {name}") from None
