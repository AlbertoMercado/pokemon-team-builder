"""Incomplete teams, their open slots and the suggestions for them (RN-08, CA-48)."""

from collections.abc import Sequence

import pytest

from core.domain import PokemonData, PoolEntry
from core.engine import GenerationResult, GenerationStatus, IncompleteReason, generate
from core.rules.catalog import RuleSettings
from core.rules.team import PresenceStatus
from tests.core.builders import battle, candidate, context, pokemon, pool_entry, type_chart
from tests.core.scenario import all_pokemon, firered_context

DRAGONITE = pokemon("dragonite", ("dragon", "flying"), line=("dratini",), dex_number=149)
VAPOREON = pokemon("vaporeon", ("water",), line=("eevee",), chain=133, dex_number=134)
JOLTEON = pokemon("jolteon", ("electric",), line=("eevee",), chain=133, dex_number=135)
FLAREON = pokemon("flareon", ("fire",), line=("eevee",), chain=133, dex_number=136)
NO_PRESENCE = RuleSettings.defaults().with_changes(enabled={"RN-13": False, "RN-14": False})


def _generate(
    favorites: Sequence[PokemonData],
    pool: Sequence[PoolEntry] = (),
    settings: RuleSettings = NO_PRESENCE,
) -> GenerationResult:
    return generate(context([candidate(p) for p in favorites], pool=pool, settings=settings))


# --- RN-08 in FireRed ----------------------------------------------------------------------


@pytest.mark.rn("RN-08")
def test_four_candidates_in_firered_and_two_free_slots() -> None:
    """The DDF example: the team of the 4 and a list of FireRed Pokémon for the 2 slots.

    Without RN-21, which would add a starter to the team.
    """
    favorites = ("arcanine", "gengar", "vaporeon", "dragonite")
    settings = RuleSettings.defaults().with_changes(enabled={"RN-21": False})
    result = generate(firered_context(favorites, settings))

    assert result.incomplete_reason is IncompleteReason.NOT_ENOUGH_CANDIDATES
    [team] = result.teams
    assert team.slugs == ("arcanine", "gengar", "vaporeon", "dragonite")
    [slots] = team.open_slots
    assert (slots.count, slots.rule_id) == (2, None)
    suggested = [s.pokemon.slug for s in slots.suggestions]
    assert suggested
    assert not set(suggested) & set(favorites)
    # Legendaries cannot be bred and are never suggested (CA-40).
    assert not {"articuno", "zapdos", "moltres", "mewtwo", "mew"} & set(suggested)
    # Every suggestion fits with the team under RN-12.
    team_types = {t for member in team.members for t in member.types}
    assert all(team_types.isdisjoint(all_pokemon()[s][0].types) for s in suggested)


@pytest.mark.rn("RN-21")
@pytest.mark.rn("RN-08")
def test_a_chosen_starter_comes_before_a_favourite_that_does_not_fit() -> None:
    """CA-65 and CA-19: no starter is a favourite, and each one clashes with a favourite
    (Charizard with Arcanine, Blastoise with Vaporeon, Venusaur with Gengar). The presence
    rule comes before the size of the team: the team includes Venusaur, which scores best,
    and leaves Gengar out."""
    favorites = ("arcanine", "gengar", "vaporeon", "dragonite")
    result = generate(firered_context(favorites))

    starter = result.presence[-1]
    assert (starter.rule_id, starter.status) == ("RN-21", PresenceStatus.CHOSEN)
    assert result.incomplete_reason is IncompleteReason.NOT_ENOUGH_CANDIDATES
    [team] = result.teams
    assert team.slugs == ("venusaur", "arcanine", "vaporeon", "dragonite")
    [slots] = team.open_slots
    assert (slots.count, slots.rule_id) == (2, None)
    assert not {"charizard", "blastoise"} & {s.pokemon.slug for s in slots.suggestions}


@pytest.mark.rn("RN-21")
@pytest.mark.rn("RN-13")
def test_a_favourite_starter_that_clashes_with_dragonite_gives_way() -> None:
    """CA-61: Charizard, the only favourite starter, shares Flying with Dragonite (RN-12).
    RN-13 comes first, so RN-21 chooses between the other starters of the game."""
    result = generate(firered_context(("dragonite", "charizard", "golem", "exeggutor")))

    starter = result.presence[-1]
    assert (starter.rule_id, starter.level, starter.status) == ("RN-21", 2, PresenceStatus.CHOSEN)
    assert starter.options == ("venusaur", "blastoise")
    assert "charizard" in starter.detail
    assert "RN-13, que tiene prioridad" in starter.detail
    [team] = result.teams
    assert team.slugs == ("blastoise", "golem", "exeggutor", "dragonite")


