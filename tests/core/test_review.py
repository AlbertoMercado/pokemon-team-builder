"""Unverified data that takes part in a generation (RN-18, RF-15)."""

import pytest

from core.domain import GameInfo, PokemonData
from core.review import (
    Fact,
    FactKind,
    FavoriteFacts,
    Origin,
    involved_facts,
    pending_facts,
    with_starters,
)
from core.rules.catalog import RuleSettings
from tests.core.builders import completed, pokemon

FIRERED = GameInfo("firered", 3)
DEFAULTS = RuleSettings.defaults()


def _favorite(
    data: PokemonData,
    *,
    exists: Origin = Origin.AUTOMATIC,
    exists_value: bool | None = True,
    arrival: Origin = Origin.INFERRED,
    arrival_value: bool | None = True,
) -> FavoriteFacts:
    prefix = f"pokemon:firered:{data.slug}"
    return FavoriteFacts(
        data,
        Fact(f"{prefix}:exists", FactKind.EXISTS, exists, exists_value),
        Fact(f"{prefix}:arrival", FactKind.ARRIVAL, arrival, arrival_value),
    )


def _keys(*favorites: FavoriteFacts, settings: RuleSettings = DEFAULTS) -> list[str]:
    return [fact.key for fact in pending_facts(FIRERED, (), favorites, settings)]


RAICHU = pokemon("raichu", ("electric",), line=("pichu", "pikachu"), dex_number=26)
ZAPDOS = pokemon("zapdos", ("electric", "flying"), egg_groups=("no-eggs",), dex_number=145)


@pytest.mark.rn("RN-18")
def test_raichu_arrival_in_firered_has_to_be_confirmed() -> None:
    """The DDF example: the proposal (inferred) is that it cannot arrive."""
    raichu = _favorite(RAICHU, arrival_value=False)
    assert _keys(raichu) == ["pokemon:firered:raichu:arrival"]


@pytest.mark.rn("RN-18")
def test_once_confirmed_nothing_is_asked() -> None:
    raichu = _favorite(RAICHU, arrival=Origin.CONFIRMED, arrival_value=False)
    assert _keys(raichu) == []


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-11")
def test_nothing_is_asked_about_a_favourite_that_cannot_be_bred() -> None:
    """Zapdos is already discarded with automatic data: its arrival does not matter."""
    zapdos = _favorite(ZAPDOS)
    assert _keys(zapdos) == []
    without_rn11 = DEFAULTS.with_changes(enabled={"RN-11": False})
    assert _keys(zapdos, settings=without_rn11) == ["pokemon:firered:zapdos:arrival"]


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-03")
def test_nothing_is_asked_about_a_favourite_of_a_later_generation() -> None:
    treecko = _favorite(pokemon("treecko", ("grass",), generation=3, dex_number=252))
    in_gold = pending_facts(GameInfo("gold", 2), (), [treecko], DEFAULTS)
    assert in_gold == ()


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-03")
def test_arrival_is_not_asked_if_the_form_is_known_not_to_exist() -> None:
    growlithe = pokemon("growlithe-hisui", ("fire", "rock"), dex_number=58, region="hisui")
    favorite = _favorite(growlithe, exists_value=False)
    assert _keys(favorite) == []


@pytest.mark.rn("RN-18")
def test_existence_comes_before_arrival() -> None:
    favorite = _favorite(RAICHU, exists=Origin.PENDING, exists_value=None)
    assert _keys(favorite) == [
        "pokemon:firered:raichu:exists",
        "pokemon:firered:raichu:arrival",
    ]


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-16")
def test_nothing_is_asked_about_a_favourite_excluded_by_the_journey() -> None:
    gengar = pokemon("gengar", ("ghost", "poison"), line=("gastly", "haunter"), dex_number=94)
    entries = [completed("leafgreen", 3, 1, gengar)]
    found = pending_facts(FIRERED, (), [_favorite(gengar)], DEFAULTS, entries)
    assert found == ()
    without_rn16 = DEFAULTS.with_changes(enabled={"RN-16": False})
    assert len(pending_facts(FIRERED, (), [_favorite(gengar)], without_rn16, entries)) == 1


