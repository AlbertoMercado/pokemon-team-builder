"""Constraints between members (RN-07, RN-12, RN-14, RN-21) and presence rules (RN-13,
RN-14, RN-21)."""

import pytest

from core.domain import GameInfo, PokemonData
from core.rules.catalog import RuleSettings
from core.rules.team import (
    DragonPresence,
    EeveePresence,
    PresenceStatus,
    SameLineConstraint,
    SharedTypeConstraint,
    SingleEeveeEvolutionConstraint,
    SingleStarterConstraint,
    StarterPresence,
    active_pair_constraints,
    conflict,
    starter_chains,
)
from tests.core.builders import candidate, context, pokemon, pool_entry

EEVEE_LINE = 133
VAPOREON = pokemon("vaporeon", ("water",), line=("eevee",), chain=EEVEE_LINE)
JOLTEON = pokemon("jolteon", ("electric",), line=("eevee",), chain=EEVEE_LINE)
EEVEE = pokemon("eevee", ("normal",), chain=EEVEE_LINE)
RHYDON = pokemon("rhydon", ("ground", "rock"), line=("rhyhorn",))
RHYPERIOR = pokemon("rhyperior", ("ground", "rock"), line=("rhyhorn", "rhydon"))
CHARIZARD = pokemon("charizard", ("fire", "flying"), line=("charmander", "charmeleon"))
PIDGEOT = pokemon("pidgeot", ("normal", "flying"), line=("pidgey", "pidgeotto"))
GENGAR = pokemon("gengar", ("ghost", "poison"), line=("gastly", "haunter"))
NIDOKING = pokemon("nidoking", ("poison", "ground"), line=("nidoran-m", "nidorino"))
DRAGONITE = pokemon("dragonite", ("dragon", "flying"), line=("dratini", "dragonair"))
KINGDRA = pokemon("kingdra", ("water", "dragon"), line=("horsea", "seadra"))
GARCHOMP = pokemon("garchomp", ("dragon", "ground"), line=("gible", "gabite"))
SALAMENCE = pokemon("salamence", ("dragon", "flying"), line=("bagon", "shelgon"))
VENUSAUR = pokemon("venusaur", ("grass", "poison"), line=("bulbasaur", "ivysaur"))
BLASTOISE = pokemon("blastoise", ("water",), line=("squirtle", "wartortle"))
WARTORTLE = pokemon("wartortle", ("water",), line=("squirtle",))
STARTERS = frozenset({"venusaur", "charizard", "blastoise"})
FIRERED = GameInfo("firered", 3, starters=STARTERS)

# --- RN-07 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-07")
def test_jolteon_and_vaporeon_are_the_same_line() -> None:
    assert SameLineConstraint().conflicts(JOLTEON, VAPOREON)


@pytest.mark.rn("RN-07")
def test_rhydon_and_rhyperior_are_the_same_line() -> None:
    assert SameLineConstraint().conflicts(RHYDON, RHYPERIOR)


@pytest.mark.rn("RN-07")
def test_different_lines_do_not_conflict() -> None:
    assert not SameLineConstraint().conflicts(CHARIZARD, PIDGEOT)


# --- RN-12 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-12")
@pytest.mark.parametrize(
    ("a", "b"),
    [(CHARIZARD, PIDGEOT), (GENGAR, NIDOKING), (RHYDON, RHYPERIOR)],
    ids=["flying", "poison-as-secondary-and-primary", "both-types"],
)
def test_members_sharing_a_type_conflict(a: PokemonData, b: PokemonData) -> None:
    assert SharedTypeConstraint().conflicts(a, b)


@pytest.mark.rn("RN-12")
def test_vaporeon_and_jolteon_do_not_share_a_type() -> None:
    """If they cannot go together it is because of RN-14, not RN-12."""
    assert not SharedTypeConstraint().conflicts(VAPOREON, JOLTEON)


# --- RN-14 (only one) ----------------------------------------------------------------------


@pytest.mark.rn("RN-14")
def test_two_evolutions_of_eevee_conflict() -> None:
    assert SingleEeveeEvolutionConstraint().conflicts(VAPOREON, JOLTEON)


@pytest.mark.rn("RN-14")
def test_eevee_itself_is_not_an_evolution() -> None:
    assert not SingleEeveeEvolutionConstraint().conflicts(EEVEE, VAPOREON)


# --- RN-21 (only one) ----------------------------------------------------------------------


@pytest.mark.rn("RN-21")
def test_starter_chains_are_those_of_the_game_starters() -> None:
    ctx = context(
        [candidate(CHARIZARD), candidate(PIDGEOT)],
        pool=[pool_entry(VENUSAUR), pool_entry(WARTORTLE)],
        game=FIRERED,
    )
    assert starter_chains(ctx) == {CHARIZARD.evolution_chain, VENUSAUR.evolution_chain}


@pytest.mark.rn("RN-21")
@pytest.mark.parametrize(
    ("a", "b"),
    [(CHARIZARD, VENUSAUR), (CHARIZARD, WARTORTLE)],
    ids=["two-starters", "starter-and-another-starter-line"],
)
def test_members_of_two_starter_lines_conflict(a: PokemonData, b: PokemonData) -> None:
    """CA-60: not only two starters; Charizard and Wartortle do not go together either."""
    chains = frozenset({CHARIZARD.evolution_chain, BLASTOISE.evolution_chain})
    assert SingleStarterConstraint(chains | {VENUSAUR.evolution_chain}).conflicts(a, b)


