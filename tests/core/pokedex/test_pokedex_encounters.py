"""The ways of obtaining a species in the game from its encounters (RN-26, CA-80 to CA-87)."""

import pytest

from core.pokedex import Encounter, EncounterKind, in_game_ways
from core.pokedex.encounters import UnknownEncounterMethodError, shared_gifts
from tests.core.pokedex.builders import encounter


def kinds(*encounters: Encounter) -> list[EncounterKind]:
    return [way.kind for way in in_game_ways(encounters)]


@pytest.mark.rn("RN-26")
def test_kinds_follow_the_order_of_rn26() -> None:
    ways = in_game_ways(
        [
            encounter("roaming-kanto", "roaming-grass", 25),
            encounter("route-2", "walk", 30, "swarm-yes"),
            encounter("route-1", "walk", 5),
            encounter("route-12", "pokeflute"),
            encounter("cinnabar-island", "gift", 100, "item-helix-fossil"),
            encounter("route-5", "npc-trade", 100, "trade-abra"),
            encounter("celadon-city", "gift"),
        ]
    )
    assert [w.kind for w in ways] == [
        EncounterKind.GIFT,
        EncounterKind.NPC_TRADE,
        EncounterKind.FOSSIL,
        EncounterKind.STATIC,
        EncounterKind.WILD,
        EncounterKind.SWARM,
        EncounterKind.ROAMING,
    ]
    assert ways[1].conditions == ("trade-abra",)  # the Pokémon the NPC asks for
    assert ways[2].item == "helix-fossil"


@pytest.mark.rn("RN-26")
def test_wild_by_probability_then_by_method() -> None:
    """The highest probability first; at the same, walk, surf, diving, the rods, Feebas's
    tiles and rock smash or headbutt (CA-84)."""
    ways = in_game_ways(
        [
            encounter("a", "headbutt-low", 50),
            encounter("b", "feebas-tile-fishing", 50),
            encounter("c", "super-rod", 50),
            encounter("d", "seaweed", 50),
            encounter("e", "surf", 50),
            encounter("f", "walk", 10),
            encounter("g", "walk", 50),
        ]
    )
    assert [w.location for w in ways] == ["g", "e", "d", "c", "b", "a", "f"]


@pytest.mark.rn("RN-26")
def test_time_of_day_counts_the_highest_and_says_when() -> None:
    """CA-81: «Aparece salvaje en la Ruta 29 (noche): 50 %»."""
    [way] = in_game_ways(
        [
            encounter("route-29", "walk", 20, "time-morning"),
            encounter("route-29", "walk", 20, "time-day"),
            encounter("route-29", "walk", 50, "time-night"),
        ]
    )
    assert (way.rarity, way.times) == (50, ("night",))


@pytest.mark.rn("RN-26")
def test_same_probability_at_every_time_says_no_moment() -> None:
    [way] = in_game_ways(
        [encounter("route-29", "walk", 30, f"time-{t}") for t in ("morning", "day", "night")]
    )
    assert (way.rarity, way.times) == (30, ())


@pytest.mark.rn("RN-26")
def test_story_progress_does_not_count() -> None:
    """The game is completed: the progress of the story is not shown (CA-85)."""
    [way] = in_game_ways([encounter("burned-tower", "roaming-grass", 25, "story-progress-x")])
    assert way.conditions == ()


@pytest.mark.rn("RN-26")
def test_swarms_go_after_the_wild_ones() -> None:
    """CA-85: «Aparece en enjambre en X: N %», after the wild ones and before roaming."""
    ways = in_game_ways(
        [
            encounter("route-1", "walk", 90, "swarm-yes"),
            encounter("route-1", "walk", 5, "swarm-no"),
            encounter("roaming", "roaming-grass", 25),
        ]
    )
    assert [(w.kind, w.rarity) for w in ways] == [
        (EncounterKind.WILD, 5),
        (EncounterKind.SWARM, 90),
        (EncounterKind.ROAMING, 25),
    ]
    assert ways[0].conditions == ways[1].conditions == ()


@pytest.mark.rn("RN-26")
def test_other_conditions_are_kept_to_show_them() -> None:
    """CA-85: «los viernes», the friendship of the first Pokémon, the casino coins (CA-83)."""
    ways = in_game_ways(
        [
            encounter("union-cave", "static", 100, "weekday-friday"),
            encounter("celadon-city", "gift", 100, "coins-9999"),
            encounter("water-labyrinth", "gift-egg", 100, "first-party-pokemon-high-friendship"),
        ]
    )
    assert {w.method: (w.kind, w.conditions) for w in ways} == {
        "gift": (EncounterKind.GIFT, ("coins-9999",)),
        "gift-egg": (EncounterKind.GIFT, ("first-party-pokemon-high-friendship",)),
        "static": (EncounterKind.STATIC, ("weekday-friday",)),
    }


