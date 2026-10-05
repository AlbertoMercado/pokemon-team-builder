"""Check of a chosen team (RF-12, CA-53): ``core.rules.check.check_team``.

Each test builds a small context and checks one rule. The property that the teams of the
engine have no problems is in ``tests/core/test_engine_properties.py``.
"""

import pytest

from core.domain import GameContext, HallOfFameEntry, PokemonData
from core.rules.catalog import RuleSettings
from core.rules.check import TeamProblem, UnknownMemberError, check_team
from tests.core.builders import candidate, completed, context, pokemon, pool_entry

EEVEE_LINE = 133
VAPOREON = pokemon("vaporeon", ("water",), line=("eevee",), chain=EEVEE_LINE, dex_number=134)
JOLTEON = pokemon("jolteon", ("electric",), line=("eevee",), chain=EEVEE_LINE, dex_number=135)
FLAREON = pokemon("flareon", ("fire",), line=("eevee",), chain=EEVEE_LINE, dex_number=136)
DRAGONITE = pokemon("dragonite", ("dragon", "flying"), line=("dratini",), dex_number=149)
GENGAR = pokemon("gengar", ("ghost", "poison"), line=("gastly",), dex_number=94)
RHYDON = pokemon("rhydon", ("ground", "rock"), line=("rhyhorn",), dex_number=112)
RHYHORN = pokemon("rhyhorn", ("ground", "rock"), dex_number=111)
EXEGGUTOR = pokemon("exeggutor", ("grass", "psychic"), line=("exeggcute",), dex_number=103)
LAPRAS = pokemon("lapras", ("water", "ice"), dex_number=131)
MAGNETON = pokemon("magneton", ("electric", "steel"), line=("magnemite",), dex_number=82)
ZAPDOS = pokemon("zapdos", ("electric", "flying"), egg_groups=("no-eggs",), dex_number=145)
DRATINI = pokemon("dratini", ("dragon",), dex_number=147)


def _context(
    *favourites: PokemonData,
    pool: tuple[PokemonData, ...] = (),
    unverified: tuple[str, ...] = (),
    disabled: tuple[str, ...] = (),
    journey: tuple[HallOfFameEntry, ...] = (),
) -> GameContext:
    settings = RuleSettings.defaults().with_changes(enabled=dict.fromkeys(disabled, False))
    entries = [pool_entry(p, verified=p.slug not in unverified) for p in pool]
    return context(
        [candidate(p) for p in favourites],
        pool=entries,
        settings=settings,
        journey=journey,
    )


def _rules(problems: tuple[TeamProblem, ...]) -> list[str]:
    return [problem.rule_id for problem in problems]


TEAM = (GENGAR, EXEGGUTOR, RHYDON, FLAREON, DRAGONITE, LAPRAS)


def test_a_team_of_the_engine_has_no_problems() -> None:
    ctx = _context(*TEAM)
    check = check_team(ctx, [p.slug for p in TEAM])
    assert check.valid
    assert check.problems == ()
    assert check.unverified == ()


@pytest.mark.rn("RN-03")
def test_rn03_a_member_that_cannot_arrive_is_a_problem() -> None:
    ctx = context([candidate(GENGAR, can_arrive=False), candidate(DRAGONITE)])
    check = check_team(ctx, ["gengar", "dragonite"])
    [problem] = [p for p in check.problems if p.rule_id == "RN-03"]
    assert problem.members == ("gengar",)
    assert "no puede llegar" in problem.detail


@pytest.mark.rn("RN-11")
def test_rn11_a_member_that_cannot_be_bred_is_a_problem() -> None:
    # Without Dragonite nor a Dragon type in the game, RN-13 cannot be met and asks for nothing.
    check = check_team(_context(ZAPDOS, GENGAR), ["zapdos", "gengar"])
    assert _rules(check.problems) == ["RN-11"]
    assert check.problems[0].members == ("zapdos",)


@pytest.mark.rn("RN-16")
def test_rn16_a_member_used_in_the_journey_is_a_problem() -> None:
    journey = (completed("leafgreen", 3, 1, GENGAR),)
    check = check_team(_context(GENGAR, DRAGONITE, journey=journey), ["gengar", "dragonite"])
    assert _rules(check.problems) == ["RN-16"]


