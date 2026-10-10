"""The Pokédex of completed games: progress, objective and ways of obtaining (RN-22 to RN-26).

Independent of the team generator (CA-79): it shares only the domain models of the game and
the evolution and breeding rules. See docs/02-ddt/motor.md.
"""

from core.pokedex.domain import DexSpecies, PokedexContext, PokedexContextError, TransferSource
from core.pokedex.encounters import Encounter, EncounterKind, InGameWay, in_game_ways
from core.pokedex.obtention import MethodKind, Obtention, ObtentionMethod, obtention_methods
from core.pokedex.progress import PokedexStatus, Progress, impossible_species, objective, progress

__all__ = [
    "DexSpecies",
    "Encounter",
    "EncounterKind",
    "InGameWay",
    "MethodKind",
    "Obtention",
    "ObtentionMethod",
    "PokedexContext",
    "PokedexContextError",
    "PokedexStatus",
    "Progress",
    "TransferSource",
    "impossible_species",
    "in_game_ways",
    "objective",
    "obtention_methods",
    "progress",
]