@pytest.mark.rn("RN-26")
@pytest.mark.parametrize("method", ["squirt-bottle", "wailmer-pail", "devon-scope", "static"])
def test_static_methods(method: str) -> None:
    """Sudowoodo with the Squirt Bottle or the Wailmer Pail is static, at 100 % (CA-84)."""
    assert kinds(encounter("route-36", method)) == [EncounterKind.STATIC]


@pytest.mark.rn("RN-26")
def test_roaming_that_depends_on_the_starter_or_the_tv() -> None:
    """CA-80 and CA-85: «Pokémon errante si elegiste a Squirtle» or «rojo en la televisión»."""
    ways = in_game_ways(
        [
            encounter("roaming-kanto", "roaming-grass", 25, "starter-squirtle"),
            encounter("roaming-hoenn", "roaming-grass", 25, "story-progress-x", "tv-option-red"),
        ]
    )
    assert {(w.kind, w.choice) for w in ways} == {
        (EncounterKind.ROAMING, "starter-squirtle"),
        (EncounterKind.ROAMING, "tv-option-red"),
    }


@pytest.mark.rn("RN-24")
def test_gift_that_depends_on_the_starter_goes_almost_last() -> None:
    """Form 6 of RN-24: «Regalo en X si elegiste a Y»."""
    [way] = in_game_ways([encounter("lab", "gift", 100, "starter-bulbasaur")])
    assert (way.kind, way.choice) == (EncounterKind.STARTER_GIFT, "starter-bulbasaur")


@pytest.mark.rn("RN-24")
def test_the_games_starter_is_a_gift_that_depends_on_the_starter() -> None:
    """CA-87: «Regalo en Pueblo Paleta si lo elegiste como inicial»."""
    [way] = in_game_ways([encounter("pallet-town", "gift")], "bulbasaur", frozenset({"bulbasaur"}))
    assert (way.kind, way.choice) == (EncounterKind.STARTER_GIFT, "starter-bulbasaur")


@pytest.mark.rn("RN-26")
def test_a_gift_chosen_among_several_says_among_which() -> None:
    """CA-87: «Regalo en Ciudad Azafrán, a elegir entre Hitmonlee y Hitmonchan». Prizes
    with conditions can all be obtained and are not a choice."""
    dojo = encounter("saffron-city", "gift", area="fighting-dojo")
    prize = encounter("celadon-city", "gift", 100, "coins-180")
    shared = shared_gifts(
        {"hitmonlee": [dojo], "hitmonchan": [dojo], "abra": [prize], "clefairy": [prize]}
    )
    assert shared == {("saffron-city", "fighting-dojo", "gift"): ("hitmonlee", "hitmonchan")}
    [way] = in_game_ways([dojo], "hitmonlee", shared=shared)
    assert (way.kind, way.alternatives) == (EncounterKind.GIFT, ("hitmonchan",))


@pytest.mark.rn("RN-24")
def test_event_places_and_the_virtual_console_are_events() -> None:
    """CA-82: «Evento: Isla Suprema con el Ticket Aurora», Celebi in Crystal's Virtual
    Console."""
    ways = in_game_ways(
        [
            encounter("birth-island", "static", event_item="auroraticket"),
            encounter("ilex-forest", "static", 100, "other-virtual-console"),
        ]
    )
    assert [(w.kind, w.item) for w in ways] == [
        (EncounterKind.EVENT, "auroraticket"),
        (EncounterKind.EVENT, None),
    ]


@pytest.mark.rn("RN-25")
def test_spin_offs_are_left_out() -> None:
    assert kinds(encounter("disc", "colosseum-bonus-disc-us"), encounter()) == [EncounterKind.WILD]


def test_an_unknown_method_is_an_error() -> None:
    """The load checks that every method is classified: a new one must be reviewed."""
    with pytest.raises(UnknownEncounterMethodError, match="dive-deep"):
        in_game_ways([encounter("sea", "dive-deep")])


def test_keys_are_stable_and_distinct() -> None:
    ways = in_game_ways(
        [
            encounter("route-1", "walk", 10, area="north"),
            encounter("route-1", "walk", 10, area="south"),
            encounter("route-1", "surf", 10),
        ]
    )
    assert [w.key for w in ways] == ["walk@route-1/north", "walk@route-1/south", "surf@route-1"]
