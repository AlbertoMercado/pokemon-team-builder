"""Rounded scores that still add up: the largest remainder method (CA-51, RF-09)."""

from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from api.services.rounding import largest_remainder, percentage, round_half_up


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Fraction(37, 2), 19),
        (Fraction(223, 12), 19),
        (Fraction(55, 3), 18),
        (Fraction(-1, 2), 0),
        (Fraction(-3, 4), -1),
        (Fraction(0), 0),
    ],
)
def test_round_half_up(value: Fraction, expected: int) -> None:
    assert round_half_up(value) == expected


@pytest.mark.rn("RN-04")
def test_firered_breakdown_adds_up_to_the_total() -> None:
    """The real FireRed team: 1 + 3 + 10 · 23/24 + 5 = 223/12, shown as 19."""
    parts = [Fraction(1), Fraction(3), Fraction(230, 24), Fraction(5)]
    assert largest_remainder(parts) == [1, 3, 10, 5]


def test_on_equal_remainders_the_first_rule_gets_the_unit() -> None:
    assert largest_remainder([Fraction(1, 2), Fraction(1, 2)]) == [1, 0]


def test_percentage() -> None:
    assert percentage(Fraction(23, 24)) == 96
    assert percentage(Fraction(1)) == 100


fractions = st.fractions(min_value=-10, max_value=10, max_denominator=1000)


@given(st.lists(fractions, max_size=8))
def test_the_rounded_parts_add_up_and_stay_close(parts: list[Fraction]) -> None:
    rounded = largest_remainder(parts)
    assert sum(rounded) == round_half_up(sum(parts, Fraction(0)))
    assert all(abs(r - p) < 1 for r, p in zip(rounded, parts, strict=True))
