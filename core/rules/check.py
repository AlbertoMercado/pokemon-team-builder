"""Check of a team chosen by the user against the active rules (RF-12, CA-53).

In the result, the user chooses a team: one Pokémon of each position and one suggestion for
each open slot. Two suggestions for free slots may not fit together, so the team is checked
before it is recorded. The check uses the same rules as the engine, so no rule is written
twice:

- every member passes the candidate filters (RN-03, RN-11, RN-16);
- no two members conflict (RN-07, RN-12, RN-14 "only one");
- the presence rules are met at the level that applies in the generation (RN-13, RN-14).

The members may be favourites or Pokémon of the pool (the suggestions). A member with
unconfirmed data (CA-31) is not a problem, but it is reported.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations

from core.domain import Availability, GameContext, PokemonData
from core.engine import generate
from core.rules.candidate import first_exclusion
from core.rules.team import PresenceStatus, active_pair_constraints, conflict

_PAIR_DETAILS = {
    "RN-07": "{a} y {b} son de la misma línea evolutiva",
    "RN-12": "{a} y {b} comparten tipo",
    "RN-14": "{a} y {b} son dos evoluciones de Eevee",
}


class UnknownMemberError(ValueError):
    """Some members are neither favourites nor Pokémon of the game's pool: ``members``."""

    def __init__(self, members: Sequence[str]) -> None:
        super().__init__(f"Pokémon que no están en el juego: {', '.join(members)}")
        self.members = tuple(members)


@dataclass(frozen=True)
class TeamProblem:
    """A rule the team does not meet: its members involved and why, in Spanish."""

    rule_id: str
    members: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class TeamCheck:
    """The problems of the team, in the order of the checks, and its unverified members."""

    problems: tuple[TeamProblem, ...]
    unverified: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.problems


def _known(ctx: GameContext) -> dict[str, tuple[PokemonData, Availability]]:
    """The favourites and the Pokémon of the pool by identifier."""
    known = {c.pokemon.slug: (c.pokemon, c.availability) for c in ctx.favorites}
    known |= {e.pokemon.slug: (e.pokemon, e.availability) for e in ctx.pool}
    return known


def _alternatives(names: Sequence[str]) -> str:
    """«Vaporeon, Jolteon o Flareon»."""
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} o {names[-1]}"


def check_team(ctx: GameContext, members: Sequence[str]) -> TeamCheck:
    """The problems of the team ``members`` (form identifiers) with the active rules.

    ``UnknownMemberError`` if a member is neither a favourite nor in the pool.
    """
    known = _known(ctx)
    unknown = [slug for slug in members if slug not in known]
    if unknown:
        raise UnknownMemberError(unknown)
    team = [known[slug] for slug in members]
    problems: list[TeamProblem] = []

    for pokemon, availability in team:
        discard = first_exclusion(pokemon, availability, ctx)
        if discard is not None:
            problems.append(TeamProblem(discard.rule_id, (pokemon.slug,), discard.detail))

    constraints = active_pair_constraints(ctx.settings)
    for (a, _), (b, _) in combinations(team, 2):
        rule_id = conflict(a, b, constraints)
        if rule_id is not None:
            detail = _PAIR_DETAILS[rule_id].format(a=a.name, b=b.name)
            problems.append(TeamProblem(rule_id, (a.slug, b.slug), detail))

    for requirement in generate(ctx).presence:
        if requirement.status is PresenceStatus.UNMET or set(members) & set(requirement.options):
            continue
        names = [known[slug][0].name if slug in known else slug for slug in requirement.options]
        problems.append(
            TeamProblem(
                requirement.rule_id,
                (),
                f"El equipo tiene que incluir a {_alternatives(names)}: {requirement.detail}",
            )
        )

    unverified = {e.pokemon.slug for e in ctx.pool if not e.verified}
    return TeamCheck(
        tuple(problems), tuple(slug for slug in dict.fromkeys(members) if slug in unverified)
    )
