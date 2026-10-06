"""Properties of ``generate`` with random contexts, checked against a brute-force search.

With up to 12 favourites, every combination can be checked: the brute force tries every
size from 6 minus the reserved slots down, keeps the combinations that meet the active hard
rules and the presence rules, scores them and keeps the best after the tie-break; if the
presence rules cannot be met together, RN-14 gives way (CA-48). The engine must return
exactly those teams (RN-04, RN-08, RN-19), all of them valid, with the right suggestions and
groups, and the same result for the same input (RF-08).
"""

from itertools import combinations, product

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.domain import GameContext, PokemonData
from core.engine import (
    TEAM_SIZE,
    GenerationResult,
    GenerationStatus,
    generate,
    presence_requirements,
    resolved_presence,
    suggestible_entries,
)
from core.rules.candidate import valid_candidates
from core.rules.catalog import RuleSettings
from core.rules.check import check_team
from core.rules.team import (
    EeveePresence,
    PairConstraint,
    PresenceRequirement,
    PresenceStatus,
    active_pair_constraints,
    conflict,
)
from core.scoring import Scorer
from tests.core.builders import (
    battle,
    candidate,
    context,
    pokemon,
    pool_entry,
    step,
    type_chart,
)

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
    """Up to 12 favourites; the named slots that are not favourites go to the pool."""
    size = draw(st.integers(0, 12) | st.integers(8, 12))
    names = draw(st.permutations(NAMES))
    pokemon_list = [draw(favourite(name, i + 1)) for i, name in enumerate(names)]
    favourites, others = pokemon_list[:size], pokemon_list[size:]
    pool = [pool_entry(p, verified=draw(st.booleans())) for p in others if draw(st.booleans())]
    enabled = {rule: draw(st.booleans()) for rule in CONFIGURABLE}
    weights = {rule: draw(st.integers(0, 10)) for rule in SOFT}
    rules = RuleSettings.defaults().with_changes(enabled=enabled, weights=weights)
    return context(
        [candidate(p) for p in favourites],
        pool=pool,
        key_battles=BATTLES,
        chart=CHART,
        settings=rules,
    )


def _valid(team: tuple[PokemonData, ...], constraints: tuple[PairConstraint, ...]) -> bool:
    return not any(conflict(a, b, constraints) for a, b in combinations(team, 2))


def _best_of_size(
    ctx: GameContext, valid: list[PokemonData], size: int, required: list[set[str]]
) -> list[tuple[PokemonData, ...]]:
    constraints = active_pair_constraints(ctx.settings)
    scorer = Scorer(ctx)
    best: tuple[object, ...] | None = None
    winners: list[tuple[PokemonData, ...]] = []
    for team in combinations(valid, size):
        slugs = {p.slug for p in team}
        if not _valid(team, constraints) or not all(slugs & options for options in required):
            continue
        key = scorer.score(team).ranking_key
        if best is None or key > best:
            best, winners = key, [team]
        elif key == best:
            winners.append(team)
    return winners


def brute_force(
    ctx: GameContext,
) -> tuple[list[tuple[PokemonData, ...]], list[PresenceRequirement]]:
    """The best teams of the largest possible size, and the presence rules that apply."""
    candidates, _ = valid_candidates(ctx)
    valid = [c.pokemon for c in candidates]
    presence = list(presence_requirements(ctx, valid))
    suggestible = [e.pokemon for e in suggestible_entries(ctx)]
    while True:
        reserved = sum(1 for p in presence if p.status is PresenceStatus.RESERVED)
        required = [set(p.options) for p in presence if p.status is PresenceStatus.CANDIDATES]
        for size in range(TEAM_SIZE - reserved, -1, -1):
            winners = _best_of_size(ctx, valid, size, required)
            if winners:
                return winners, presence
        # Only RN-13 and RN-14 together can fail: RN-14 gives way (CA-48).
        [index] = [i for i, p in enumerate(presence) if p.rule_id == "RN-14"]
        presence[index] = EeveePresence().requirement((), suggestible)


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-08")
@pytest.mark.rn("RN-19")
@settings(max_examples=200, deadline=None)
@given(ctx=contexts())
def test_engine_returns_exactly_the_best_teams_of_the_brute_force(ctx: GameContext) -> None:
    result = generate(ctx)
    winners, presence = brute_force(ctx)
    assert [team.members for team in result.teams] == winners
    assert [(p.rule_id, p.status, p.options) for p in result.presence] == [
        (p.rule_id, p.status, p.options) for p in presence
    ]
    complete = len(winners[0]) == TEAM_SIZE
    assert (result.status is GenerationStatus.COMPLETE) == complete


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
        assert len(team.members) + sum(s.count for s in team.open_slots) == TEAM_SIZE
        assert set(team.slugs) <= favourites
        assert set(team.slugs) <= set(result.valid_candidates)
        assert _valid(team.members, constraints)
        assert all(set(team.slugs) & options for options in required)


