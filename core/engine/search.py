"""Backtracking search of teams: independent sets of the incompatibility graph (ADR-0006).

Candidates are numbered in canonical order and each one has a bit set with the candidates it
conflicts with (RN-07, RN-12, RN-14). A team is a set of ``size`` candidates with no
conflicts between them that contains at least one candidate of each required set (RN-13,
RN-14). Teams come out in lexicographic order of their canonical indices, so the result
does not depend on anything but the input (RF-08).
"""

from collections.abc import Callable, Iterator, Sequence
from fractions import Fraction

from core.domain import PokemonData

type Conflicts = Callable[[PokemonData, PokemonData], bool]
type RankingKey = tuple[Fraction, int]


def conflict_masks(candidates: Sequence[PokemonData], conflicts: Conflicts) -> tuple[int, ...]:
    """For each candidate, the bit set of the candidates it cannot go with."""
    masks = [0] * len(candidates)
    for i, a in enumerate(candidates):
        for j in range(i + 1, len(candidates)):
            if conflicts(a, candidates[j]):
                masks[i] |= 1 << j
                masks[j] |= 1 << i
    return tuple(masks)


def teams(
    candidates: Sequence[PokemonData],
    size: int,
    conflicts: Conflicts,
    required: Sequence[frozenset[str]] = (),
) -> Iterator[tuple[PokemonData, ...]]:
    """Every team of ``size`` candidates without conflicts that meets every required set.

    Prunes a branch as soon as too few compatible candidates are left, or a required set can
    no longer be met.
    """
    masks = conflict_masks(candidates, conflicts)
    required_masks = [
        sum(1 << i for i, c in enumerate(candidates) if c.slug in options) for options in required
    ]
    if size <= 0 or any(mask == 0 for mask in required_masks):
        return

    def extend(chosen: list[int], chosen_mask: int, allowed: int) -> Iterator[tuple[int, ...]]:
        missing = size - len(chosen)
        if missing == 0:
            if all(req & chosen_mask for req in required_masks):
                yield tuple(chosen)
            return
        if allowed.bit_count() < missing:
            return
        for req in required_masks:
            if not req & chosen_mask and not req & allowed:
                return
        while allowed:
            low = allowed & -allowed
            index = low.bit_length() - 1
            allowed ^= low
            chosen.append(index)
            yield from extend(chosen, chosen_mask | low, allowed & ~masks[index])
            chosen.pop()
            if allowed.bit_count() < missing:
                return

    for indices in extend([], 0, (1 << len(candidates)) - 1):
        yield tuple(candidates[i] for i in indices)


def best_teams(
    found: Iterator[tuple[PokemonData, ...]],
    ranking_key: Callable[[tuple[PokemonData, ...]], RankingKey],
) -> tuple[RankingKey | None, list[tuple[PokemonData, ...]]]:
    """The teams with the highest ranking key (RN-04, RN-19), in the order they were found."""
    best: RankingKey | None = None
    winners: list[tuple[PokemonData, ...]] = []
    for team in found:
        key = ranking_key(team)
        if best is None or key > best:
            best, winners = key, [team]
        elif key == best:
            winners.append(team)
    return best, winners
