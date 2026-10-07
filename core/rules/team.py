"""Rules about the whole team: constraints between members and presence rules.

- **Between members** (RN-07, RN-12, RN-14 and RN-21 "at most one"): two candidates conflict
  if they cannot be in the same team. Together they form the incompatibility graph of the
  search (docs/02-ddt/algoritmo-generacion.md).
- **Presence** (RN-13, RN-14 and RN-21 "at least one"): which Pokémon the team must include,
  resolved to the first level of the DDF that can be met.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from core.domain import GameContext, GameInfo, PokemonData
from core.domain.lines import DRAGONITE, EEVEE_EVOLUTIONS

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


class SingleStarterConstraint:
    """RN-21, "only one": two members of the lines of the game's starters never go together.

    Not only two starters: Charizard and Wartortle do not go together either, so that no other
    starter is spent for the other games of the generation (CA-60). ``chains`` are the
    evolution chains of the starters.
    """

    rule_id = "RN-21"

    def __init__(self, chains: frozenset[int]) -> None:
        self._chains = chains

    def conflicts(self, a: PokemonData, b: PokemonData) -> bool:
        return a.evolution_chain in self._chains and b.evolution_chain in self._chains


def starter_chains(ctx: GameContext) -> frozenset[int]:
    """The evolution chains of the game's starters among the favourites and the pool."""
    known = [c.pokemon for c in ctx.favorites] + [e.pokemon for e in ctx.pool]
    return frozenset(p.evolution_chain for p in known if p.slug in ctx.game.starters)


def active_pair_constraints(ctx: GameContext) -> tuple[PairConstraint, ...]:
    """The constraints between members of the active rules, in catalogue order."""
    constraints: tuple[PairConstraint, ...] = (
        SameLineConstraint(),
        SharedTypeConstraint(),
        SingleEeveeEvolutionConstraint(),
        SingleStarterConstraint(starter_chains(ctx)),
    )
    return tuple(c for c in constraints if ctx.settings.is_enabled(c.rule_id))


def conflict(a: PokemonData, b: PokemonData, constraints: Sequence[PairConstraint]) -> str | None:
    """The first rule that forbids ``a`` and ``b`` together, or ``None``."""
    for constraint in constraints:
        if constraint.conflicts(a, b):
            return constraint.rule_id
    return None


class PresenceStatus(StrEnum):
    CANDIDATES = "candidates"  # the team must include one of ``options``, all valid candidates
    # No valid candidate: the team must include one of ``options``, Pokémon of the game that
    # are not favourites and that the rule chooses itself (RN-21, CA-65).
    CHOSEN = "chosen"
    RESERVED = "reserved"  # no valid candidate: a slot is reserved for ``options`` (RN-08)
    UNMET = "unmet"  # nothing in the game meets it: the team is generated without it


@dataclass(frozen=True)
class PresenceRequirement:
    """The level of a presence rule that applies, and the Pokémon that meet it.

    ``level`` is the level of the rule in the DDF. ``options`` are valid candidates for
    ``CANDIDATES`` and Pokémon of the game that are not favourites and pass the candidate
    filters (CA-40) for ``CHOSEN`` and ``RESERVED``, all in canonical order.
    """

    rule_id: str
    level: int
    status: PresenceStatus
    options: tuple[str, ...]
    detail: str

    @property
    def requires_member(self) -> bool:
        """Whether the search has to put one of ``options`` in the team."""
        return self.status in {PresenceStatus.CANDIDATES, PresenceStatus.CHOSEN}


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


class StarterPresence:
    """RN-21, "at least one": a starter of the game, a favourite or not (CA-65).

    ``starters`` are the game's, as the form of their final evolution (CA-59).
    """

    rule_id = "RN-21"

    def __init__(self, starters: frozenset[str]) -> None:
        self._starters = starters

    def requirement(
        self, valid: Sequence[PokemonData], suggestible: Sequence[PokemonData]
    ) -> PresenceRequirement:
        favorites = [p for p in valid if p.slug in self._starters]
        if favorites:
            return PresenceRequirement(
                self.rule_id,
                1,
                PresenceStatus.CANDIDATES,
                _slugs(favorites),
                "El equipo incluye un inicial de tus favoritos",
            )
        others = [p for p in suggestible if p.slug in self._starters]
        if others:
            return PresenceRequirement(
                self.rule_id,
                2,
                PresenceStatus.CHOSEN,
                _slugs(others),
                "Ningún inicial favorito es un candidato válido: el equipo incluye uno de los "
                "iniciales del juego, aunque no sea favorito",
            )
        return PresenceRequirement(
            self.rule_id,
            3,
            PresenceStatus.UNMET,
            (),
            "Ningún inicial del juego puede formar parte del equipo: se genera sin esta regla",
        )


def presence_rules(game: GameInfo) -> tuple[PresenceRule, ...]:
    """Every presence rule, in catalogue order, which is also their priority (CA-48, CA-61)."""
    return (DragonPresence(), EeveePresence(), StarterPresence(game.starters))
