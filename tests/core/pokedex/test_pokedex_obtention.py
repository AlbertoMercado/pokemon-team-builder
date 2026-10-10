"""Every way of obtaining a species, simplest first (RN-24, RN-25), with the DDF's examples."""

import pytest

from core.domain import EvolutionStep
from core.pokedex import MethodKind, PokedexContext, obtention_methods
from tests.core.pokedex.builders import encounter, pokedex, source, species

BABY = ("no-eggs",)


def methods(ctx: PokedexContext, slug: str) -> list[tuple[MethodKind, str | None]]:
    """Each method as (kind, the game or Pokémon it comes from)."""
    return [(m.kind, m.game or m.pokemon) for m in obtention_methods(ctx, slug).methods]


@pytest.mark.rn("RN-24")
def test_pichu_is_bred_from_a_registered_pikachu() -> None:
    """DDF: with Pikachu registered, Pichu: breed from Pikachu (form 1)."""
    ctx = pokedex(
        species("pichu", egg_groups=BABY),
        species("pikachu", encounter("viridian-forest", "walk", 5), evolves_from="pichu"),
        registered=["pikachu"],
    )
    assert methods(ctx, "pichu") == [(MethodKind.BREED_REGISTERED, "pikachu")]


@pytest.mark.rn("RN-24")
def test_a_later_stage_evolves_the_previous_one_first() -> None:
    """DDF: Venusaur, evolve Ivysaur at level 32; the link says Ivysaur is not registered."""
    ctx = pokedex(
        species("bulbasaur"),
        species("ivysaur", evolves_from="bulbasaur"),
        species(
            "venusaur",
            encounter("somewhere", "gift"),
            evolves_from="ivysaur",
            conditions={"minimum_level": 32},
        ),
    )
    first, second = obtention_methods(ctx, "venusaur").methods
    assert (first.kind, first.pokemon, first.pokemon_registered) == (
        MethodKind.EVOLVE,
        "ivysaur",
        False,
    )
    assert first.evolution is not None
    assert first.evolution.condition("minimum_level") == 32
    assert second.kind is MethodKind.IN_GAME


@pytest.mark.rn("RN-24")
def test_eevee_is_a_gift_in_the_game() -> None:
    """DDF: Eevee, gift in Celadon City (form 3)."""
    ctx = pokedex(species("eevee", encounter("celadon-city", "gift")))
    [method] = obtention_methods(ctx, "eevee").methods
    assert method.kind is MethodKind.IN_GAME
    assert method.way is not None
    assert method.way.location == "celadon-city"


@pytest.mark.rn("RN-24")
@pytest.mark.rn("RN-25")
def test_ekans_in_leafgreen_is_transferred_from_firered() -> None:
    """DDF: in LeafGreen, with FireRed completed and Ekans registered there, form 2; without
    that record, form 5, although FireRed is not completed."""
    route = {"ekans": [encounter("route-4", "walk", 25)]}
    ekans = species("ekans")
    registered = pokedex(
        ekans, game="leafgreen", sources=[source("firered", route, registered=["ekans"])]
    )
    assert methods(registered, "ekans") == [(MethodKind.TRANSFER_REGISTERED, "firered")]
    not_completed = pokedex(ekans, game="leafgreen", sources=[source("firered", route)])
    [method] = obtention_methods(not_completed, "ekans").methods
    assert (method.kind, method.game) == (MethodKind.TRANSFER, "firered")
    assert method.way is not None
    assert method.way.location == "route-4"  # the simplest way there


@pytest.mark.rn("RN-24")
def test_mew_is_an_event() -> None:
    ctx = pokedex(species("mew", egg_groups=BABY, is_event=True))
    assert methods(ctx, "mew") == [(MethodKind.EVENT, None)]


@pytest.mark.rn("RN-24")
def test_forms_follow_the_order_of_rn24() -> None:
    """Forms 1 to 7 of a first stage, all at once."""
    ctx = pokedex(
        species(
            "bulbasaur",
            encounter("event-island", "static", event_item="ticket"),
            encounter("lab", "gift", 100, "starter-squirtle"),
            encounter("route-1", "walk", 5),
        ),
        species("ivysaur", evolves_from="bulbasaur"),
        species("venusaur", encounter("route-2", "walk", 5), evolves_from="ivysaur"),
        registered=["ivysaur"],
        sources=[
            source("leafgreen", registered=["bulbasaur"]),
            source("emerald", {"bulbasaur": [encounter("route-3", "surf", 5)]}),
        ],
    )
    assert methods(ctx, "bulbasaur") == [
        (MethodKind.BREED_REGISTERED, "ivysaur"),  # 1
        (MethodKind.TRANSFER_REGISTERED, "leafgreen"),  # 2
        (MethodKind.IN_GAME, None),  # 3
        (MethodKind.BREED, "venusaur"),  # 4
        (MethodKind.TRANSFER, "emerald"),  # 5
        (MethodKind.STARTER_GIFT, None),  # 6
        (MethodKind.EVENT, None),  # 7
    ]


@pytest.mark.rn("RN-24")
def test_no_breeding_in_the_first_generation() -> None:
    ctx = pokedex(
        species("pichu", egg_groups=BABY),
        species("pikachu", evolves_from="pichu"),
        registered=["pikachu"],
        has_breeding=False,
        generation=1,
    )
    assert methods(ctx, "pichu") == []


