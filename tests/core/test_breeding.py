"""Breeding and the stage that hatches (RN-11, CA-25, CA-36), with the DDF's examples."""

import pytest

from core import breeding
from tests.core.builders import pokemon, stage, step


@pytest.mark.rn("RN-11")
@pytest.mark.parametrize(
    ("slug", "egg_groups", "expected"),
    [
        ("zapdos", ("no-eggs",), False),  # legendary
        ("mew", ("no-eggs",), False),  # mythical
        ("ditto", ("ditto",), False),  # breeds with others, never hatches
        ("unown", ("no-eggs",), False),
        ("dragonite", ("water1", "dragon"), True),  # pseudo-legendary, hatches as Dratini
    ],
)
def test_breeding_by_egg_groups(slug: str, egg_groups: tuple[str, ...], expected: bool) -> None:
    assert breeding.can_be_bred(pokemon(slug, egg_groups=egg_groups)) is expected


@pytest.mark.rn("RN-11")
def test_line_can_be_bred_even_if_a_stage_cannot() -> None:
    """Pikachu can be bred though Pichu cannot: Pikachu's eggs hatch Pichu. The line's egg
    groups include later evolutions, so Pichu as a favourite can be bred too."""
    line_groups = ("no-eggs", "ground", "fairy")  # Pichu's plus Pikachu's and Raichu's
    pichu = pokemon("pichu", ("electric",), egg_groups=line_groups)
    pikachu = pokemon("pikachu", ("electric",), line=("pichu",), egg_groups=line_groups)
    assert breeding.can_be_bred(pichu)
    assert breeding.can_be_bred(pikachu)


def test_egg_stage_is_the_first_of_the_line() -> None:
    """CA-25: Raichu hatches as Pichu."""
    raichu = pokemon("raichu", ("electric",), line=("pichu", "pikachu"))
    assert breeding.egg_stage(raichu).pokemon == "pichu"


def test_incense_baby_is_skipped() -> None:
    """CA-36: Azumarill hatches as Marill, which needs no incense; Azurill as itself."""
    azurill = stage("azurill", is_baby=True, requires_incense=True)
    azumarill = pokemon(
        "azumarill",
        ("water",),
        stages=[azurill, stage("marill"), stage("azumarill")],
        steps=[
            step("azurill", "marill", minimum_happiness=160),
            step("marill", "azumarill", minimum_level=18),
        ],
    )
    only_azurill = pokemon("azurill", ("normal",), stages=[azurill], steps=[])

    assert breeding.egg_stage(azumarill).pokemon == "marill"
    assert breeding.egg_stage(only_azurill).pokemon == "azurill"
    # Azurill's friendship step is not part of Azumarill's journey from the egg (RN-15).
    assert [(s.from_pokemon, s.to_pokemon) for s in breeding.steps_from_egg(azumarill)] == [
        ("marill", "azumarill")
    ]


def test_steps_from_egg_of_a_plain_line() -> None:
    gengar = pokemon(
        "gengar",
        ("ghost", "poison"),
        line=("gastly", "haunter"),
        steps=[step("gastly", "haunter", minimum_level=25), step("haunter", "gengar", "trade")],
    )
    assert [s.trigger for s in breeding.steps_from_egg(gengar)] == ["level-up", "trade"]
