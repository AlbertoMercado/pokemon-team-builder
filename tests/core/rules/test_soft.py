"""Soft rules RN-06, RN-15, RN-17 and RN-20, each scoring a team between 0 and 1."""

from fractions import Fraction

import pytest

from core.domain import GameInfo, KeyBattle, PokemonData
from core.rules.catalog import CATALOG, RuleKind
from core.rules.soft import (
    SOFT_RULES,
    KeyBattleCoverageRule,
    RandomEvolutionRule,
    SameSpeciesRule,
    TediousEvolutionRule,
)
from tests.core.builders import battle, context, pokemon, step, type_chart

GENGAR = pokemon(
    "gengar",
    ("ghost", "poison"),
    line=("gastly", "haunter"),
    steps=[step("gastly", "haunter", minimum_level=25), step("haunter", "gengar", "trade")],
)
RAICHU = pokemon(
    "raichu",
    ("electric",),
    line=("pikachu",),
    steps=[step("pikachu", "raichu", "use-item", trigger_item="thunder-stone")],
)
BEAUTIFLY = pokemon(
    "beautifly",
    ("bug", "flying"),
    line=("wurmple", "silcoon"),
    steps=[
        step("wurmple", "silcoon", minimum_level=7, percentage_chance=50),
        step("silcoon", "beautifly", minimum_level=10),
    ],
)

# Brock: Geodude and Onix, Rock/Ground. Water hits them x4; Fighting resists Rock.
BROCK = battle("brock", ("geodude", ("rock", "ground")), ("onix", ("rock", "ground")))
CHART = type_chart(
    overrides={
        ("water", "rock"): 200,
        ("water", "ground"): 200,
        ("rock", "fighting"): 50,
        ("grass", "rock"): 200,
        ("grass", "ground"): 200,
        ("ground", "fire"): 200,
        ("rock", "fire"): 200,
        ("ground", "electric"): 200,
        ("rock", "flying"): 200,
        ("ground", "flying"): 0,
    }
)
SQUIRTLE = pokemon("squirtle", ("water",))
MACHOP = pokemon("machop", ("fighting",))


def test_every_soft_rule_of_the_catalogue_is_implemented() -> None:
    soft = {rule_id for rule_id, rule in CATALOG.items() if rule.kind is RuleKind.SOFT}
    assert set(SOFT_RULES) == soft
    assert all(rule.rule_id == rule_id for rule_id, rule in SOFT_RULES.items())


# --- RN-06 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-06")
def test_vulpix_and_alolan_vulpix_score_zero() -> None:
    vulpix = pokemon("vulpix", ("fire",), species="vulpix")
    alolan = pokemon("vulpix-alola", ("ice",), species="vulpix", region="alola")
    result = SameSpeciesRule().score([vulpix, alolan, MACHOP], context())
    assert result.value == 0
    assert result.penalized == ("vulpix", "vulpix-alola")


@pytest.mark.rn("RN-06")
def test_different_species_score_one() -> None:
    assert SameSpeciesRule().score([SQUIRTLE, MACHOP], context()).value == 1


# --- RN-15 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-15")
def test_one_tedious_member_out_of_two_scores_half() -> None:
    """Gengar counts against (trade); Raichu does not (Thunder Stone)."""
    result = TediousEvolutionRule().score([GENGAR, RAICHU], context())
    assert (result.value, result.penalized) == (Fraction(1, 2), ("gengar",))


@pytest.mark.rn("RN-15")
def test_one_tedious_member_out_of_six() -> None:
    team = [GENGAR, *(pokemon(f"p{i}") for i in range(5))]
    assert TediousEvolutionRule().score(team, context()).value == Fraction(5, 6)


@pytest.mark.rn("RN-15")
def test_empty_team_has_no_tedious_member() -> None:
    assert TediousEvolutionRule().score([], context()).value == 1


# --- RN-20 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-20")
def test_beautifly_scores_zero() -> None:
    result = RandomEvolutionRule().score([BEAUTIFLY, RAICHU], context())
    assert (result.value, result.penalized) == (Fraction(0), ("beautifly",))


@pytest.mark.rn("RN-20")
def test_gengar_scores_one() -> None:
    """Trade is tedious (RN-15) but not random."""
    assert RandomEvolutionRule().score([GENGAR], context()).value == 1


# --- RN-17 ---------------------------------------------------------------------------------


def _coverage(team: list[PokemonData], *battles: KeyBattle) -> Fraction:
    ctx = context(key_battles=battles, chart=CHART)
    return KeyBattleCoverageRule().score(team, ctx).value


@pytest.mark.rn("RN-17")
def test_against_brock_water_covers_attack() -> None:
    """Water hits Rock/Ground x4 but does not resist Rock or Ground: attack only."""
    assert _coverage([SQUIRTLE], BROCK) == Fraction(1, 2)


@pytest.mark.rn("RN-17")
def test_against_brock_fighting_covers_defense() -> None:
    """Fighting resists Rock and is not weak to Ground: defense only."""
    assert _coverage([MACHOP], BROCK) == Fraction(1, 2)


@pytest.mark.rn("RN-17")
def test_against_brock_water_and_fighting_cover_everything() -> None:
    assert _coverage([SQUIRTLE, MACHOP], BROCK) == 1


@pytest.mark.rn("RN-17")
def test_resisting_one_type_is_not_enough_if_weak_to_the_other() -> None:
    """A Flying member is immune to Ground but weak to Rock: no defense."""
    pidgey = pokemon("pidgey", ("normal", "flying"))
    assert _coverage([pidgey], BROCK) == 0


@pytest.mark.rn("RN-17")
def test_each_battle_weighs_the_same() -> None:
    """Brock fully covered (1) and a battle with nothing covered (0) average 1/2."""
    misty = battle("misty", ("staryu", ("water",)), ("starmie", ("water", "psychic")))
    assert _coverage([SQUIRTLE, MACHOP], BROCK, misty) == Fraction(1, 2)


@pytest.mark.rn("RN-17")
def test_each_rival_of_a_battle_weighs_the_same() -> None:
    """Water covers attack on Geodude (1/2) and nothing on Pikachu (0): 1/4."""
    mixed = battle("mixed", ("geodude", ("rock", "ground")), ("pikachu", ("electric",)))
    assert _coverage([SQUIRTLE], mixed) == Fraction(1, 4)


@pytest.mark.rn("RN-17")
def test_without_key_battles_the_rule_scores_zero() -> None:
    assert _coverage([SQUIRTLE, MACHOP]) == 0


@pytest.mark.rn("RN-17")
def test_types_follow_the_generation_chart() -> None:
    """In the 1st generation Ghost does not affect Psychic (RN-10): no attack."""
    gen1 = type_chart(
        1,
        ("normal", "ghost", "psychic"),
        overrides={("ghost", "psychic"): 0, ("ghost", "ghost"): 200},
    )
    haunter = pokemon("haunter", ("ghost",))
    abra = battle("sabrina", ("abra", ("psychic",)))
    gastly = battle("agatha", ("gastly", ("ghost",)))
    ctx = context(key_battles=[abra, gastly], chart=gen1, game=GameInfo("red", 1))
    assert KeyBattleCoverageRule().score([haunter], ctx).value == Fraction(1, 4)
