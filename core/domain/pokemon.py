"""Pokémon as the engine sees them: forms with their data in the target game (RN-05, RN-09).

Each ``PokemonData`` is one form (RN-05): a regional form is a different object with its own
identifier. It is the evolution the user wants to reach (RN-09); the stages before it are in
``stages``, from the first stage of its line, with the evolution steps between them.
"""

from dataclasses import dataclass
from itertools import pairwise

type ConditionValue = str | int | bool

MAX_TYPES = 2


class PokemonDataError(ValueError):
    """A Pokémon's data is not consistent."""


@dataclass(frozen=True)
class Stage:
    """A stage of an evolution line, used to decide the stage that hatches (CA-25, CA-36)."""

    pokemon: str
    species: str
    is_baby: bool = False
    requires_incense: bool = False


@dataclass(frozen=True)
class EvolutionStep:
    """One way of evolving between two consecutive stages in the target game (RN-15, RN-20).

    ``trigger`` and ``conditions`` are PokeAPI's (``level-up``, ``{"time_of_day": "day"}``…);
    ``conditions`` is a sorted tuple of pairs so the step is immutable and hashable.
    """

    from_pokemon: str
    to_pokemon: str
    trigger: str
    conditions: tuple[tuple[str, ConditionValue], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "conditions", tuple(sorted(self.conditions)))

    def condition(self, name: str) -> ConditionValue | None:
        return dict(self.conditions).get(name)


@dataclass(frozen=True)
class PokemonData:
    """A form with its data in the target game's generation (RN-10).

    ``generation`` is the one in which the form appeared (RN-03). ``types`` are ordered: the
    first is the primary type (RN-13). ``stages`` go from the first stage of the line to this
    form, and ``evolution_steps`` link consecutive stages (several steps for the same pair
    are alternative methods). ``line_egg_groups`` are the egg groups of every species of the
    evolution line, later evolutions included, to decide whether it can be bred (RN-11).
    """

    slug: str
    species: str
    dex_number: int
    name: str
    generation: int
    types: tuple[str, ...]
    evolution_chain: int
    stages: tuple[Stage, ...]
    line_egg_groups: frozenset[str]
    evolution_steps: tuple[EvolutionStep, ...] = ()
    region: str | None = None
    is_legendary: bool = False
    is_mythical: bool = False

    def __post_init__(self) -> None:
        if not 1 <= len(self.types) <= MAX_TYPES or len(set(self.types)) != len(self.types):
            raise PokemonDataError(f"{self.slug}: tipos no válidos {self.types}")
        if not self.stages or self.stages[-1].pokemon != self.slug:
            raise PokemonDataError(f"{self.slug}: la última etapa debe ser el propio Pokémon")
        pairs = {(a.pokemon, b.pokemon) for a, b in pairwise(self.stages)}
        steps = {(step.from_pokemon, step.to_pokemon) for step in self.evolution_steps}
        if steps != pairs:
            raise PokemonDataError(
                f"{self.slug}: los pasos de evolución {sorted(steps)} no unen sus etapas "
                f"{sorted(pairs)}"
            )

    @property
    def primary_type(self) -> str:
        return self.types[0]

    @property
    def is_dual_type(self) -> bool:
        """Used to break ties (RN-19)."""
        return len(self.types) == MAX_TYPES


@dataclass(frozen=True)
class Availability:
    """Whether a form exists in the target game and can arrive in time (RN-03).

    Values are already confirmed by the user when they were inferred or pending (RN-18).
    """

    exists_in_game: bool
    can_arrive: bool


@dataclass(frozen=True)
class Candidate:
    """A favourite of the user with its availability in the target game (RN-02)."""

    pokemon: PokemonData
    availability: Availability


@dataclass(frozen=True)
class PoolEntry:
    """A Pokémon of the game that is not a favourite, for suggestions (RN-08).

    ``verified`` is false when some of its data was not confirmed (CA-31).
    """

    pokemon: PokemonData
    availability: Availability
    verified: bool