@pytest.mark.rn("RN-07")
def test_rn07_two_members_of_the_same_line_are_a_problem() -> None:
    check = check_team(
        _context(RHYDON, DRAGONITE, pool=(RHYHORN,)), ["rhydon", "rhyhorn", "dragonite"]
    )
    [problem] = check.problems
    assert problem.rule_id == "RN-07"
    assert problem.members == ("rhydon", "rhyhorn")
    assert problem.detail == "Rhydon y Rhyhorn son de la misma línea evolutiva"


@pytest.mark.rn("RN-12")
def test_rn12_two_suggestions_that_share_a_type_are_a_problem() -> None:
    """Two suggestions for free slots fit the team, but not each other."""
    ctx = _context(GENGAR, DRAGONITE, pool=(LAPRAS, VAPOREON), disabled=("RN-14",))
    check = check_team(ctx, ["gengar", "dragonite", "lapras", "vaporeon"])
    [problem] = check.problems
    assert problem.rule_id == "RN-12"
    assert problem.members == ("lapras", "vaporeon")
    assert problem.detail == "Lapras y Vaporeon comparten tipo"


@pytest.mark.rn("RN-14")
def test_rn14_two_evolutions_of_eevee_are_a_problem() -> None:
    ctx = _context(VAPOREON, JOLTEON, DRAGONITE, disabled=("RN-07",))
    check = check_team(ctx, ["vaporeon", "jolteon", "dragonite"])
    assert _rules(check.problems) == ["RN-14"]
    assert check.problems[0].detail == "Vaporeon y Jolteon son dos evoluciones de Eevee"


@pytest.mark.rn("RN-13")
def test_rn13_a_team_without_dragonite_when_it_is_a_candidate_is_a_problem() -> None:
    ctx = _context(GENGAR, DRAGONITE, disabled=("RN-14",))
    check = check_team(ctx, ["gengar"])
    [problem] = check.problems
    assert problem.rule_id == "RN-13"
    assert problem.members == ()
    assert problem.detail.startswith("El equipo tiene que incluir a Dragonite: ")


@pytest.mark.rn("RN-13")
def test_rn13_a_reserved_slot_is_met_with_a_suggestion() -> None:
    """Level 3: no favourite is a primary Dragon type; Dratini comes from the pool."""
    ctx = _context(GENGAR, pool=(DRATINI,), disabled=("RN-14",))
    assert _rules(check_team(ctx, ["gengar"]).problems) == ["RN-13"]
    assert check_team(ctx, ["gengar", "dratini"]).valid


@pytest.mark.rn("RN-14")
def test_rn14_a_team_without_an_evolution_of_eevee_is_a_problem() -> None:
    ctx = _context(GENGAR, VAPOREON, JOLTEON, DRAGONITE)
    check = check_team(ctx, ["gengar", "dragonite"])
    [problem] = check.problems
    assert problem.rule_id == "RN-14"
    assert "Vaporeon o Jolteon" in problem.detail


@pytest.mark.rn("RN-12")
def test_a_disabled_rule_is_not_checked() -> None:
    ctx = _context(GENGAR, DRAGONITE, pool=(LAPRAS, VAPOREON), disabled=("RN-12", "RN-14"))
    assert check_team(ctx, ["gengar", "dragonite", "lapras", "vaporeon"]).valid


def test_an_unverified_suggestion_is_reported_but_is_not_a_problem() -> None:
    """CA-31."""
    ctx = _context(
        GENGAR, DRAGONITE, pool=(MAGNETON,), unverified=("magneton",), disabled=("RN-14",)
    )
    check = check_team(ctx, ["gengar", "dragonite", "magneton"])
    assert check.valid
    assert check.unverified == ("magneton",)


def test_a_pokemon_outside_the_game_is_an_error() -> None:
    with pytest.raises(UnknownMemberError, match="mew") as error:
        check_team(_context(GENGAR), ["gengar", "mew"])
    assert error.value.members == ("mew",)
