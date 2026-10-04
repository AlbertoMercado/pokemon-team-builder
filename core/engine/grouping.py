"""Grouping of tied teams that only differ in interchangeable members (RN-04, CA-33).

Two members are interchangeable if they have the same types in the target game, like Lapras
and Cloyster (Water/Ice). Tied teams with the same types position by position form a group,
shown as "Water/Ice: Lapras or Cloyster". A group is only formed if every combination of its
alternatives is one of the tied teams (CA-49): otherwise it would show a team that breaks a
hard rule, and those teams are shown one by one. An evolution of Eevee is never grouped with
another Pokémon while RN-14 is active, because the other team would not meet it and would not
be among the tied teams.
"""

from collections.abc import Sequence
from math import prod

from core.domain import PokemonData
from core.engine.result import RankedTeam, TeamGroup

type Signature = tuple[tuple[str, ...], ...]


def _canonical(pokemon: PokemonData) -> tuple[int, str]:
    return pokemon.dex_number, pokemon.slug


def _signature(team: RankedTeam) -> Signature | None:
    """The types of each member, sorted; ``None`` if two members have the same types."""
    types = sorted(member.types for member in team.members)
    return None if len(set(types)) < len(types) else tuple(types)


def _single(team: RankedTeam) -> TeamGroup:
    return TeamGroup(tuple((member,) for member in team.members), (team,))


def _group(teams: Sequence[RankedTeam]) -> list[TeamGroup]:
    """One group if the teams are every combination of their alternatives; else one each.

    The teams have the same signature, so each type combination is one position.
    """
    if len(teams) == 1:
        return [_single(teams[0])]
    by_types = [{m.types: m for m in team.members} for team in teams]
    positions = []
    for types in sorted(by_types[0]):
        alternatives = {aligned[types] for aligned in by_types}
        positions.append(tuple(sorted(alternatives, key=_canonical)))
    if prod(len(alternatives) for alternatives in positions) != len(teams):
        return [_single(team) for team in teams]
    positions.sort(key=lambda alternatives: _canonical(alternatives[0]))
    return [TeamGroup(tuple(positions), tuple(teams))]


def group_teams(teams: Sequence[RankedTeam]) -> tuple[TeamGroup, ...]:
    """Groups of ``teams``, in the order of their first team."""
    partitions: dict[Signature | int, list[RankedTeam]] = {}
    for index, team in enumerate(teams):
        signature = _signature(team)
        partitions.setdefault(index if signature is None else signature, []).append(team)
    order = {team.slugs: index for index, team in enumerate(teams)}
    groups = [group for members in partitions.values() for group in _group(members)]
    return tuple(sorted(groups, key=lambda group: order[group.teams[0].slugs]))