@pytest.mark.rn("RN-21")
def test_a_starter_and_another_line_do_not_conflict() -> None:
    chains = frozenset({CHARIZARD.evolution_chain, VENUSAUR.evolution_chain})
    assert not SingleStarterConstraint(chains).conflicts(CHARIZARD, PIDGEOT)


# --- Active constraints --------------------------------------------------------------------


@pytest.mark.rn("RN-07")
@pytest.mark.rn("RN-12")
@pytest.mark.rn("RN-14")
@pytest.mark.rn("RN-21")
def test_conflict_names_the_first_active_rule() -> None:
    pool = [pool_entry(VENUSAUR), pool_entry(BLASTOISE)]
    every = active_pair_constraints(context([candidate(CHARIZARD)], pool=pool, game=FIRERED))
    without_rn07 = active_pair_constraints(
        context(settings=RuleSettings.defaults().with_changes(enabled={"RN-07": False}))
    )
    assert conflict(JOLTEON, VAPOREON, every) == "RN-07"
    assert conflict(JOLTEON, VAPOREON, without_rn07) == "RN-14"
    assert conflict(CHARIZARD, GENGAR, every) is None
    assert conflict(VENUSAUR, BLASTOISE, every) == "RN-21"


@pytest.mark.rn("RN-07")
@pytest.mark.rn("RN-12")
@pytest.mark.rn("RN-14")
@pytest.mark.rn("RN-21")
def test_disabled_constraints_do_not_apply() -> None:
    settings = RuleSettings.defaults().with_changes(
        enabled={"RN-07": False, "RN-12": False, "RN-14": False, "RN-21": False}
    )
    assert active_pair_constraints(context(settings=settings)) == ()


# --- RN-13 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-13")
def test_dragonite_is_required_when_it_is_a_valid_candidate() -> None:
    """Level 1, even with other Dragon types among the candidates."""
    result = DragonPresence().requirement([GARCHOMP, DRAGONITE], [])
    assert (result.level, result.status, result.options) == (
        1,
        PresenceStatus.CANDIDATES,
        ("dragonite",),
    )


@pytest.mark.rn("RN-13")
def test_garchomp_meets_it_and_kingdra_does_not() -> None:
    """Level 2: only primary Dragon types count; Kingdra is Water/Dragon."""
    result = DragonPresence().requirement([KINGDRA, GARCHOMP, SALAMENCE], [])
    assert (result.level, result.options) == (2, ("garchomp", "salamence"))


@pytest.mark.rn("RN-13")
def test_a_slot_is_reserved_for_dragons_of_the_game() -> None:
    """Level 3: no valid candidate, but the game has primary Dragon types."""
    result = DragonPresence().requirement([KINGDRA], [DRAGONITE])
    assert (result.level, result.status, result.options) == (
        3,
        PresenceStatus.RESERVED,
        ("dragonite",),
    )


@pytest.mark.rn("RN-13")
def test_unmet_when_the_game_has_no_primary_dragon() -> None:
    """Level 4: the team is generated without the rule."""
    result = DragonPresence().requirement([KINGDRA], [KINGDRA])
    assert (result.level, result.status, result.options) == (4, PresenceStatus.UNMET, ())


# --- RN-14 (at least one) ------------------------------------------------------------------


@pytest.mark.rn("RN-14")
def test_one_of_the_eevee_evolutions_among_candidates() -> None:
    result = EeveePresence().requirement([EEVEE, VAPOREON, JOLTEON], [])
    assert (result.level, result.status, result.options) == (
        1,
        PresenceStatus.CANDIDATES,
        ("vaporeon", "jolteon"),
    )


@pytest.mark.rn("RN-14")
def test_a_slot_is_reserved_for_eevee_evolutions_of_the_game() -> None:
    """Eevee as a favourite does not count: it is not an evolution."""
    result = EeveePresence().requirement([EEVEE], [JOLTEON])
    assert (result.level, result.status, result.options) == (
        2,
        PresenceStatus.RESERVED,
        ("jolteon",),
    )


@pytest.mark.rn("RN-14")
def test_unmet_without_eevee_evolutions_in_the_game() -> None:
    result = EeveePresence().requirement([EEVEE], [])
    assert (result.level, result.status) == (3, PresenceStatus.UNMET)


# --- RN-21 (at least one) ------------------------------------------------------------------


@pytest.mark.rn("RN-21")
def test_a_favourite_starter_among_candidates() -> None:
    """Level 1: the starters among the valid candidates, even if others are suggestible."""
    result = StarterPresence(STARTERS).requirement([CHARIZARD, PIDGEOT], [VENUSAUR])
    assert (result.level, result.status, result.options) == (
        1,
        PresenceStatus.CANDIDATES,
        ("charizard",),
    )


@pytest.mark.rn("RN-21")
def test_without_a_favourite_starter_the_rule_chooses_one_of_the_game() -> None:
    """Level 2 (CA-65): no slot is reserved, the team includes one that is not a favourite.

    Wartortle as a favourite does not count: only the final evolution is a starter (CA-59).
    """
    result = StarterPresence(STARTERS).requirement([WARTORTLE], [VENUSAUR, BLASTOISE])
    assert (result.level, result.status, result.options) == (
        2,
        PresenceStatus.CHOSEN,
        ("venusaur", "blastoise"),
    )
    assert result.requires_member


@pytest.mark.rn("RN-21")
def test_unmet_when_no_starter_of_the_game_can_be_in_the_team() -> None:
    result = StarterPresence(STARTERS).requirement([PIDGEOT], [PIDGEOT])
    assert (result.level, result.status, result.options) == (3, PresenceStatus.UNMET, ())
