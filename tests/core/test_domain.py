"""Domain models of the engine: Pokémon, key battles and the game context."""

import pytest

from core.domain import (
    GameContextError,
    GameInfo,
    KeyBattle,
    PokemonDataError,
)
from tests.core.builders import (
    GEN1_TYPES,
    battle,
    candidate,
    context,
    pokemon,
    pool_entry,
    stage,
    step,
    type_chart,
)

# --- Pokémon -------------------------------------------------------------------------------


@pytest.mark.rn("RN-05")
def test_regional_form_is_a_different_pokemon() -> None:
    vulpix = pokemon("vulpix", ("fire",), species="vulpix", chain=19)
    alolan = pokemon("vulpix-alola", ("ice",), species="vulpix", chain=19, region="alola")

    assert vulpix != alolan
    assert len({vulpix, alolan}) == 2
    assert (alolan.species, alolan.region) == ("vulpix", "alola")


@pytest.mark.rn("RN-09")
def test_favourite_is_the_evolution_to_reach_with_its_previous_stages() -> None:
    """Butterfree is evaluated with its own data; Caterpie and Metapod come implicitly."""
    butterfree = pokemon("butterfree", ("bug", "flying"), line=("caterpie", "metapod"))

    assert [s.pokemon for s in butterfree.stages] == ["caterpie", "metapod", "butterfree"]
    assert [(s.from_pokemon, s.to_pokemon) for s in butterfree.evolution_steps] == [
        ("caterpie", "metapod"),
        ("metapod", "butterfree"),
    ]
    assert butterfree.types == ("bug", "flying")


def test_primary_type_and_dual_type() -> None:
    """RN-13 uses the primary type; RN-19 counts dual-type members."""
    kingdra = pokemon("kingdra", ("water", "dragon"))
    assert (kingdra.primary_type, kingdra.is_dual_type) == ("water", True)
    assert not pokemon("vaporeon", ("water",)).is_dual_type


@pytest.mark.parametrize("types", [(), ("water", "ice", "psychic"), ("water", "water")])
def test_invalid_types_are_rejected(types: tuple[str, ...]) -> None:
    with pytest.raises(PokemonDataError, match="tipos"):
        pokemon("lapras", types)


def test_last_stage_must_be_the_pokemon() -> None:
    with pytest.raises(PokemonDataError, match="última etapa"):
        pokemon("gengar", stages=[stage("gastly"), stage("haunter")])


def test_steps_must_link_the_stages() -> None:
    with pytest.raises(PokemonDataError, match="no unen"):
        pokemon("gengar", line=("gastly", "haunter"), steps=[step("haunter", "gengar", "trade")])


def test_alternative_steps_for_the_same_pair_are_allowed() -> None:
    milotic = pokemon(
        "milotic",
        ("water",),
        line=("feebas",),
        steps=[
            step("feebas", "milotic", minimum_beauty=170),
            step("feebas", "milotic", "trade", held_item="prism-scale"),
        ],
    )
    assert len(milotic.evolution_steps) == 2


def test_step_conditions_are_immutable_and_readable() -> None:
    espeon_step = step("eevee", "espeon", time_of_day="day", minimum_happiness=160)

    assert espeon_step.condition("time_of_day") == "day"
    assert espeon_step.condition("held_item") is None
    assert espeon_step.conditions == (("minimum_happiness", 160), ("time_of_day", "day"))
    assert hash(espeon_step) == hash(
        step("eevee", "espeon", minimum_happiness=160, time_of_day="day")
    )


# --- Game ----------------------------------------------------------------------------------


def test_game_mechanics() -> None:
    emerald = GameInfo("emerald", 3, frozenset({"day_night_cycle", "contests"}))
    assert emerald.has("day_night_cycle")
    assert not GameInfo("firered", 3).has("day_night_cycle")


def test_key_battle_needs_rivals() -> None:
    with pytest.raises(ValueError, match="al menos un rival"):
        KeyBattle("firered-brock", "gym_leader", "Brock", ())


# --- Context -------------------------------------------------------------------------------


def test_valid_context() -> None:
    ctx = context(
        [candidate(pokemon("gengar", ("ghost", "poison")))],
        pool=[pool_entry(pokemon("lapras", ("water", "ice")), verified=False)],
        key_battles=[battle("brock", ("geodude", ("rock", "ground")))],
    )
    assert [c.pokemon.slug for c in ctx.favorites] == ["gengar"]
    assert not ctx.pool[0].verified


def test_chart_must_be_of_the_game_generation() -> None:
    with pytest.raises(GameContextError, match="generación"):
        context(chart=type_chart(1, GEN1_TYPES), game=GameInfo("firered", 3))


def test_favourites_are_unique() -> None:
    gengar = candidate(pokemon("gengar", ("ghost", "poison")))
    with pytest.raises(GameContextError, match="repetidos"):
        context([gengar, gengar])


def test_a_favourite_is_not_in_the_pool() -> None:
    gengar = pokemon("gengar", ("ghost", "poison"))
    with pytest.raises(GameContextError, match="pool"):
        context([candidate(gengar)], pool=[pool_entry(gengar)])


@pytest.mark.rn("RN-10")
def test_types_must_exist_in_the_game_generation() -> None:
    """Clefairy is Normal in the 3rd generation: Fairy does not exist yet."""
    with pytest.raises(GameContextError, match="clefairy: fairy"):
        context([candidate(pokemon("clefairy", ("fairy",)))])
    with pytest.raises(GameContextError, match="mawile: fairy"):
        context(key_battles=[battle("x", ("mawile", ("steel", "fairy")))])
