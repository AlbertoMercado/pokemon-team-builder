"""Exclusions of the journey (RN-16, CA-17, CA-18, CA-21), with the DDF's examples."""

import pytest

from core import journey
from core.domain import HallOfFameEntry
from tests.core.builders import completed, pokemon

# Lines (evolution chains) used by the examples.
GASTLY_LINE, PICHU_LINE, CHARMANDER_LINE, RHYHORN_LINE, EEVEE_LINE, DRATINI_LINE = range(1, 7)

DRAGONITE = pokemon("dragonite", ("dragon", "flying"), chain=DRATINI_LINE)
VAPOREON = pokemon("vaporeon", ("water",), chain=EEVEE_LINE)
GENGAR = pokemon("gengar", ("ghost", "poison"), chain=GASTLY_LINE)
RAICHU = pokemon("raichu", ("electric",), chain=PICHU_LINE)
CHARIZARD = pokemon("charizard", ("fire", "flying"), chain=CHARMANDER_LINE)
RHYHORN = pokemon("rhyhorn", ("ground", "rock"), chain=RHYHORN_LINE)
LEAFGREEN_TEAM = (DRAGONITE, VAPOREON, GENGAR, RAICHU, CHARIZARD, RHYHORN)


def _games(entries: tuple[HallOfFameEntry, ...]) -> list[str]:
    return [entry.game for entry in entries]


@pytest.mark.rn("RN-16")
@pytest.mark.parametrize(
    ("completed_games", "target_generation", "excluded_teams"),
    [
        # LeafGreen (3rd) → FireRed (3rd): LeafGreen's team.
        ([("leafgreen", 3)], 3, ["leafgreen"]),
        # LeafGreen (3rd) → Platinum (4th): LeafGreen's team, the last completed game.
        ([("leafgreen", 3)], 4, ["leafgreen"]),
        # LeafGreen → Platinum → HeartGold (4th): Platinum's, not LeafGreen's.
        ([("leafgreen", 3), ("platinum", 4)], 4, ["platinum"]),
        # LeafGreen (3rd) → White (5th) → Emerald (3rd): White's (last) and LeafGreen's.
        ([("leafgreen", 3), ("white", 5)], 3, ["leafgreen", "white"]),
        # Scarlet (9th) → Shield (8th): Scarlet's.
        ([("scarlet", 9)], 8, ["scarlet"]),
    ],
)
def test_which_teams_are_excluded(
    completed_games: list[tuple[str, int]], target_generation: int, excluded_teams: list[str]
) -> None:
    entries = [completed(game, gen, n) for n, (game, gen) in enumerate(completed_games, 1)]
    assert _games(journey.affected_entries(entries, target_generation)) == excluded_teams


def test_no_journey_excludes_nothing() -> None:
    assert journey.affected_entries([], 3) == ()


@pytest.mark.rn("RN-16")
def test_leafgreen_team_in_firered() -> None:
    """DDF example: after LeafGreen with Dragonite, Vaporeon, Gengar, Raichu, Charizard and
    Rhyhorn, FireRed excludes Vaporeon and the lines of Gastly, Pichu, Charmander and
    Rhyhorn. Dragonite, Jolteon, Flareon and Eevee are still candidates."""
    entries = [completed("leafgreen", 3, 1, *LEAFGREEN_TEAM)]

    def excluded(slug: str, chain: int) -> bool:
        return journey.excluding_entry(pokemon(slug, chain=chain), entries, 3) is not None

    assert excluded("vaporeon", EEVEE_LINE)
    assert excluded("gastly", GASTLY_LINE)
    assert excluded("haunter", GASTLY_LINE)
    assert excluded("pikachu", PICHU_LINE)
    assert excluded("charmeleon", CHARMANDER_LINE)
    assert excluded("rhydon", RHYHORN_LINE)
    # Exceptions (CA-21): Dragonite's line is never excluded; from Eevee's, only Vaporeon.
    assert not excluded("dragonite", DRATINI_LINE)
    assert not excluded("dratini", DRATINI_LINE)
    assert not excluded("jolteon", EEVEE_LINE)
    assert not excluded("flareon", EEVEE_LINE)
    assert not excluded("eevee", EEVEE_LINE)


@pytest.mark.rn("RN-16")
def test_line_is_excluded_in_the_same_form_only() -> None:
    """CA-18: using Raichu excludes Pichu's line, but not Alolan Raichu (RN-05)."""
    entries = [completed("leafgreen", 3, 1, RAICHU)]
    alolan = pokemon("raichu-alola", ("electric", "psychic"), chain=PICHU_LINE, region="alola")
    assert journey.excluding_entry(alolan, entries, 7) is None


@pytest.mark.rn("RN-16")
def test_excluding_entry_says_who_and_where() -> None:
    entries = [completed("leafgreen", 3, 1, GENGAR)]
    found = journey.excluding_entry(pokemon("haunter", chain=GASTLY_LINE), entries, 3)
    assert found is not None
    entry, member = found
    assert (entry.game, member.pokemon) == ("leafgreen", "gengar")
