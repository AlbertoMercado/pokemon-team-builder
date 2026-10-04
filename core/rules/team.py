"""Rules about the whole team: constraints between members and presence rules.

- **Between members** (RN-07, RN-12, RN-14 "at most one"): two candidates conflict if they
  cannot be in the same team. Together they form the incompatibility graph of the search
  (docs/02-ddt/algoritmo-generacion.md).
- **Presence** (RN-13, RN-14 "at least one"): which Pokémon the team must include, resolved
  to the first level of the DDF that can be met.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from core.domain import PokemonData
from core.domain.lines import DRAGONITE, EEVEE_EVOLUTIONS
from core.rules.catalog import RuleSettings

DRAGON = "dragon"


class PairConstraint(Protocol):
    """A hard rule that forbids two given members in the same team."""

    @property
    def rule_id(self) -> str: ...

    def conflicts(self, a: PokemonData, b: PokemonData) -> bool: ...


class SameLineConstraint:
    """RN-07: no two members of the same evolution line (PokeAPI evolution chain).

    Regional forms share the chain of their base form.
    """

    rule_id = "RN-07"

    def conflicts(self, a: PokemonData, b: PokemonData) -> bool:
        return a.evolution_chain == b.evolution_chain


class SharedTypeConstraint:
    """RN-12: no type in more than one member, as primary or secondary type.

    The types are those of the favourite form in the target game (RN-09, RN-10).
    """

    rule_id = "RN-12"

    def conflicts(self, a: PokemonData, b: PokemonData) -> bool:
        return not set(a.types).isdisjoint(b.types)


class SingleEeveeEvolutionConstraint:
    """RN-14, "only one": two evolutions of Eevee never go together. Eevee itself is not one."""

    rule_id = "RN-14"

    def conflicts(self, a: PokemonData, b: PokemonData) -> bool:
        return a.slug in EEVEE_EVOLUTIONS and b.slug in EEVEE_EVOLUTIONS


PAIR_CONSTRAINTS: tuple[PairConstraint, ...] = (
    SameLineConstraint(),
    SharedTypeConstraint(),
    SingleEeveeEvolutionConstraint(),
)


def active_pair_constraints(settings: RuleSettings) -> tuple[PairConstraint, ...]:
    return tuple(c for c in PAIR_CONSTRAINTS if settings.is_enabled(c.rule_id))


def conflict(a: PokemonData, b: PokemonData, constraints: Sequence[PairConstraint]) -> str | None:
    """The first rule that forbids ``a`` and ``b`` together, or ``None``."""
    for constraint in constraints:
        if constraint.conflicts(a, b):
            return constraint.rule_id
    return None


class PresenceStatus(StrEnum):
    CANDIDATES = "candidates"  # the team must include one of ``options``, all valid candidates
    RESERVED = "reserved"  # no valid candidate: a slot is reserved for ``options`` (RN-08)
    UNMET = "unmet"  # nothing in the game meets it: the team is generated without it


@dataclass(frozen=True)
class PresenceRequirement:
    """The level of a presence rule that applies, and the Pokémon that meet it.

    ``level`` is the level of the rule in the DDF. ``options`` are valid candidates for
    ``CANDIDATES`` and Pokémon of the game that pass the candidate filters (CA-40) for
    ``RESERVED``, both in canonical order.
    """

    rule_id: str
    level: int
    status: PresenceStatus
    options: tuple[str, ...]
    detail: str


class PresenceRule(Protocol):
    @property
    def rule_id(self) -> str: ...

    def requirement(
        self, valid: Sequence[PokemonData], suggestible: Sequence[PokemonData]
    ) -> PresenceRequirement:
        """``valid`` are the valid candidates; ``suggestible``, the Pokémon of the game that
        are not favourites and pass the candidate filters. Both in canonical order."""
        ...


def _slugs(pokemon: Sequence[PokemonData]) -> tuple[str, ...]:
    return tuple(p.slug for p in pokemon)


class DragonPresence:
    """RN-13: Dragonite if it is a valid candidate; if not, a primary Dragon type."""

    rule_id = "RN-13"

    def requirement(
        self, valid: Sequence[PokemonData], suggestible: Sequence[PokemonData]
    ) -> PresenceRequirement:
        if any(p.slug == DRAGONITE for p in valid):
            return PresenceRequirement(
                self.rule_id,
                1,
                PresenceStatus.CANDIDATES,
                (DRAGONITE,),
                "Dragonite es un candidato válido: forma parte del equipo",
            )
        dragons = [p for p in valid if p.primary_type == DRAGON]
        if dragons:
            return PresenceRequirement(
                self.rule_id,
                2,
                PresenceStatus.CANDIDATES,
                _slugs(dragons),
                "Dragonite no es un candidato válido: el equipo incluye un candidato de tipo "
                "primario Dragón",
            )
        others = [p for p in suggestible if p.primary_type == DRAGON]
        if others:
            return PresenceRequirement(
                self.rule_id,
                3,
                PresenceStatus.RESERVED,
                _slugs(others),
                "Ningún candidato válido es de tipo primario Dragón: se reserva un hueco",
            )
        return PresenceRequirement(
            self.rule_id,
            4,
            PresenceStatus.UNMET,
            (),
            "Ningún Pokémon del juego de tipo primario Dragón puede formar parte del equipo: "
            "se genera sin esta regla",
        )


class EeveePresence:
    """RN-14, "at least one": an evolution of Eevee."""

    rule_id = "RN-14"

    def requirement(
        self, valid: Sequence[PokemonData], suggestible: Sequence[PokemonData]
    ) -> PresenceRequirement:
        evolutions = [p for p in valid if p.slug in EEVEE_EVOLUTIONS]
        if evolutions:
            return PresenceRequirement(
                self.rule_id,
                1,
                PresenceStatus.CANDIDATES,
                _slugs(evolutions),
                "El equipo incluye una evolución de Eevee",
            )
        others = [p for p in suggestible if p.slug in EEVEE_EVOLUTIONS]
        if others:
            return PresenceRequirement(
                self.rule_id,
                2,
                PresenceStatus.RESERVED,
                _slugs(others),
                "Ninguna evolución de Eevee es un candidato válido: se reserva un hueco",
            )
        return PresenceRequirement(
            self.rule_id,
            3,
            PresenceStatus.UNMET,
            (),
            "Ninguna evolución de Eevee puede formar parte del equipo: se genera sin esta regla",
        )


PRESENCE_RULES: tuple[PresenceRule, ...] = (DragonPresence(), EeveePresence())
