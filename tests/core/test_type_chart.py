"""Type chart of a generation (RN-10, ADR-0006)."""

from fractions import Fraction

import pytest

from core.domain import TypeChart, TypeChartError
from tests.core.builders import GEN1_TYPES, type_chart


def test_factor_against_one_type() -> None:
    chart = type_chart(overrides={("water", "fire"): 200, ("water", "grass"): 50})
    assert chart.factor("water", ["fire"]) == 2
    assert chart.factor("water", ["grass"]) == Fraction(1, 2)
    assert chart.factor("water", ["normal"]) == 1


def test_factor_against_two_types_is_the_product() -> None:
    """Brock's Geodude and Onix (Rock/Ground) take x4 from Water (RN-17 example)."""
    chart = type_chart(overrides={("water", "rock"): 200, ("water", "ground"): 200})
    assert chart.factor("water", ["rock", "ground"]) == 4


def test_immunity_makes_the_product_zero() -> None:
    chart = type_chart(overrides={("electric", "ground"): 0, ("electric", "water"): 200})
    assert chart.factor("electric", ["water", "ground"]) == 0


@pytest.mark.rn("RN-10")
def test_each_generation_has_its_own_chart() -> None:
    """Ghost did not affect Psychic in the 1st generation; from the 2nd it is x2."""
    gen1 = type_chart(1, GEN1_TYPES, {("ghost", "psychic"): 0})
    gen3 = type_chart(3, overrides={("ghost", "psychic"): 200})
    assert gen1.factor("ghost", ["psychic"]) == 0
    assert gen3.factor("ghost", ["psychic"]) == 2
    assert not gen1.has_type("steel")
    assert gen3.has_type("steel")


def test_incomplete_chart_is_rejected() -> None:
    with pytest.raises(TypeChartError, match="faltan"):
        TypeChart.from_hundredths(3, ["water", "fire"], {("water", "fire"): 200})


def test_invalid_factor_is_rejected() -> None:
    factors = {(a, d): 100 for a in ("water", "fire") for d in ("water", "fire")}
    factors[("water", "fire")] = 300
    with pytest.raises(TypeChartError, match="no válidos"):
        TypeChart.from_hundredths(3, ["water", "fire"], factors)


def test_unknown_type_is_an_error() -> None:
    with pytest.raises(TypeChartError, match="fairy"):
        type_chart().factor("fairy", ["dragon"])  # Fairy does not exist in the 3rd generation
