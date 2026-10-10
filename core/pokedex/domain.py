"""The Pokédex of a completed game as the rules see it (RN-22 to RN-26).

Everything is identified by species, because a Pokédex registers species (RN-22). The
encounters and evolution steps keep PokeAPI's methods and conditions as loaded
(docs/02-ddt/modelo-datos.md): ``core.pokedex.encounters`` decides what each one is.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cached_property

from core.domain import EvolutionStep, GameInfo
from core.pokedex.encounters import Encounter, GiftPlace, shared_gifts


class PokedexContextError(ValueError):
    """The Pokédex context is not consistent."""


@dataclass(frozen=True)
class DexSpecies:
    """A species of the game's Pokédex with what is needed to obtain it there.

    ``number`` is its number in that Pokédex, which sets the order (RN-23). ``evolutions`` are
    the steps that evolve into it in the game, with species identifiers; several steps from
    the same species are alternative methods. ``egg_groups`` are its own, to know whether it
    lays eggs (CA-86). ``is_event`` marks the species obtained by event in the game (RN-24).
    """

    species: str
    number: int
    generation: int
    egg_groups: frozenset[str] = frozenset()
    requires_incense: bool = False
    evolutions: tuple[EvolutionStep, ...] = ()
    encounters: tuple[Encounter, ...] = ()
    is_event: bool = False

    def __post_init__(self) -> None:
        wrong = sorted({s.to_pokemon for s in self.evolutions} - {self.species})
        if wrong:
            raise PokedexContextError(f"{self.species}: pasos de evolución hacia {wrong}")

    @property
    def previous(self) -> frozenset[str]:
        """The species it evolves from in the game; empty if it is the first stage."""
        return frozenset(step.from_pokemon for step in self.evolutions)


@dataclass(frozen=True)
class TransferSource:
    """A game that can send Pokémon to this one (RN-25).

    ``completed`` says whether it is in the Hall of Fame; then ``registered`` are the species
    registered in its Pokédex. ``encounters`` are its encounters by species. With
    ``max_species_generation`` only species up to that generation can be sent (Time Capsule).
    """

    game: str
    completed: bool = False
    registered: frozenset[str] = frozenset()
    encounters: Mapping[str, tuple[Encounter, ...]] = field(default_factory=dict)
    max_species_generation: int | None = None
    starters: frozenset[str] = frozenset()

    @cached_property
    def gift_choices(self) -> dict[GiftPlace, tuple[str, ...]]:
        """Places of the game where one of several gifts is chosen (CA-87)."""
        return shared_gifts(self.encounters)

    def can_send(self, species: DexSpecies) -> bool:
        limit = self.max_species_generation
        return limit is None or species.generation <= limit


@dataclass(frozen=True)
class PokedexContext:
    """The Pokédex of one completed game and the user's progress in it.

    Built by ``api/services/`` from both databases. ``species`` go in the order of the
    Pokédex (RN-22). ``registered`` and ``impossible`` are the user's marks (RF-21, RF-22);
    ``started`` says whether the initial list was confirmed (RN-22). ``sources`` are the games
    that can send Pokémon to this one, in the order to propose them (RN-25). ``starters`` are
    the species received as the game's starter (CA-87).
    """

    game: GameInfo
    has_breeding: bool
    species: tuple[DexSpecies, ...]
    registered: frozenset[str] = frozenset()
    impossible: frozenset[str] = frozenset()
    started: bool = False
    sources: tuple[TransferSource, ...] = ()
    starters: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        numbers = [entry.number for entry in self.species]
        if numbers != sorted(set(numbers)):
            raise PokedexContextError(f"números de la Pokédex desordenados o repetidos: {numbers}")
        slugs = [entry.species for entry in self.species]
        if len(set(slugs)) != len(slugs):
            raise PokedexContextError("especies repetidas en la Pokédex")
        known = set(slugs)
        for name, marked in (("registradas", self.registered), ("imposibles", self.impossible)):
            unknown = sorted(marked - known)
            if unknown:
                raise PokedexContextError(f"especies {name} fuera de la Pokédex: {unknown}")
        both = sorted(self.registered & self.impossible)
        if both:
            raise PokedexContextError(f"especies registradas y a la vez imposibles: {both}")
        outside = sorted({p for e in self.species for p in e.previous} - known)
        if outside:
            raise PokedexContextError(f"evoluciones desde especies fuera de la Pokédex: {outside}")
        if any(source.game == self.game.slug for source in self.sources):
            raise PokedexContextError(f"{self.game.slug} no puede transferirse a sí mismo")

    @cached_property
    def gift_choices(self) -> dict[GiftPlace, tuple[str, ...]]:
        """Places of the game where one of several gifts is chosen (CA-87)."""
        return shared_gifts({entry.species: entry.encounters for entry in self.species})

    @cached_property
    def _by_species(self) -> dict[str, DexSpecies]:
        return {entry.species: entry for entry in self.species}

    def entry(self, species: str) -> DexSpecies:
        try:
            return self._by_species[species]
        except KeyError:
            raise PokedexContextError(
                f"{species} no está en la Pokédex de {self.game.slug}"
            ) from None