@pytest.mark.rn("RN-24")
def test_breeding_gives_only_the_stage_that_hatches() -> None:
    """CA-86: Ivysaur is not bred, Bulbasaur is."""
    ctx = pokedex(
        species("bulbasaur"),
        species("ivysaur", evolves_from="bulbasaur"),
        species("venusaur", evolves_from="ivysaur"),
        registered=["venusaur"],
    )
    assert methods(ctx, "ivysaur") == [(MethodKind.EVOLVE, "bulbasaur")]
    assert methods(ctx, "bulbasaur") == [(MethodKind.BREED_REGISTERED, "venusaur")]


@pytest.mark.rn("RN-24")
def test_incense_lines_hatch_both_stages() -> None:
    """CA-86 and CA-36: Marill hatches without an incense; Azurill too, with it."""
    ctx = pokedex(
        species("azurill", egg_groups=BABY, requires_incense=True),
        species("marill", evolves_from="azurill", egg_groups=("water1", "fairy")),
        species("azumarill", evolves_from="marill", egg_groups=("water1", "fairy")),
        registered=["azumarill"],
    )
    assert methods(ctx, "marill") == [
        (MethodKind.EVOLVE, "azurill"),
        (MethodKind.BREED_REGISTERED, "azumarill"),
    ]
    [breed] = obtention_methods(ctx, "azurill").methods
    assert (breed.kind, breed.pokemon, breed.incense) == (
        MethodKind.BREED_REGISTERED,
        "azumarill",
        True,
    )


@pytest.mark.rn("RN-24")
def test_lines_that_cannot_be_bred() -> None:
    ctx = pokedex(
        species("articuno", egg_groups=BABY),
        species("ditto", egg_groups=("ditto",)),
        registered=["ditto"],
    )
    assert methods(ctx, "articuno") == []


@pytest.mark.rn("RN-24")
def test_evolution_methods_least_tedious_first_without_the_impossible() -> None:
    """CA-86 and RN-15: trading is tedious, levelling up is not; without a day and night
    cycle, a time of day evolution is impossible."""
    ctx = pokedex(
        species("eevee"),
        species(
            "espeon",
            evolves_from="eevee",
            conditions={"minimum_happiness": 220, "time_of_day": "day"},
        ),
        species("haunter"),
        species("gengar", evolves_from="haunter", trigger="trade", conditions={}),
    )
    assert methods(ctx, "espeon") == []
    with_clock = pokedex(*ctx.species, mechanics=["day_night_cycle"])
    assert methods(with_clock, "espeon") == [(MethodKind.EVOLVE, "eevee")]
    both = pokedex(
        species("haunter"),
        species(
            "gengar",
            evolutions=[
                EvolutionStep("haunter", "gengar", "trade"),
                EvolutionStep("haunter", "gengar", "level-up", (("minimum_level", 40),)),
            ],
        ),
    )
    triggers = [
        m.evolution.trigger for m in obtention_methods(both, "gengar").methods if m.evolution
    ]
    assert triggers == ["level-up", "trade"]


@pytest.mark.rn("RN-25")
def test_time_capsule_only_sends_first_generation_species() -> None:
    route = {"chikorita": [encounter()], "pidgey": [encounter()]}
    ctx = pokedex(
        species("pidgey", generation=1),
        species("chikorita", generation=2),
        game="red",
        generation=1,
        has_breeding=False,
        sources=[source("gold", route, max_species_generation=1)],
    )
    assert methods(ctx, "pidgey") == [(MethodKind.TRANSFER, "gold")]
    assert methods(ctx, "chikorita") == []


@pytest.mark.rn("RN-25")
def test_a_starter_gift_in_another_game_is_not_obtained_there() -> None:
    """Form 5 needs form 3 in the other game (CA-86); a starter there is a choice (CA-87)."""
    lab = {"treecko": [encounter("route-101", "gift")]}
    ctx = pokedex(species("treecko"), sources=[source("ruby", lab, starters=["treecko"])])
    assert methods(ctx, "treecko") == []


@pytest.mark.rn("RN-25")
def test_only_from_spin_offs_is_impossible_automatically() -> None:
    disc = encounter("disc", "colosseum-bonus-disc-us")
    ctx = pokedex(species("jirachi", disc), species("pidgey", disc, encounter()), species("x"))
    assert obtention_methods(ctx, "jirachi").automatically_impossible
    pidgey = obtention_methods(ctx, "pidgey")
    assert not pidgey.automatically_impossible
    assert [m.kind for m in pidgey.methods] == [MethodKind.IN_GAME]
    nothing = obtention_methods(ctx, "x")  # the user may mark it as impossible
    assert (nothing.methods, nothing.automatically_impossible) == ((), False)


def test_keys_are_stable_and_distinct() -> None:
    ctx = pokedex(
        species("bulbasaur", encounter("route-1", "walk", 5), encounter("lab", "gift")),
        species("ivysaur", evolves_from="bulbasaur"),
        registered=["ivysaur"],
        sources=[source("leafgreen", registered=["bulbasaur"])],
    )
    keys = [m.key for m in obtention_methods(ctx, "bulbasaur").methods]
    assert keys == [
        "breed:ivysaur",
        "transfer:leafgreen",
        "in_game:gift@lab",
        "in_game:walk@route-1",
    ]
    assert obtention_methods(ctx, "ivysaur").methods[0].key == (
        "evolve:bulbasaur:level-up:minimum_level=16"
    )
