"""Filters per candidate (RN-03, RN-11, RN-16) and the reason of each discard (RF-10)."""

import pytest

from core.domain import Candidate, GameInfo
from core.rules.candidate import DiscardReason, valid_candidates
from core.rules.catalog import RuleSettings
from tests.core.builders import GEN1_TYPES, candidate, completed, context, pokemon, type_chart

GOLD = GameInfo("gold", 2)
GEN2_CHART = type_chart(2, (*GEN1_TYPES, "steel", "dark"))


def _slugs(candidates: list[Candidate]) -> list[str]:
    return [c.pokemon.slug for c in candidates]


# --- RN-03 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-03")
def test_vulpix_is_a_candidate_in_firered_though_not_catchable() -> None:
    """It exists in FireRed (by trade) and can arrive: that is enough."""
    valid, discards = valid_candidates(context([candidate(pokemon("vulpix", ("fire",)))]))
    assert (_slugs(valid), discards) == (["vulpix"], [])


@pytest.mark.rn("RN-03")
def test_treecko_is_not_a_candidate_in_gold() -> None:
    """Level 1: it appears in the 3rd generation and Gold is of the 2nd."""
    treecko = candidate(pokemon("treecko", ("grass",), generation=3, dex_number=252))
    _, [discard] = valid_candidates(context([treecko], chart=GEN2_CHART, game=GOLD))

    assert (discard.pokemon, discard.rule_id, discard.reason) == (
        "treecko",
        "RN-03",
        DiscardReason.GENERATION,
    )
    assert "3.ª generación" in discard.detail


@pytest.mark.rn("RN-03")
def test_form_that_cannot_be_had_in_the_game() -> None:
    """Level 2: Hisuian Growlithe passes the generation level but does not exist in Sword."""
    growlithe = pokemon("growlithe-hisui", ("fire", "rock"), generation=3, region="hisui")
    _, [discard] = valid_candidates(context([candidate(growlithe, exists=False)]))

    assert discard.reason is DiscardReason.GAME
    assert discard.fact_key == "pokemon:firered:growlithe-hisui:exists"


@pytest.mark.rn("RN-03")
def test_raichu_cannot_arrive_at_firered() -> None:
    """Level 3 (CA-28): it hatches as Pichu, which cannot be received before the end."""
    raichu = candidate(
        pokemon("raichu", ("electric",), line=("pichu", "pikachu")), can_arrive=False
    )
    _, [discard] = valid_candidates(context([raichu]))

    assert (discard.rule_id, discard.reason) == ("RN-03", DiscardReason.ARRIVAL)
    assert discard.fact_key == "pokemon:firered:raichu:arrival"


@pytest.mark.rn("RN-03")
def test_availability_is_not_configurable() -> None:
    raichu = candidate(pokemon("raichu", ("electric",)), can_arrive=False)
    settings = RuleSettings.defaults().with_changes(enabled={"RN-11": False, "RN-16": False})
    valid, _ = valid_candidates(context([raichu], settings=settings))
    assert valid == []


# --- RN-11 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-11")
def test_legendaries_are_discarded_with_their_egg_groups() -> None:
    zapdos = candidate(pokemon("zapdos", ("electric", "flying"), egg_groups=("no-eggs",)))
    _, [discard] = valid_candidates(context([zapdos]))

    assert (discard.rule_id, discard.reason) == ("RN-11", DiscardReason.BREEDING)
    assert "no-eggs" in discard.detail
    assert discard.fact_key is None  # automatic data: nothing confirmed by the user


@pytest.mark.rn("RN-11")
def test_breeding_rule_can_be_switched_off() -> None:
    mew = candidate(pokemon("mew", ("psychic",), egg_groups=("no-eggs",)))
    settings = RuleSettings.defaults().with_changes(enabled={"RN-11": False})
    valid, discards = valid_candidates(context([mew], settings=settings))
    assert (_slugs(valid), discards) == (["mew"], [])


# --- RN-16 ---------------------------------------------------------------------------------


@pytest.mark.rn("RN-16")
def test_pokemon_used_in_the_journey_are_discarded() -> None:
    gengar = pokemon("gengar", ("ghost", "poison"), chain=7, line=("gastly", "haunter"))
    haunter = pokemon("haunter", ("ghost", "poison"), chain=7, line=("gastly",))
    journey = [completed("leafgreen", 3, 1, gengar)]

    _, [discard] = valid_candidates(context([candidate(haunter)], journey=journey))

    assert (discard.rule_id, discard.reason) == ("RN-16", DiscardReason.JOURNEY)
    assert "gengar" in discard.detail
    assert "leafgreen" in discard.detail


@pytest.mark.rn("RN-16")
def test_journey_rule_can_be_switched_off() -> None:
    gengar = pokemon("gengar", ("ghost", "poison"), chain=7)
    settings = RuleSettings.defaults().with_changes(enabled={"RN-16": False})
    journey = [completed("leafgreen", 3, 1, gengar)]
    valid, _ = valid_candidates(context([candidate(gengar)], journey=journey, settings=settings))
    assert _slugs(valid) == ["gengar"]


# --- Order ---------------------------------------------------------------------------------


def test_first_failing_filter_is_the_reason() -> None:
    """A legendary that cannot arrive is discarded by RN-03, the first filter."""
    mewtwo = pokemon("mewtwo", ("psychic",), egg_groups=("no-eggs",))
    _, [discard] = valid_candidates(context([candidate(mewtwo, can_arrive=False)]))
    assert discard.rule_id == "RN-03"


def test_results_are_in_canonical_order() -> None:
    """National Pokédex number, then form identifier (RF-08)."""
    favorites = [
        candidate(pokemon("vulpix-alola", ("ice",), dex_number=37, region="alola")),
        candidate(pokemon("gengar", ("ghost", "poison"), dex_number=94)),
        candidate(pokemon("bulbasaur", ("grass", "poison"), dex_number=1)),
        candidate(pokemon("vulpix", ("fire",), dex_number=37)),
        candidate(pokemon("mew", ("psychic",), dex_number=151, egg_groups=("no-eggs",))),
        candidate(pokemon("abra", ("psychic",), dex_number=63), can_arrive=False),
    ]
    valid, discards = valid_candidates(context(favorites))

    assert _slugs(valid) == ["bulbasaur", "vulpix", "vulpix-alola", "gengar"]
    assert [d.pokemon for d in discards] == ["abra", "mew"]
