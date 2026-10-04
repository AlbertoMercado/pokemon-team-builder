"""Breeding: whether a line can be bred and which stage hatches (RN-11, CA-25, CA-36)."""

from core.domain import EvolutionStep, PokemonData, Stage

# Egg groups whose Pokémon never lay eggs of their own line: "no-eggs" (legendaries,
# mythicals, babies, Unown…) and "ditto" (Ditto breeds with others, but never hatches).
NON_BREEDING_EGG_GROUPS = frozenset({"no-eggs", "ditto"})


def can_be_bred(pokemon: PokemonData) -> bool:
    """Some species of the line lays eggs from which the line hatches (RN-11).

    Pikachu can be bred even though Pichu cannot: Pikachu's eggs hatch Pichu.
    """
    return bool(pokemon.line_egg_groups - NON_BREEDING_EGG_GROUPS)


def egg_stage(pokemon: PokemonData) -> Stage:
    """The stage that hatches and arrives at the target game (CA-25).

    The first stage of the line, unless it is an incense baby: then the next one, which
    hatches without an incense (Marill rather than Azurill, CA-36). An incense baby that is
    itself the favourite hatches as itself.
    """
    first = pokemon.stages[0]
    if first.requires_incense and len(pokemon.stages) > 1:
        return pokemon.stages[1]
    return first


def steps_from_egg(pokemon: PokemonData) -> tuple[EvolutionStep, ...]:
    """Evolution steps from the stage that hatches up to the favourite (RN-15, RN-20)."""
    stages = [stage.pokemon for stage in pokemon.stages]
    start = stages.index(egg_stage(pokemon).pokemon)
    after_egg = set(stages[start:])
    return tuple(step for step in pokemon.evolution_steps if step.from_pokemon in after_egg)