@pytest.mark.rn("RN-08")
@pytest.mark.rn("RN-19")
def test_suggestions_are_ordered_by_gain_then_two_types() -> None:
    """Against Misty (Water), Electric and Grass cover the attack; Raichu, Pikachu and Oddish
    add the same and Oddish has two types; Rattata adds nothing."""
    pool = [
        pool_entry(pokemon("rattata", ("normal",), dex_number=19)),
        pool_entry(pokemon("pikachu", ("electric",), dex_number=25)),
        pool_entry(pokemon("raichu", ("electric",), line=("pikachu",), dex_number=26)),
        pool_entry(pokemon("oddish", ("grass", "poison"), dex_number=43)),
    ]
    ctx = context(
        [candidate(pokemon("onix", ("rock", "ground"), dex_number=95))],
        pool=pool,
        key_battles=[battle("misty", ("starmie", ("water",)))],
        chart=type_chart(overrides={("electric", "water"): 200, ("grass", "water"): 200}),
        settings=NO_PRESENCE,
    )
    [team] = generate(ctx).teams
    [slots] = team.open_slots
    assert [s.pokemon.slug for s in slots.suggestions] == ["oddish", "pikachu", "raichu", "rattata"]
    gains = [s.gain for s in slots.suggestions]
    assert gains == sorted(gains, reverse=True)
    assert gains[-1] == 0


@pytest.mark.rn("RN-08")
@pytest.mark.rn("RN-18")
def test_unverified_suggestions_are_marked() -> None:
    """CA-31: a suggestion with unconfirmed data is shown, marked."""
    pool = [pool_entry(pokemon("pidgey", ("flying",), dex_number=16), verified=False)]
    [team] = _generate([], pool=pool).teams
    [slots] = team.open_slots
    assert [(s.pokemon.slug, s.verified) for s in slots.suggestions] == [("pidgey", False)]


@pytest.mark.rn("RN-08")
def test_without_valid_candidates_the_team_is_empty_with_six_free_slots() -> None:
    zapdos = pokemon("zapdos", ("electric", "flying"), egg_groups=("no-eggs",), dex_number=145)
    result = _generate([zapdos], pool=[pool_entry(JOLTEON)])
    [team] = result.teams
    assert team.members == ()
    [slots] = team.open_slots
    assert slots.count == 6
    assert [s.pokemon.slug for s in slots.suggestions] == ["jolteon"]


# --- Reserved slots ------------------------------------------------------------------------


@pytest.mark.rn("RN-08")
@pytest.mark.rn("RN-14")
def test_a_reserved_slot_only_admits_what_fits_with_the_team() -> None:
    """RN-14 level 2: Vaporeon would meet it, but the team already has a Water member."""
    squirtle = pokemon("squirtle", ("water",), dex_number=7)
    settings = RuleSettings.defaults().with_changes(enabled={"RN-13": False})
    result = _generate(
        [squirtle], pool=[pool_entry(VAPOREON), pool_entry(JOLTEON)], settings=settings
    )
    [team] = result.teams
    reserved, free = team.open_slots
    assert (reserved.count, reserved.rule_id) == (1, "RN-14")
    assert [s.pokemon.slug for s in reserved.suggestions] == ["jolteon"]
    assert (free.count, free.rule_id) == (4, None)


# --- CA-48 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-13")
@pytest.mark.rn("RN-14")
def test_when_dragon_and_eevee_cannot_go_together_the_dragon_comes_first() -> None:
    """Zekrom (Dragon/Electric) is the only primary Dragon and Jolteon the only Eevee
    evolution among the favourites; they share Electric (RN-12). Jolteon gives way and
    RN-14 reserves a slot for the other evolutions of Eevee (CA-48)."""
    zekrom = pokemon("zekrom", ("dragon", "electric"), dex_number=644, generation=3)
    settings = RuleSettings.defaults()
    result = _generate(
        [zekrom, JOLTEON], pool=[pool_entry(VAPOREON), pool_entry(FLAREON)], settings=settings
    )

    dragon, eevee, _ = result.presence  # the game has no starters: RN-21 is unmet
    assert (dragon.status, dragon.options) == (PresenceStatus.CANDIDATES, ("zekrom",))
    assert (eevee.level, eevee.status, eevee.options) == (
        2,
        PresenceStatus.RESERVED,
        ("vaporeon", "flareon"),
    )
    assert "jolteon" in eevee.detail
    [team] = result.teams
    assert team.slugs == ("zekrom",)
    reserved = team.open_slots[0]
    assert reserved.rule_id == "RN-14"
    assert [s.pokemon.slug for s in reserved.suggestions] == ["vaporeon", "flareon"]


def test_a_complete_team_has_no_open_slots() -> None:
    fillers = [
        pokemon(f"f{i}", (t,), dex_number=i)
        for i, t in enumerate(("normal", "fire", "water", "grass", "rock", "ghost"), start=1)
    ]
    result = _generate(fillers)
    assert result.status is GenerationStatus.COMPLETE
    assert all(team.open_slots == () for team in result.teams)
