"""Real scenario: FireRed with real data and a plausible list of favourites.

Data from ``fixtures/firered.json`` (extracted from a real ``reference.sqlite``) and the
favourites of ``scenario.FAVORITES``. The expected teams are a snapshot: if the data or the
rules change on purpose, update them after checking that the new result makes sense.
"""

import time
from fractions import Fraction

import pytest

from core.domain.lines import EEVEE_EVOLUTIONS
from core.engine import GenerationStatus, generate
from core.rules.catalog import RuleSettings
from core.rules.team import PresenceStatus
from tests.core.scenario import FAVORITES, firered_context

EXPECTED_TEAMS = [
    ("tentacruel", "magneton", "exeggutor", "rhydon", "flareon", "dragonite"),
    ("magneton", "cloyster", "exeggutor", "rhydon", "flareon", "dragonite"),
    ("magneton", "exeggutor", "rhydon", "lapras", "flareon", "dragonite"),
]


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-14")
def test_firered_with_the_default_rules() -> None:
    result = generate(firered_context())

    assert result.status is GenerationStatus.COMPLETE
    assert [team.slugs for team in result.teams] == EXPECTED_TEAMS
    # 1 (RN-06) + 3 (RN-15) + 10 · 23/24 (RN-17) + 5 (RN-20). RN-17 misses only the attack
    # on the Psychic rivals (Kadabra, Mr. Mime and Alakazam).
    assert {team.score.total for team in result.teams} == {Fraction(223, 12)}
    assert {team.score.dual_types for team in result.teams} == {5}


@pytest.mark.rn("RN-11")
def test_legendaries_are_discarded_because_they_cannot_be_bred() -> None:
    result = generate(firered_context())
    assert [(d.pokemon, d.rule_id) for d in result.discards] == [
        ("zapdos", "RN-11"),
        ("mewtwo", "RN-11"),
    ]
    assert len(result.valid_candidates) == len(FAVORITES) - 2


@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-14")
def test_presence_rules_in_firered() -> None:
    """Dragonite is a valid candidate (level 1), and so are three Eevee evolutions."""
    result = generate(firered_context())
    dragon, eevee = result.presence
    assert (dragon.level, dragon.status, dragon.options) == (
        1,
        PresenceStatus.CANDIDATES,
        ("dragonite",),
    )
    assert eevee.options == ("vaporeon", "jolteon", "flareon")
    for team in result.teams:
        assert len(set(team.slugs) & EEVEE_EVOLUTIONS) == 1


@pytest.mark.rn("RN-12")
def test_no_type_is_repeated() -> None:
    for team in generate(firered_context()).teams:
        types = [t for member in team.members for t in member.types]
        assert len(types) == len(set(types))


def test_it_takes_less_than_a_second() -> None:
    ctx = firered_context()
    start = time.perf_counter()
    generate(ctx)
    assert time.perf_counter() - start < 1


@pytest.mark.rn("RN-12")
def test_without_rn12_the_coverage_is_complete() -> None:
    """Without RN-12 the six can cover every rival aspect: the score reaches its maximum."""
    settings = RuleSettings.defaults().with_changes(enabled={"RN-12": False})
    result = generate(firered_context(settings=settings))
    assert result.status is GenerationStatus.COMPLETE
    assert {team.score.total for team in result.teams} == {Fraction(19)}


@pytest.mark.rn("RN-04")
def test_tied_teams_are_grouped() -> None:
    """CA-33: the teams with Cloyster and with Lapras (both Water/Ice) form one group."""
    result = generate(firered_context())
    positions = [
        [tuple(p.slug for p in alternatives) for alternatives in group.positions]
        for group in result.groups
    ]
    assert positions == [
        [("tentacruel",), ("magneton",), ("exeggutor",), ("rhydon",), ("flareon",), ("dragonite",)],
        [
            ("magneton",),
            ("cloyster", "lapras"),
            ("exeggutor",),
            ("rhydon",),
            ("flareon",),
            ("dragonite",),
        ],
    ]
