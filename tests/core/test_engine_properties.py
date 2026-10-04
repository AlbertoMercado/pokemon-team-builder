"""Properties of ``generate`` with random contexts, checked against a brute-force search.

With up to 12 favourites, every combination of 6 can be checked: the brute force keeps the
combinations that meet the active hard rules and the presence rules, scores them and keeps
the best after the tie-break. The engine must return exactly those teams (RN-04, RN-19),
all of them valid, and the same result for the same input (RF-08).
"""

from itertools import combinations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.domain import GameContext, PokemonData
from core.engine import TEAM_SIZE, GenerationStatus, generate, presence_requirements
from core.rules.candidate import valid_candidates
from core.rules.catalog import RuleSettings
from core.rules.team import PresenceStatus, active_pair_constraints, conflict
from core.scoring import Scorer
from tests.core.builders import battle, candidate, context, pokemon, step, type_chart

TYPES = (
    "normal", "fire", "water", "grass", "electric", "dragon", "flying", "rock",
    "ice", "ground", "psychic", "bug", "ghost", "steel",
)  # fmt: skip
# Named slots so that the special lines of RN-13 and RN-14 appear in the contexts.
NAMES = ("dragonite", "vaporeon", "jolteon", "flareon", "espeon", *(f"p{i}" for i in range(7)))
CHART = type_chart(
    overrides={
        ("water", "fire"): 200,
        ("water", "rock"): 200,
        ("fire", "grass"): 200,
        ("grass", "water"): 200,
        ("electric", "water"): 200,
        ("electric", "flying"): 200,
        ("rock", "flying"): 200,
        ("dragon", "dragon"): 200,
        ("fire", "water"): 50,
        ("water", "grass"): 50,
        ("electric", "grass"): 50,
        ("normal", "rock"): 50,
    }
)
BATTLES = (
    battle("brock", ("geodude", ("rock",)), ("onix", ("rock",))),
    battle("misty", ("starmie", ("water",))),
    battle("lance", ("dragonite", ("dragon", "flying")), ("gyarados", ("water", "flying"))),
)
CONFIGURABLE = ("RN-07", "RN-11", "RN-12", "RN-13", "RN-14")
SOFT = ("RN-06", "RN-15", "RN-17", "RN-20")


@st.composite
def favourite(draw: st.DrawFn, slug: str, dex_number: int) -> PokemonData:
    types = draw(st.lists(st.sampled_from(TYPES), min_size=1, max_size=2, unique=True))
    trigger = draw(st.sampled_from(["level-up", "level-up", "trade"]))
    random_step = draw(st.booleans()) and trigger == "level-up"
    conditions = {"percentage_chance": 50} if random_step else {}
    return pokemon(
        slug,
        types,
        line=(f"pre-{slug}",),
        steps=[step(f"pre-{slug}", slug, trigger, **conditions)],
        dex_number=dex_number,
        chain=draw(st.integers(1, 10)),
        species=draw(st.sampled_from([slug, slug, "shared"])),
        egg_groups=draw(st.sampled_from([("monster",)] * 4 + [("no-eggs",)])),
    )


@st.composite
def contexts(draw: st.DrawFn) -> GameContext:
    size = draw(st.integers(0, 12) | st.integers(8, 12))
    names = draw(st.permutations(NAMES))[:size]
    favourites = [draw(favourite(name, i + 1)) for i, name in enumerate(names)]
    enabled = {rule: draw(st.booleans()) for rule in CONFIGURABLE}
    weights = {rule: draw(st.integers(0, 10)) for rule in SOFT}
    rules = RuleSettings.defaults().with_changes(enabled=enabled, weights=weights)
    return context(
        [candidate(p) for p in favourites], key_battles=BATTLES, chart=CHART, settings=rules
    )


def brute_force(ctx: GameContext) -> tuple[GenerationStatus, list[tuple[str, ...]]]:
    """Every combination of 6 valid candidates, filtered and ranked one by one."""
    candidates, _ = valid_candidates(ctx)
    valid = [c.pokemon for c in candidates]
    presence = presence_requirements(ctx, valid)
    if any(p.status is PresenceStatus.RESERVED for p in presence):
        return GenerationStatus.INCOMPLETE, []
    required = [set(p.options) for p in presence if p.status is PresenceStatus.CANDIDATES]
    constraints = active_pair_constraints(ctx.settings)
    scorer = Scorer(ctx)
    best: tuple[object, ...] | None = None
    winners: list[tuple[str, ...]] = []
    for team in combinations(valid, TEAM_SIZE):
        if any(conflict(a, b, constraints) for a, b in combinations(team, 2)):
            continue
        slugs = {p.slug for p in team}
        if not all(slugs & options for options in required):
            continue
        key = scorer.score(team).ranking_key
        if best is None or key > best:
            best, winners = key, [tuple(p.slug for p in team)]
        elif key == best:
            winners.append(tuple(p.slug for p in team))
    status = GenerationStatus.COMPLETE if winners else GenerationStatus.INCOMPLETE
    return status, winners


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-19")
@settings(max_examples=200, deadline=None)
@given(ctx=contexts())
def test_engine_returns_exactly_the_best_teams_of_the_brute_force(ctx: GameContext) -> None:
    result = generate(ctx)
    status, winners = brute_force(ctx)
    assert result.status is status
    assert [team.slugs for team in result.teams] == winners


@pytest.mark.rn("RN-01")
@pytest.mark.rn("RN-02")
@pytest.mark.rn("RN-07")
@pytest.mark.rn("RN-12")
@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-14")
@settings(max_examples=200, deadline=None)
@given(ctx=contexts())
def test_every_team_meets_the_active_hard_rules(ctx: GameContext) -> None:
    result = generate(ctx)
    favourites = {c.pokemon.slug for c in ctx.favorites}
    constraints = active_pair_constraints(ctx.settings)
    required = [set(p.options) for p in result.presence if p.status is PresenceStatus.CANDIDATES]
    for team in result.teams:
        assert len(team.members) == TEAM_SIZE
        assert set(team.slugs) <= favourites
        assert set(team.slugs) <= set(result.valid_candidates)
        assert not any(conflict(a, b, constraints) for a, b in combinations(team.members, 2))
        assert all(set(team.slugs) & options for options in required)


@pytest.mark.rn("RN-04")
@settings(max_examples=100, deadline=None)
@given(ctx=contexts())
def test_same_input_same_result(ctx: GameContext) -> None:
    assert generate(ctx) == generate(ctx)


@pytest.mark.rn("RN-04")
@settings(max_examples=100, deadline=None)
@given(ctx=contexts())
def test_scorer_ranking_key_matches_the_full_score(ctx: GameContext) -> None:
    members = [c.pokemon for c in ctx.favorites][:TEAM_SIZE]
    scorer = Scorer(ctx)
    assert scorer.ranking_key(members) == scorer.score(members).ranking_key
