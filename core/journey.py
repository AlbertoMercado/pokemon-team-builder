"""Exclusions from the user's journey: Pokémon already used are not repeated (RN-16).

For a target game, the teams of these Hall of Fame entries count (CA-17):

1. the last completed game, whatever its generation;
2. every completed game of the target game's generation.

From each member, its evolution line in the same form is excluded (CA-18), except:
Dragonite's line is never excluded, and from Eevee's line only the form used is (CA-21).
"""

from collections.abc import Sequence

from core.domain import HallOfFameEntry, JourneyMember, PokemonData
from core.domain.lines import DRAGONITE_LINE, EEVEE, EEVEE_EVOLUTIONS


def affected_entries(
    journey: Sequence[HallOfFameEntry], target_generation: int
) -> tuple[HallOfFameEntry, ...]:
    """Entries whose teams are excluded in a game of ``target_generation``, in order."""
    if not journey:
        return ()
    last = max(journey, key=lambda entry: entry.sequence)
    return tuple(
        entry
        for entry in sorted(journey, key=lambda entry: entry.sequence)
        if entry is last or entry.generation == target_generation
    )


def _excludes(member: JourneyMember, pokemon: PokemonData) -> bool:
    if member.pokemon in DRAGONITE_LINE:
        return False
    if member.pokemon == EEVEE or member.pokemon in EEVEE_EVOLUTIONS:
        return pokemon.slug == member.pokemon
    return pokemon.evolution_chain == member.evolution_chain and pokemon.region == member.region


def excluding_entry(
    pokemon: PokemonData, journey: Sequence[HallOfFameEntry], target_generation: int
) -> tuple[HallOfFameEntry, JourneyMember] | None:
    """The first entry and member that exclude ``pokemon``, or ``None`` if it is not excluded."""
    for entry in affected_entries(journey, target_generation):
        for member in entry.members:
            if _excludes(member, pokemon):
                return entry, member
    return None
