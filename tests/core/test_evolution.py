"""Tedious (RN-15), random (RN-20) and impossible evolutions in the target game."""

import pytest

from core.domain import CONTESTS, DAY_NIGHT_CYCLE, EvolutionStep, GameInfo
from core.evolution import Tedium, assess, step_tedium
from tests.core.builders import pokemon, stage, step

FIRERED = GameInfo("firered", 3)
EMERALD = GameInfo("emerald", 3, frozenset({DAY_NIGHT_CYCLE, CONTESTS}))

GENGAR = pokemon(
    "gengar",
    ("ghost", "poison"),
    line=("gastly", "haunter"),
    steps=[step("gastly", "haunter", minimum_level=25), step("haunter", "gengar", "trade")],
)
RAICHU = pokemon(
    "raichu",
    ("electric",),
    line=("pichu", "pikachu"),
    steps=[
        step("pichu", "pikachu", minimum_happiness=220),
        step("pikachu", "raichu", "use-item", trigger_item="thunder-stone"),
    ],
)
MILOTIC = pokemon(
    "milotic", ("water",), line=("feebas",), steps=[step("feebas", "milotic", minimum_beauty=170)]
)
ESPEON = pokemon(
    "espeon",
    ("psychic",),
    line=("eevee",),
    steps=[step("eevee", "espeon", time_of_day="day", minimum_happiness=160)],
)
BEAUTIFLY = pokemon(
    "beautifly",
    ("bug", "flying"),
    line=("wurmple", "silcoon"),
    steps=[
        step(
            "wurmple",
            "silcoon",
            minimum_level=7,
            percentage_chance=50,
            condition_expression="PID 16 >> 10 % 5 >=",
        ),
        step("silcoon", "beautifly", minimum_level=10),
    ],
)


@pytest.mark.rn("RN-15")
def test_gengar_is_tedious_because_haunter_evolves_by_trade() -> None:
    result = assess(GENGAR, FIRERED)
    assert result.tedious_steps == (("haunter", "gengar", frozenset({Tedium.TRADE})),)
    assert result.is_tedious


@pytest.mark.rn("RN-20")
def test_gengar_is_not_random() -> None:
    """Trade is tedious, not random: RN-20 does not penalise it."""
    assert not assess(GENGAR, FIRERED).is_random


@pytest.mark.rn("RN-15")
def test_raichu_is_not_tedious_friendship_and_stone() -> None:
    assert not assess(RAICHU, FIRERED).is_tedious


@pytest.mark.rn("RN-15")
def test_milotic_is_tedious_by_beauty_in_emerald() -> None:
    """Emerald has contests: beauty is tedious but possible."""
    [(_, _, reasons)] = assess(MILOTIC, EMERALD).tedious_steps
    assert reasons == {Tedium.BEAUTY}


@pytest.mark.rn("RN-15")
def test_milotic_is_impossible_in_firered_without_contests() -> None:
    """Without contests it has to evolve in another game: also tedious."""
    [(_, _, reasons)] = assess(MILOTIC, FIRERED).tedious_steps
    assert reasons == {Tedium.BEAUTY, Tedium.IMPOSSIBLE}


@pytest.mark.rn("RN-15")
def test_espeon_needs_time_of_day_which_firered_has_not() -> None:
    [(_, _, in_firered)] = assess(ESPEON, FIRERED).tedious_steps
    [(_, _, in_emerald)] = assess(ESPEON, EMERALD).tedious_steps
    assert in_firered == {Tedium.TIME_OF_DAY, Tedium.IMPOSSIBLE}
    assert in_emerald == {Tedium.TIME_OF_DAY}


@pytest.mark.rn("RN-15")
@pytest.mark.rn("RN-20")
def test_beautifly_is_random_and_therefore_tedious() -> None:
    """Wurmple evolves at random into Silcoon or Cascoon (CA-35): both rules count it."""
    result = assess(BEAUTIFLY, EMERALD)
    assert result.tedious_steps == (("wurmple", "silcoon", frozenset({Tedium.RANDOM})),)
    assert result.is_tedious
    assert result.is_random


@pytest.mark.rn("RN-15")
@pytest.mark.parametrize(
    ("evolution_step", "expected"),
    [
        (step("nincada", "shedinja", "shed"), {Tedium.SHED}),
        (step("tyrogue", "hitmonlee", minimum_level=20, relative_physical_stats=1), {Tedium.STATS}),
        (step("onix", "steelix", "trade", held_item="metal-coat"), {Tedium.TRADE}),
        (step("karrablast", "escavalier", "trade", trade_species="shelmet"), {Tedium.TRADE}),
        (step("magneton", "magnezone", location="mt-coronet"), {Tedium.LOCATION}),
        (step("mantyke", "mantine", party_species="remoraid"), {Tedium.PARTY}),
        (step("piloswine", "mamoswine", known_move="ancient-power"), {Tedium.MOVE}),
        (step("sliggoo", "goodra", minimum_level=50, needs_overworld_rain=True), {Tedium.OTHER}),
        (step("farfetchd", "sirfetchd", "three-critical-hits"), {Tedium.OTHER}),
        (step("golbat", "crobat", minimum_happiness=220), set()),
        (step("happiny", "chansey", held_item="oval-stone"), set()),
        (step("bulbasaur", "ivysaur", minimum_level=16), set()),
    ],
)
def test_each_method_of_ca_20(evolution_step: EvolutionStep, expected: set[Tedium]) -> None:
    assert step_tedium(evolution_step, EMERALD) == expected


@pytest.mark.rn("RN-15")
def test_an_unknown_condition_is_tedious() -> None:
    """A condition this module does not know never makes a step look easy."""
    assert step_tedium(step("a", "b", some_new_condition=1), EMERALD) == {Tedium.OTHER}


@pytest.mark.rn("RN-15")
def test_the_easiest_alternative_method_counts() -> None:
    """With an easy method and a tedious one for the same step, the player picks the easy one."""
    slowking = pokemon(
        "slowking",
        ("water", "psychic"),
        line=("slowpoke",),
        steps=[
            step("slowpoke", "slowking", "trade", held_item="kings-rock"),
            step("slowpoke", "slowking", "use-item", trigger_item="galarica-wreath"),
        ],
    )
    assert not assess(slowking, EMERALD).is_tedious


@pytest.mark.rn("RN-15")
def test_steps_before_the_stage_that_hatches_do_not_count() -> None:
    """Azumarill hatches as Marill (CA-36): Azurill's step is never done."""
    azumarill = pokemon(
        "azumarill",
        ("water",),
        stages=[
            stage("azurill", is_baby=True, requires_incense=True),
            stage("marill"),
            stage("azumarill"),
        ],
        steps=[step("azurill", "marill", "trade"), step("marill", "azumarill", minimum_level=18)],
    )
    assert not assess(azumarill, EMERALD).is_tedious


@pytest.mark.rn("RN-15")
def test_tedious_steps_follow_the_line_order() -> None:
    line = ("a", "b", "c")
    data = pokemon("c", line=line[:-1], steps=[step("b", "c", "trade"), step("a", "b", "shed")])
    assert [s[:2] for s in assess(data, EMERALD).tedious_steps] == [("a", "b"), ("b", "c")]
