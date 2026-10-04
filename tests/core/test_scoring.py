"""Weighted score (RN-04), its breakdown (RF-09) and the tie-break key (RN-19)."""

from fractions import Fraction
from random import Random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from core.domain import PokemonData
from core.rules.catalog import RuleSettings
from core.scoring import score_team
from tests.core.builders import battle, context, pokemon, step, type_chart

GENGAR = pokemon(
    "gengar",
    ("ghost", "poison"),
    line=("haunter",),
    dex_number=94,
    steps=[step("haunter", "gengar", "trade")],
)
BEAUTIFLY = pokemon(
    "beautifly",
    ("bug", "flying"),
    line=("silcoon",),
    dex_number=267,
    steps=[step("silcoon", "beautifly", minimum_level=7, percentage_chance=50)],
)
FILLERS = [pokemon(f"filler-{i}", dex_number=i) for i in range(1, 7)]


def _total(team: list[PokemonData], settings: RuleSettings | None = None) -> Fraction:
    return score_team(team, context(settings=settings)).total


@pytest.mark.rn("RN-04")
def test_breakdown_has_every_active_soft_rule_with_its_default_weight() -> None:
    score = score_team(FILLERS, context(key_battles=[battle("brock", ("onix", ("rock",)))]))
    assert [(r.rule_id, r.weight) for r in score.breakdown] == [
        ("RN-06", 1),
        ("RN-15", 3),
        ("RN-17", 10),
        ("RN-20", 5),
    ]
    assert score.total == 1 + 3 + 0 + 5


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-15")
@pytest.mark.rn("RN-20")
def test_beautifly_costs_five_and_a_half_and_gengar_half_a_point() -> None:
    """The DDF example of RN-20, with the default weights and a team of 6."""
    base = _total(FILLERS)
    assert base - _total([BEAUTIFLY, *FILLERS[1:]]) == Fraction(11, 2)
    assert base - _total([GENGAR, *FILLERS[1:]]) == Fraction(1, 2)


@pytest.mark.rn("RN-04")
def test_disabled_rules_do_not_score() -> None:
    settings = RuleSettings.defaults().with_changes(enabled={"RN-20": False})
    score = score_team([BEAUTIFLY], context(settings=settings))
    assert "RN-20" not in [r.rule_id for r in score.breakdown]


@pytest.mark.rn("RN-04")
def test_a_rule_with_weight_zero_appears_but_adds_nothing() -> None:
    settings = RuleSettings.defaults().with_changes(weights={"RN-20": 0})
    score = score_team([BEAUTIFLY], context(settings=settings))
    [rn20] = [r for r in score.breakdown if r.rule_id == "RN-20"]
    assert (rn20.weight, rn20.score, rn20.contribution) == (0, Fraction(0), Fraction(0))


@pytest.mark.rn("RN-04")
def test_breakdown_says_which_members_count_against() -> None:
    score = score_team([BEAUTIFLY, GENGAR, *FILLERS[:4]], context())
    penalized = {r.rule_id: r.penalized for r in score.breakdown}
    assert penalized["RN-15"] == ("gengar", "beautifly")  # canonical order: 94, 267
    assert penalized["RN-20"] == ("beautifly",)


@pytest.mark.rn("RN-19")
def test_lapras_team_beats_blastoise_team_at_equal_score() -> None:
    lapras = pokemon("lapras", ("water", "ice"), dex_number=131)
    blastoise = pokemon("blastoise", ("water",), dex_number=9)
    ctx = context()
    with_lapras = score_team([lapras, *FILLERS[:5]], ctx)
    with_blastoise = score_team([blastoise, *FILLERS[:5]], ctx)

    assert with_lapras.total == with_blastoise.total
    assert (with_lapras.dual_types, with_blastoise.dual_types) == (1, 0)
    assert with_lapras.ranking_key > with_blastoise.ranking_key


@pytest.mark.rn("RN-19")
def test_score_comes_before_dual_types() -> None:
    """A better score wins even with fewer members with two types."""
    ctx = context()
    plain = score_team(FILLERS, ctx)
    with_beautifly = score_team([BEAUTIFLY, *FILLERS[1:]], ctx)

    assert with_beautifly.dual_types > plain.dual_types
    assert plain.ranking_key > with_beautifly.ranking_key


# --- Properties ----------------------------------------------------------------------------

TYPES = ("normal", "fire", "water", "grass", "rock", "ground", "flying")
CHART = type_chart(
    overrides={
        ("water", "fire"): 200,
        ("water", "rock"): 200,
        ("grass", "water"): 200,
        ("fire", "grass"): 200,
        ("rock", "fire"): 200,
        ("rock", "flying"): 200,
        ("fire", "water"): 50,
        ("grass", "grass"): 50,
        ("ground", "flying"): 0,
    }
)
BATTLES = [
    battle("brock", ("onix", ("rock", "ground"))),
    battle("misty", ("starmie", ("water",)), ("staryu", ("water",))),
    battle("blaine", ("arcanine", ("fire",))),
]
TRIGGERS = st.sampled_from(["level-up", "trade", "use-item", "shed"])


@st.composite
def members(draw: st.DrawFn, index: int) -> PokemonData:
    types = draw(st.lists(st.sampled_from(TYPES), min_size=1, max_size=2, unique=True))
    evolves = draw(st.booleans())
    steps = []
    if evolves:
        conditions = draw(st.sampled_from([{}, {"percentage_chance": 50}, {"minimum_beauty": 1}]))
        steps = [step(f"pre-{index}", f"p{index}", draw(TRIGGERS), **conditions)]
    return pokemon(
        f"p{index}",
        types,
        line=(f"pre-{index}",) if evolves else (),
        steps=steps,
        dex_number=index,
        species=draw(st.sampled_from(["a", "b", "c", "d", "e", "f", "g"])),
    )


@st.composite
def teams(draw: st.DrawFn) -> list[PokemonData]:
    size = draw(st.integers(min_value=0, max_value=6))
    return [draw(members(i)) for i in range(1, size + 1)]


@st.composite
def settings(draw: st.DrawFn) -> RuleSettings:
    weights = {r: draw(st.integers(0, 10)) for r in ("RN-06", "RN-15", "RN-17", "RN-20")}
    enabled = {r: draw(st.booleans()) for r in ("RN-06", "RN-15", "RN-17", "RN-20")}
    return RuleSettings.defaults().with_changes(enabled=enabled, weights=weights)


@pytest.mark.rn("RN-04")
@given(team=teams(), rules=settings())
def test_total_is_the_sum_of_the_breakdown_and_within_bounds(
    team: list[PokemonData], rules: RuleSettings
) -> None:
    score = score_team(team, context(key_battles=BATTLES, chart=CHART, settings=rules))
    assert score.total == sum(r.weight * r.score for r in score.breakdown)
    assert all(0 <= r.score <= 1 for r in score.breakdown)
    assert 0 <= score.total <= sum(r.weight for r in score.breakdown)


@pytest.mark.rn("RN-04")
@given(team=teams(), rng=st.randoms())
def test_score_does_not_depend_on_member_order(team: list[PokemonData], rng: Random) -> None:
    ctx = context(key_battles=BATTLES, chart=CHART)
    shuffled = list(team)
    rng.shuffle(shuffled)
    assert score_team(team, ctx) == score_team(shuffled, ctx)
