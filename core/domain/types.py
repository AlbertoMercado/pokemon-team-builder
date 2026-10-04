"""Type chart of a generation (RN-10).

Factors are exact fractions (ADR-0006): 0, 1/2, 1 or 2 for one defending type, and their
product against a Pokémon with two types (1/4 to 4).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

# Factors are loaded in hundredths (docs/02-ddt/modelo-datos.md, ``type_efficacy``).
VALID_HUNDREDTHS = frozenset({0, 50, 100, 200})


class TypeChartError(ValueError):
    """The type chart is incomplete, has invalid factors or is asked about an unknown type."""


@dataclass(frozen=True)
class TypeChart:
    """Damage factors between the types of one generation.

    Not hashable: ``factors`` is a read-only mapping. Build it with ``from_hundredths``.
    """

    generation: int
    types: tuple[str, ...]
    factors: Mapping[tuple[str, str], Fraction]

    @classmethod
    def from_hundredths(
        cls, generation: int, types: Iterable[str], factors: Mapping[tuple[str, str], int]
    ) -> "TypeChart":
        """Build a chart from factors in hundredths; every pair of ``types`` is required."""
        type_list = tuple(types)
        expected = {(a, d) for a in type_list for d in type_list}
        missing = sorted(expected - set(factors))
        extra = sorted(set(factors) - expected)
        if missing or extra:
            raise TypeChartError(f"pares que faltan {missing[:5]} o sobran {extra[:5]}")
        invalid = {pair: f for pair, f in factors.items() if f not in VALID_HUNDREDTHS}
        if invalid:
            raise TypeChartError(f"factores no válidos: {invalid}")
        exact = {pair: Fraction(f, 100) for pair, f in factors.items()}
        return cls(generation=generation, types=type_list, factors=MappingProxyType(exact))

    def factor(self, attacking: str, defending: Iterable[str]) -> Fraction:
        """Factor of an ``attacking`` type against a Pokémon with the ``defending`` types."""
        result = Fraction(1)
        for defending_type in defending:
            try:
                result *= self.factors[(attacking, defending_type)]
            except KeyError:
                raise TypeChartError(
                    f"{attacking} contra {defending_type}: tipo desconocido en la generación "
                    f"{self.generation}"
                ) from None
        return result

    def has_type(self, type_name: str) -> bool:
        return type_name in self.types
