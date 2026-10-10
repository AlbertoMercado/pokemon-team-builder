"""The FireRed Pokédex with real data (``tests/core/pokedex_scenario.py``): the known cases
of the plan (docs/06-historial/plan-pokedex.md) and that the whole Pokédex is fast."""

import time
from collections.abc import Iterable

import pytest

from core.pokedex import (
    EncounterKind,
    MethodKind,
    Obtention,
    PokedexStatus,
    objective,
    obtention_methods,
    progress,
)
from tests.core.pokedex_scenario import firered_pokedex


def recommended(
    slug: str, registered: Iterable[str] = (), completed: dict[str, Iterable[str]] | None = None
) -> Obtention:
    return obtention_methods(firered_pokedex(registered, completed=completed), slug)


def first_way(slug: str) -> tuple[MethodKind, EncounterKind | None, str | None]:
    method = obtention_methods(firered_pokedex(), slug).recommended
    assert method is not None
    way = method.way
    return method.kind, way.kind if way else None, way.location if way else None


@pytest.mark.rn("RN-26")
@pytest.mark.parametrize(
    ("slug", "expected"),
    [
        ("eevee", (MethodKind.IN_GAME, EncounterKind.GIFT, "celadon-city")),
        ("lapras", (MethodKind.IN_GAME, EncounterKind.GIFT, "saffron-city")),
        ("omanyte", (MethodKind.IN_GAME, EncounterKind.FOSSIL, "cinnabar-island")),
        ("aerodactyl", (MethodKind.IN_GAME, EncounterKind.FOSSIL, "cinnabar-island")),
        ("snorlax", (MethodKind.IN_GAME, EncounterKind.STATIC, "kanto-route-12")),
        ("zapdos", (MethodKind.IN_GAME, EncounterKind.STATIC, "kanto-power-plant")),
        ("raikou", (MethodKind.IN_GAME, EncounterKind.ROAMING, "roaming-kanto")),
        ("ekans", (MethodKind.IN_GAME, EncounterKind.WILD, "kanto-route-11")),
        ("bulbasaur", (MethodKind.STARTER_GIFT, EncounterKind.STARTER_GIFT, "pallet-town")),
        ("deoxys", (MethodKind.EVENT, EncounterKind.EVENT, "birth-island")),
        ("mew", (MethodKind.EVENT, None, None)),
    ],
)
def test_known_cases(slug: str, expected: tuple[object, ...]) -> None:
    assert first_way(slug) == expected


@pytest.mark.rn("RN-26")
def test_raikou_depends_on_the_starter() -> None:
    """CA-80: «Pokémon errante si elegiste a Squirtle»."""
    method = obtention_methods(firered_pokedex(), "raikou").recommended
    assert method is not None
    assert method.way is not None
    assert method.way.choice == "starter-squirtle"


@pytest.mark.rn("RN-26")
def test_hitmonlee_or_hitmonchan() -> None:
    """CA-87: a gift chosen among two, after evolving Tyrogue."""
    kinds = [
        (m.kind, m.way.alternatives if m.way else ()) for m in recommended("hitmonlee").methods
    ]
    assert kinds[:2] == [(MethodKind.EVOLVE, ()), (MethodKind.IN_GAME, ("hitmonchan",))]


@pytest.mark.rn("RN-25")
def test_sandshrew_comes_from_the_other_games() -> None:
    """Exclusive to LeafGreen: transferred from a compatible game (form 5)."""
    methods = recommended("sandshrew").methods
    assert {m.kind for m in methods} == {MethodKind.TRANSFER}
    assert "leafgreen" in {m.game for m in methods}
    registered = recommended("sandshrew", completed={"leafgreen": ["sandshrew"]}).methods
    assert (registered[0].kind, registered[0].game) == (MethodKind.TRANSFER_REGISTERED, "leafgreen")


@pytest.mark.rn("RN-24")
def test_pichu_is_bred_from_a_pikachu_of_the_game() -> None:
    """Form 4: Pikachu is wild in the Viridian Forest; with it registered, form 1."""
    assert [m.kind for m in recommended("pichu").methods][:1] == [MethodKind.BREED]
    assert [m.kind for m in recommended("pichu", registered=["pikachu"]).methods][:1] == [
        MethodKind.BREED_REGISTERED
    ]


@pytest.mark.rn("RN-22")
@pytest.mark.rn("RN-23")
def test_progress_and_objective_of_a_new_pokedex_are_fast() -> None:
    """The whole Pokédex, with every way of every species, in well under a second."""
    start = time.perf_counter()
    ctx = firered_pokedex(started=False)
    result = progress(ctx)
    first = objective(ctx)
    for entry in ctx.species:
        obtention_methods(ctx, entry.species)
    assert time.perf_counter() - start < 1
    assert (result.percent, result.total, result.status) == (0, 386, PokedexStatus.NOT_STARTED)
    assert first == "bulbasaur"
