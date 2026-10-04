"""Scores as rounded integers that still add up (CA-51, RF-09).

The engine scores with exact fractions (ADR-0006); the API sends integers. A team's total is
rounded half up, and the contributions of its rules are distributed with the largest
remainder method so they add up to that total: each gets its integer part, and the units left
go to the largest fractional parts (on equal parts, to the first rule in catalogue order).
"""

import math
from collections.abc import Sequence
from fractions import Fraction

HALF = Fraction(1, 2)


def round_half_up(value: Fraction) -> int:
    """The nearest integer; halves go up (18.5 → 19, -0.5 → 0)."""
    return math.floor(value + HALF)


def largest_remainder(parts: Sequence[Fraction]) -> list[int]:
    """``parts`` as integers that add up to ``round_half_up(sum(parts))``.

    Each integer is the part's floor or ceiling, so it differs from the exact part by less
    than 1.
    """
    total = round_half_up(sum(parts, Fraction(0)))
    result = [math.floor(part) for part in parts]
    by_remainder = sorted(range(len(parts)), key=lambda i: (result[i] - parts[i], i))
    for index in by_remainder[: total - sum(result)]:
        result[index] += 1
    return result


def percentage(value: Fraction) -> int:
    """A score between 0 and 1 as a rounded percentage."""
    return round_half_up(value * 100)
