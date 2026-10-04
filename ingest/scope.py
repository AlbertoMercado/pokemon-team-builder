"""Scope of the current load (CA-11): which generations and games are loaded.

Changing the scope (e.g. adding the 4th generation) starts here, but also needs the data
load plan, the checks in ``ingest/checks.py`` and the curated data to be updated.
"""

# Species and games of generations 1 to MAX_GENERATION are loaded (#0001 to #0386).
MAX_GENERATION = 3

# Games of these generations can be chosen as target game (RF-05).
TARGET_GENERATIONS = frozenset({3})

# Breeding exists from the 2nd generation; earlier games cannot be target games (CA-29).
FIRST_BREEDING_GENERATION = 2

# Version groups that PokeAPI files under a loaded generation but are not loaded as games.
EXCLUDED_VERSION_GROUPS = frozenset(
    {
        "colosseum",  # not a main-series game
        "xd",  # not a main-series game
        "red-green-japan",  # released only in Japan, never in Spanish
        "blue-japan",  # released only in Japan, never in Spanish
    }
)
