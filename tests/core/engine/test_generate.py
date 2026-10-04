"""``generate``: complete teams with the constraints, presence rules and tie-break."""

from collections.abc import Sequence

import pytest

from core.domain import KeyBattle, PokemonData
from core.engine import GenerationResult, GenerationStatus, IncompleteReason, generate
from core.rules.catalog import RuleSettings
from core.rules.team import PresenceStatus
from tests.core.builders import battle, candidate, context, pokemon, pool_entry, type_chart

# One type per filler, not used by the named Pokémon below, so fillers never conflict.
FILLER_TYPES = ("normal", "fighting", "poison", "ground", "rock", "bug", "ghost", "steel")
FILLERS = [pokemon(f"filler-{t}", (t,), dex_number=200 + i) for i, t in enumerate(FILLER_TYPES)]

DRAGONITE = pokemon("dragonite", ("dragon", "flying"), line=("dratini",), dex_number=149)
VAPOREON = pokemon("vaporeon", ("water",), line=("eevee",), chain=133, dex_number=134)
JOLTEON = pokemon("jolteon", ("electric",), line=("eevee",), chain=133, dex_number=135)
FLAREON = pokemon("flareon", ("fire",), line=("eevee",), chain=133, dex_number=136)
LAPRAS = pokemon("lapras", ("water", "ice"), dex_number=131)
BLASTOISE = pokemon("blastoise", ("water",), line=("squirtle",), dex_number=9)
NO_PRESENCE = RuleSettings.defaults().with_changes(enabled={"RN-13": False, "RN-14": False})


def _generate(
    favorites: Sequence[PokemonData],
    *,
    settings: RuleSettings = NO_PRESENCE,
    pool: Sequence[PokemonData] = (),
    key_battles: Sequence[KeyBattle] = (),
) -> GenerationResult:
    ctx = context(
        [candidate(p) for p in favorites],
        pool=[pool_entry(p) for p in pool],
        key_battles=key_battles,
        settings=settings,
    )
    return generate(ctx)


# --- RN-01 and RN-02 -----------------------------------------------------------------------


@pytest.mark.rn("RN-01")
@pytest.mark.rn("RN-02")
def test_teams_have_six_favourites() -> None:
    result = _generate(FILLERS[:7], pool=[LAPRAS])
    assert result.status is GenerationStatus.COMPLETE
    assert all(len(team.members) == 6 for team in result.teams)
    assert all(set(team.slugs) <= {f.slug for f in FILLERS} for team in result.teams)


@pytest.mark.rn("RN-01")
@pytest.mark.rn("RN-08")
def test_fewer_than_six_candidates_is_incomplete() -> None:
    result = _generate(FILLERS[:5])
    assert (result.status, result.teams) == (GenerationStatus.INCOMPLETE, ())
    assert result.incomplete_reason is IncompleteReason.NOT_ENOUGH_CANDIDATES


@pytest.mark.rn("RN-01")
@pytest.mark.rn("RN-12")
def test_no_six_without_conflicts_is_incomplete() -> None:
    """Seven candidates, but every one shares a type with the first: no team of 6."""
    clashing = [pokemon(f"water-{t}", ("water", t)) for t in FILLER_TYPES[:6]]
    result = _generate([LAPRAS, *clashing])
    assert result.incomplete_reason is IncompleteReason.NO_VALID_TEAM


# --- RN-04 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-04")
def test_every_tied_team_is_returned_in_canonical_order() -> None:
    """Seven equal fillers: the 7 teams of 6 tie and all are returned."""
    result = _generate(FILLERS[:7])
    assert len(result.teams) == 7
    dex_numbers = [tuple(m.dex_number for m in t.members) for t in result.teams]
    assert dex_numbers == sorted(dex_numbers)
    assert len({t.score.total for t in result.teams}) == 1


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-17")
def test_the_best_score_wins() -> None:
    """Against Brock (Rock/Ground), a Water member covers the attack."""
    chart_ctx_battle = battle("brock", ("onix", ("rock", "ground")))
    squirtle = pokemon("squirtle", ("water",), dex_number=7)
    result = generate(
        context(
            [candidate(p) for p in (*FILLERS[:6], squirtle)],
            key_battles=[chart_ctx_battle],
            chart=type_chart(overrides={("water", "rock"): 200}),
            settings=NO_PRESENCE,
        )
    )
    assert all("squirtle" in team.slugs for team in result.teams)