@pytest.mark.rn("RN-18")
def test_game_data_comes_first_and_only_if_unverified() -> None:
    game_facts = [
        Fact("mechanic:firered:day_night_cycle", FactKind.MECHANIC, Origin.INFERRED, False),
        Fact("mechanic:firered:contests", FactKind.MECHANIC, Origin.CONFIRMED, False),
        Fact("battle:firered:brock", FactKind.KEY_BATTLE, Origin.AUTOMATIC, ("geodude", "onix")),
        Fact("battle:firered:misty", FactKind.KEY_BATTLE, Origin.PENDING),
    ]
    found = pending_facts(FIRERED, game_facts, [_favorite(RAICHU)], DEFAULTS)
    assert [fact.key for fact in found] == [
        "mechanic:firered:day_night_cycle",
        "battle:firered:misty",
        "pokemon:firered:raichu:arrival",
    ]


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-17")
def test_key_battles_are_not_asked_without_rn17() -> None:
    """The key battles only take part in RN-17; the mechanics are still asked."""
    game_facts = [
        Fact("mechanic:firered:day_night_cycle", FactKind.MECHANIC, Origin.INFERRED, False),
        Fact("battle:firered:misty", FactKind.KEY_BATTLE, Origin.PENDING),
    ]
    without_rn17 = DEFAULTS.with_changes(enabled={"RN-17": False})
    found = pending_facts(FIRERED, game_facts, (), without_rn17)
    assert [fact.key for fact in found] == ["mechanic:firered:day_night_cycle"]


@pytest.mark.rn("RN-18")
def test_favourites_in_canonical_order() -> None:
    pikachu = pokemon("pikachu", ("electric",), dex_number=25)
    assert _keys(_favorite(RAICHU), _favorite(pikachu)) == [
        "pokemon:firered:pikachu:arrival",
        "pokemon:firered:raichu:arrival",
    ]


def test_only_a_pending_fact_has_no_value() -> None:
    with pytest.raises(ValueError, match="pendiente"):
        Fact("battle:firered:brock", FactKind.KEY_BATTLE, Origin.PENDING, ("onix",))
    with pytest.raises(ValueError, match="pendiente"):
        Fact("battle:firered:brock", FactKind.KEY_BATTLE, Origin.INFERRED)


@pytest.mark.rn("RN-18")
def test_involved_facts_include_the_known_ones() -> None:
    """What takes part, whatever its origin: the API shows it and says what was confirmed."""
    game_facts = [
        Fact("mechanic:firered:contests", FactKind.MECHANIC, Origin.CONFIRMED, False),
        Fact("battle:firered:brock", FactKind.KEY_BATTLE, Origin.AUTOMATIC, ("geodude", "onix")),
    ]
    raichu = _favorite(RAICHU, arrival=Origin.CONFIRMED, arrival_value=True)
    found = involved_facts(FIRERED, game_facts, [raichu], DEFAULTS)
    assert [fact.key for fact in found] == [
        "mechanic:firered:contests",
        "battle:firered:brock",
        "pokemon:firered:raichu:exists",
        "pokemon:firered:raichu:arrival",
    ]
    assert pending_facts(FIRERED, game_facts, [raichu], DEFAULTS) == ()


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-03")
def test_a_known_false_value_that_discards_a_favourite_takes_part() -> None:
    """Raichu confirmed as unable to arrive: that confirmation decides its discard (RF-09)."""
    raichu = _favorite(RAICHU, arrival=Origin.CONFIRMED, arrival_value=False)
    keys = [fact.key for fact in involved_facts(FIRERED, (), [raichu], DEFAULTS)]
    assert keys == ["pokemon:firered:raichu:exists", "pokemon:firered:raichu:arrival"]
    growlithe = pokemon("growlithe-hisui", ("fire", "rock"), dex_number=58, region="hisui")
    missing = _favorite(growlithe, exists=Origin.CONFIRMED, exists_value=False)
    keys = [fact.key for fact in involved_facts(FIRERED, (), [missing], DEFAULTS)]
    assert keys == ["pokemon:firered:growlithe-hisui:exists"]


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-11")
def test_nothing_takes_part_of_a_favourite_discarded_by_other_rules() -> None:
    assert involved_facts(FIRERED, (), [_favorite(ZAPDOS)], DEFAULTS) == ()


VENUSAUR = pokemon("venusaur", ("grass", "poison"), line=("bulbasaur", "ivysaur"), dex_number=3)
CHARIZARD = pokemon("charizard", ("fire", "flying"), line=("charmander",), dex_number=6)


@pytest.mark.rn("RN-21")
@pytest.mark.rn("RN-18")
def test_the_starters_that_are_not_favourites_are_reviewed_too() -> None:
    """CA-66: RN-21 can choose a starter that is not a favourite, so its data takes part."""
    favourites = [_favorite(CHARIZARD), _favorite(RAICHU)]
    starters = [_favorite(VENUSAUR), _favorite(CHARIZARD)]

    reviewed = with_starters(favourites, starters, DEFAULTS)

    assert [f.pokemon.slug for f in reviewed] == ["charizard", "raichu", "venusaur"]
    assert _keys(*reviewed) == [
        "pokemon:firered:venusaur:arrival",
        "pokemon:firered:charizard:arrival",
        "pokemon:firered:raichu:arrival",
    ]


@pytest.mark.rn("RN-21")
def test_without_rn21_only_the_favourites_are_reviewed() -> None:
    settings = DEFAULTS.with_changes(enabled={"RN-21": False})
    favourites = [_favorite(RAICHU)]
    assert with_starters(favourites, [_favorite(VENUSAUR)], settings) == favourites
