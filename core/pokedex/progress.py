"""The progress of a Pokédex and the Pokémon to register next (RN-22, RN-23).

A species is impossible if the user marked it or if it can only be obtained from spin-offs
(RN-25). Impossible species count in the total and not as registered (CA-71).
"""

from collections.abc import Set
from dataclasses import dataclass
from enum import StrEnum

from core.pokedex.domain import PokedexContext
from core.pokedex.obtention import obtention_methods


class PokedexStatus(StrEnum):
    """States of a Pokédex (RN-22)."""

    NOT_STARTED = "not_started"  # the initial list was not confirmed yet (RF-21)
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True)
class Progress:
    """How much of a Pokédex is registered (RN-22).

    ``percent`` is rounded down, so 100 only appears with the Pokédex completed.
    ``impossible`` counts the species marked by the user and the automatic ones (RN-25).
    """

    registered: int
    total: int
    impossible: int
    status: PokedexStatus

    @property
    def percent(self) -> int:
        return self.registered * 100 // self.total if self.total else 0


def impossible_species(ctx: PokedexContext) -> frozenset[str]:
    """Species not registered that the user marked or that are impossible automatically."""
    automatic = {
        entry.species
        for entry in ctx.species
        if entry.species not in ctx.registered | ctx.impossible
        and obtention_methods(ctx, entry.species).automatically_impossible
    }
    return ctx.impossible | automatic


def progress(ctx: PokedexContext) -> Progress:
    """The progress of the Pokédex of ``ctx`` (RN-22)."""
    registered, total = len(ctx.registered), len(ctx.species)
    if not ctx.started:
        status = PokedexStatus.NOT_STARTED
    elif registered == total:
        status = PokedexStatus.COMPLETED
    else:
        status = PokedexStatus.IN_PROGRESS
    return Progress(registered, total, len(impossible_species(ctx)), status)


def objective(ctx: PokedexContext, skipped: Set[str] = frozenset()) -> str | None:
    """The first species, in the Pokédex order, neither registered nor impossible (RN-23).

    ``skipped`` are the ones the user skipped for now; they are not kept (CA-77). ``None``
    when no species is left.
    """
    left_out = ctx.registered | ctx.impossible | skipped
    for entry in ctx.species:
        if entry.species in left_out:
            continue
        if not obtention_methods(ctx, entry.species).automatically_impossible:
            return entry.species
    return None