# --- RN-19 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-19")
def test_lapras_team_is_preferred_to_blastoise_team() -> None:
    """Same score; Lapras has two types."""
    result = _generate([BLASTOISE, LAPRAS, *FILLERS[:5]])
    assert [t.slugs for t in result.teams] == [
        ("lapras", *(f.slug for f in FILLERS[:5])),
    ]


# --- RN-13 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-13")
def test_dragonite_is_in_every_team() -> None:
    settings = RuleSettings.defaults().with_changes(enabled={"RN-14": False})
    result = _generate([DRAGONITE, *FILLERS[:6]], settings=settings)
    assert result.teams
    assert all("dragonite" in team.slugs for team in result.teams)


@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-08")
def test_dragonite_comes_before_a_team_of_six() -> None:
    """With Dragonite only 5 fit (RN-12); without it, 6 would. The result is incomplete.

    Pidgeot shares Flying and Kingdra shares Dragon with Dragonite.
    """
    pidgeot = pokemon("pidgeot", ("normal", "flying"), dex_number=18)
    kingdra = pokemon("kingdra", ("water", "dragon"), dex_number=230)
    favorites = [DRAGONITE, pidgeot, kingdra, *FILLERS[1:5]]
    settings = RuleSettings.defaults().with_changes(enabled={"RN-14": False})
    result = _generate(favorites, settings=settings)
    assert result.incomplete_reason is IncompleteReason.NO_VALID_TEAM


@pytest.mark.rn("RN-13")
def test_unmet_dragon_rule_does_not_block_the_team() -> None:
    """Level 4: no primary Dragon type in the game; the team is generated without it."""
    settings = RuleSettings.defaults().with_changes(enabled={"RN-14": False})
    result = _generate(FILLERS[:6], settings=settings)
    assert result.status is GenerationStatus.COMPLETE
    [presence] = result.presence
    assert (presence.rule_id, presence.status) == ("RN-13", PresenceStatus.UNMET)


@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-08")
def test_a_reserved_slot_makes_the_result_incomplete() -> None:
    """Level 3: Dragonite is in the game but not a favourite."""
    settings = RuleSettings.defaults().with_changes(enabled={"RN-14": False})
    result = _generate(FILLERS[:6], settings=settings, pool=[DRAGONITE])
    assert result.incomplete_reason is IncompleteReason.RESERVED_SLOT


# --- RN-14 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-14")
def test_exactly_one_of_vaporeon_jolteon_and_flareon() -> None:
    """The DDF example in FireRed, with RN-07 off so only RN-14 keeps them apart."""
    settings = RuleSettings.defaults().with_changes(enabled={"RN-07": False, "RN-13": False})
    result = _generate([VAPOREON, JOLTEON, FLAREON, *FILLERS[:5]], settings=settings)
    assert len(result.teams) == 3
    for team in result.teams:
        assert len(set(team.slugs) & {"vaporeon", "jolteon", "flareon"}) == 1


@pytest.mark.rn("RN-14")
def test_the_evolution_is_chosen_by_score() -> None:
    """Against Misty (Water), Jolteon covers the attack: it is the one chosen."""
    settings = RuleSettings.defaults().with_changes(enabled={"RN-13": False})
    result = generate(
        context(
            [candidate(p) for p in (VAPOREON, JOLTEON, FLAREON, *FILLERS[:5])],
            key_battles=[battle("misty", ("starmie", ("water",)))],
            chart=type_chart(overrides={("electric", "water"): 200}),
            settings=settings,
        )
    )
    assert all("jolteon" in team.slugs for team in result.teams)


# --- Determinism (RF-08) -------------------------------------------------------------------


def test_same_input_same_result_whatever_the_favourites_order() -> None:
    favorites = [DRAGONITE, LAPRAS, BLASTOISE, *FILLERS]
    first = _generate(favorites)
    assert _generate(list(reversed(favorites))) == first
    assert _generate(favorites) == first


@pytest.mark.rn("RN-11")
def test_discards_come_with_the_result() -> None:
    zapdos = pokemon("zapdos", ("electric", "flying"), egg_groups=("no-eggs",), dex_number=145)
    result = _generate([zapdos, *FILLERS[:6]])
    assert [(d.pokemon, d.rule_id) for d in result.discards] == [("zapdos", "RN-11")]
    assert "zapdos" not in result.valid_candidates
