"""The progress of a Pokédex and the Pokémon to register next (RN-22, RN-23), and the
consistency of its context."""

import pytest

from core.pokedex import PokedexContextError, PokedexStatus, objective, progress
from tests.core.pokedex.builders import encounter, pokedex, species

KANTO_STARTERS = ("bulbasaur", "ivysaur", "venusaur", "charmander")


@pytest.mark.rn("RN-22")
def test_ddf_example_77_percent_and_3_impossible() -> None:
    """DDF: in FireRed, with 300 registered and 3 impossible, 77 % (300 of 386)."""
    entries = [species(f"p{n}", encounter()) for n in range(386)]
    ctx = pokedex(
        *entries,
        registered=[f"p{n}" for n in range(300)],
        impossible=["p300", "p301", "p302"],
    )
    result = progress(ctx)
    assert (result.percent, result.registered, result.total, result.impossible) == (
        77,
        300,
        386,
        3,
    )
    assert result.status is PokedexStatus.IN_PROGRESS


@pytest.mark.rn("RN-22")
def test_rounds_down_so_100_means_complete() -> None:
    entries = [species(f"p{n}", encounter()) for n in range(386)]
    almost = pokedex(*entries, registered=[f"p{n}" for n in range(385)])
    assert progress(almost).percent == 99
    full = pokedex(*entries, registered=[f"p{n}" for n in range(386)])
    assert (progress(full).percent, progress(full).status) == (100, PokedexStatus.COMPLETED)


@pytest.mark.rn("RN-22")
def test_not_started_until_the_initial_list_is_confirmed() -> None:
    ctx = pokedex(species("bulbasaur", encounter()), started=False)
    assert progress(ctx).status is PokedexStatus.NOT_STARTED


@pytest.mark.rn("RN-22")
@pytest.mark.rn("RN-25")
def test_automatic_impossible_ones_count_as_impossible() -> None:
    ctx = pokedex(
        species("jirachi", encounter("disc", "colosseum-bonus-disc-us")),
        species("pidgey", encounter()),
        impossible=["pidgey"],
    )
    assert progress(ctx).impossible == 2


@pytest.mark.rn("RN-23")
def test_ddf_example_objective_skip_and_back() -> None:
    """DDF: with Bulbasaur and Ivysaur registered, Venusaur; skipped, Charmander; on coming
    back (nothing kept), Venusaur again."""
    ctx = pokedex(
        *(species(s, encounter()) for s in KANTO_STARTERS),
        registered=["bulbasaur", "ivysaur"],
    )
    assert objective(ctx) == "venusaur"
    assert objective(ctx, {"venusaur"}) == "charmander"
    assert objective(ctx) == "venusaur"


@pytest.mark.rn("RN-23")
def test_objective_leaves_out_the_impossible_ones() -> None:
    ctx = pokedex(
        species("mew", encounter("disc", "pokemon-channel-pal")),
        species("bulbasaur", encounter()),
        species("ivysaur", encounter()),
        impossible=["bulbasaur"],
    )
    assert objective(ctx) == "ivysaur"


@pytest.mark.rn("RN-23")
def test_no_objective_when_nothing_is_left() -> None:
    ctx = pokedex(species("bulbasaur", encounter()), species("mew"), registered=["bulbasaur"])
    assert objective(ctx) == "mew"  # no known way: the user can mark it as impossible
    assert objective(ctx, {"mew"}) is None


def test_inconsistent_marks_are_rejected() -> None:
    with pytest.raises(PokedexContextError, match="fuera de la Pokédex"):
        pokedex(species("bulbasaur"), registered=["missingno"])
    with pytest.raises(PokedexContextError, match="a la vez imposibles"):
        pokedex(species("bulbasaur"), registered=["bulbasaur"], impossible=["bulbasaur"])


def test_inconsistent_species_are_rejected() -> None:
    with pytest.raises(PokedexContextError, match="desordenados o repetidos"):
        pokedex(species("ivysaur", number=2), species("bulbasaur", number=1))
    with pytest.raises(PokedexContextError, match="fuera de la Pokédex"):
        pokedex(species("ivysaur", evolves_from="bulbasaur"))