@pytest.mark.rn("RN-03")
@pytest.mark.rn("RN-07")
@pytest.mark.rn("RN-11")
@pytest.mark.rn("RN-12")
@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-14")
@pytest.mark.rn("RN-16")
@settings(max_examples=200, deadline=None)
@given(ctx=contexts())
def test_check_finds_no_problem_in_the_teams_of_the_engine(ctx: GameContext) -> None:
    """``check_team`` uses the engine's rules: its teams only miss their reserved slots."""
    result = generate(ctx)
    reserved = {p.rule_id for p in result.presence if p.status is PresenceStatus.RESERVED}
    for team in result.teams:
        check = check_team(ctx, team.slugs)
        assert {problem.rule_id for problem in check.problems} <= reserved
        assert all(problem.members == () for problem in check.problems)
        assert check.unverified == ()
        if not reserved:
            assert check.valid


@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-14")
@settings(max_examples=200, deadline=None)
@given(ctx=contexts())
def test_resolved_presence_is_the_one_of_the_generation(ctx: GameContext) -> None:
    """``resolved_presence`` (used by ``check_team``) resolves RN-13 and RN-14 to the same
    level as ``generate``, also when one of them gives way (CA-48)."""
    assert resolved_presence(ctx) == generate(ctx).presence


def _suggestion_order(gain: object, pokemon: PokemonData) -> tuple[object, ...]:
    return gain, not pokemon.is_dual_type, pokemon.dex_number, pokemon.slug


@pytest.mark.rn("RN-08")
@pytest.mark.rn("RN-19")
@settings(max_examples=200, deadline=None)
@given(ctx=contexts())
def test_suggestions_fit_meet_their_slot_and_are_ordered(ctx: GameContext) -> None:
    result = generate(ctx)
    constraints = active_pair_constraints(ctx.settings)
    scorer = Scorer(ctx)
    suggestible = {e.pokemon.slug: e for e in suggestible_entries(ctx)}
    reserved = {p.rule_id: set(p.options) for p in result.presence}
    for team in result.teams:
        base = scorer.score(team.members).total
        fitting = {
            slug
            for slug, entry in suggestible.items()
            if _valid((*team.members, entry.pokemon), constraints)
        }
        for slot in team.open_slots:
            slugs = [s.pokemon.slug for s in slot.suggestions]
            allowed = fitting if slot.rule_id is None else fitting & reserved[slot.rule_id]
            assert set(slugs) == allowed
            for s in slot.suggestions:
                assert s.verified == suggestible[s.pokemon.slug].verified
                assert s.gain == scorer.score((*team.members, s.pokemon)).total - base
            keys = [_suggestion_order(-s.gain, s.pokemon) for s in slot.suggestions]
            assert keys == sorted(keys)


@pytest.mark.rn("RN-04")
@settings(max_examples=200, deadline=None)
@given(ctx=contexts())
def test_groups_are_exactly_the_tied_teams(ctx: GameContext) -> None:
    """Every combination of a group is one of its teams, with the same types per position."""
    result: GenerationResult = generate(ctx)
    grouped = [team.slugs for group in result.groups for team in group.teams]
    assert sorted(grouped) == sorted(team.slugs for team in result.teams)
    for group in result.groups:
        combos = {frozenset(p.slug for p in combo) for combo in product(*group.positions)}
        assert combos == {frozenset(team.slugs) for team in group.teams}
        for alternatives in group.positions:
            assert len({p.types for p in alternatives}) == 1


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
