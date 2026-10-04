"""Grouping of tied teams that only differ in interchangeable members (RN-04, CA-33, CA-49)."""

from collections.abc import Sequence

import pytest

from core.domain import PokemonData
from core.engine import GenerationResult, generate
from core.rules.catalog import RuleSettings
from tests.core.builders import candidate, context, pokemon

FILLERS = [
    pokemon(f"filler-{t}", (t,), dex_number=200 + i)
    for i, t in enumerate(("normal", "fighting", "poison", "ground", "rock", "bug"))
]
LAPRAS = pokemon("lapras", ("water", "ice"), dex_number=131)
CLOYSTER = pokemon("cloyster", ("water", "ice"), line=("shellder",), dex_number=91)
VAPOREON = pokemon("vaporeon", ("water",), line=("eevee",), chain=133, dex_number=134)
BLASTOISE = pokemon("blastoise", ("water",), line=("squirtle",), dex_number=9)
NO_PRESENCE = RuleSettings.defaults().with_changes(enabled={"RN-13": False, "RN-14": False})


def _generate(
    favorites: Sequence[PokemonData], settings: RuleSettings = NO_PRESENCE
) -> GenerationResult:
    return generate(context([candidate(p) for p in favorites], settings=settings))


def _positions(result: GenerationResult) -> list[list[tuple[str, ...]]]:
    return [
        [tuple(p.slug for p in alternatives) for alternatives in group.positions]
        for group in result.groups
    ]


@pytest.mark.rn("RN-04")
def test_lapras_or_cloyster() -> None:
    """Both Water/Ice: the two tied teams form one group."""
    result = _generate([LAPRAS, CLOYSTER, *FILLERS[:5]])
    assert len(result.teams) == 2
    [group] = result.groups
    assert ("cloyster", "lapras") in [tuple(p.slug for p in a) for a in group.positions]
    assert group.teams == result.teams


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-14")
def test_vaporeon_is_never_grouped_with_another_water_type_while_rn14_is_active() -> None:
    """With RN-14 the team with Blastoise instead of Vaporeon is not valid: no group."""
    settings = RuleSettings.defaults().with_changes(enabled={"RN-13": False})
    result = _generate([VAPOREON, BLASTOISE, *FILLERS[:5]], settings=settings)
    assert all("vaporeon" in team.slugs for team in result.teams)
    assert all("blastoise" not in alts for group in _positions(result) for alts in group)


@pytest.mark.rn("RN-04")
def test_without_rn14_vaporeon_and_blastoise_are_interchangeable() -> None:
    result = _generate([VAPOREON, BLASTOISE, *FILLERS[:5]])
    [group] = result.groups
    assert ("blastoise", "vaporeon") in [tuple(p.slug for p in a) for a in group.positions]


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-07")
def test_teams_are_not_grouped_if_a_combination_breaks_a_rule() -> None:
    """CA-49: Lapras or Cloyster and Kingler or Krabby would make 4 teams, but Cloyster and
    Krabby share a line here (RN-07): only 3 are valid and they are shown one by one."""
    krabby = pokemon("krabby", ("bug", "steel"), dex_number=98, chain=90)
    kingler = pokemon("kingler", ("bug", "steel"), dex_number=99, chain=99)
    cloyster = pokemon("cloyster", ("water", "ice"), dex_number=91, chain=90)
    result = _generate([LAPRAS, cloyster, krabby, kingler, *FILLERS[:4]])
    assert len(result.teams) == 3
    assert len(result.groups) == 3
    assert all(len(group.teams) == 1 for group in result.groups)


@pytest.mark.rn("RN-04")
def test_groups_cover_every_tied_team_in_order() -> None:
    result = _generate([LAPRAS, CLOYSTER, *FILLERS])
    grouped = [team for group in result.groups for team in group.teams]
    assert sorted(t.slugs for t in grouped) == sorted(t.slugs for t in result.teams)
    for group in result.groups:
        for alternatives in group.positions:
            assert len({p.types for p in alternatives}) == 1
