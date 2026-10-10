"""Readable constructors of Pokédex data for the core tests.

Each test only states what matters to it, e.g.
``pokedex(species("bulbasaur"), species("ivysaur", evolves_from="bulbasaur"))``. Species
without a number are numbered in the order they are given.
"""

from collections.abc import Iterable, Mapping
from dataclasses import replace

from core.domain import ConditionValue, EvolutionStep, GameInfo
from core.pokedex import DexSpecies, Encounter, PokedexContext, TransferSource


def encounter(
    location: str = "route-1",
    method: str = "walk",
    rarity: int = 100,
    *conditions: str,
    area: str | None = None,
    event_item: str | None = None,
) -> Encounter:
    return Encounter(location, method, rarity, conditions, area, event_item)


def species(
    slug: str,
    *encounters: Encounter,
    number: int = 0,
    generation: int = 3,
    egg_groups: Iterable[str] = ("field",),
    evolves_from: str | None = None,
    trigger: str = "level-up",
    conditions: Mapping[str, ConditionValue] | None = None,
    evolutions: Iterable[EvolutionStep] = (),
    requires_incense: bool = False,
    is_event: bool = False,
) -> DexSpecies:
    """A species; ``evolves_from`` adds one step (by default, level 16) from that species."""
    steps = list(evolutions)
    if evolves_from is not None:
        level = {"minimum_level": 16} if conditions is None else conditions
        steps.append(EvolutionStep(evolves_from, slug, trigger, tuple(level.items())))
    return DexSpecies(
        species=slug,
        number=number,
        generation=generation,
        egg_groups=frozenset(egg_groups),
        requires_incense=requires_incense,
        evolutions=tuple(steps),
        encounters=encounters,
        is_event=is_event,
    )


def source(
    game: str = "leafgreen",
    encounters: Mapping[str, Iterable[Encounter]] | None = None,
    *,
    registered: Iterable[str] | None = None,
    max_species_generation: int | None = None,
    starters: Iterable[str] = (),
) -> TransferSource:
    """A game that can send Pokémon; completed only if ``registered`` is given."""
    return TransferSource(
        game=game,
        completed=registered is not None,
        registered=frozenset(registered or ()),
        encounters={s: tuple(rows) for s, rows in (encounters or {}).items()},
        max_species_generation=max_species_generation,
        starters=frozenset(starters),
    )


def pokedex(
    *entries: DexSpecies,
    registered: Iterable[str] = (),
    impossible: Iterable[str] = (),
    started: bool = True,
    sources: Iterable[TransferSource] = (),
    starters: Iterable[str] = (),
    has_breeding: bool = True,
    game: str = "firered",
    generation: int = 3,
    mechanics: Iterable[str] = (),
) -> PokedexContext:
    numbered = tuple(
        entry if entry.number else replace(entry, number=index)
        for index, entry in enumerate(entries, start=1)
    )
    return PokedexContext(
        game=GameInfo(game, generation, frozenset(mechanics)),
        has_breeding=has_breeding,
        species=numbered,
        registered=frozenset(registered),
        impossible=frozenset(impossible),
        started=started,
        sources=tuple(sources),
        starters=frozenset(starters),
    )
