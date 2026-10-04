"""Index of the loaded Pokémon by Spanish name, for sources that name Pokémon (WikiDex)."""

import unicodedata
from dataclasses import dataclass

from ingest import scope
from ingest.sources.pokeapi.transform import SPANISH_LANGUAGE_ID, PokeapiTables

TYPOGRAPHIC_APOSTROPHE = "\u2019"  # PokeAPI writes "Farfetch\u2019d"; WikiDex may use "'"


def normalize_name(name: str) -> str:
    """Comparable form of a Pokémon name: case and typographic apostrophes do not matter."""
    return (
        unicodedata.normalize("NFKC", name).replace(TYPOGRAPHIC_APOSTROPHE, "'").strip().casefold()
    )


@dataclass(frozen=True)
class IndexedPokemon:
    slug: str
    evolution_chain: int


@dataclass(frozen=True)
class PokemonIndex:
    """Default forms of the loaded species, by Spanish name, and the line of each species."""

    by_name: dict[str, IndexedPokemon]
    chain_by_species: dict[str, int]

    def find(self, name: str) -> IndexedPokemon | None:
        return self.by_name.get(normalize_name(name))


def build_index(tables: PokeapiTables) -> PokemonIndex:
    species = {s.id: s for s in tables.species if s.generation_id <= scope.MAX_GENERATION}
    names = {
        n.pokemon_species_id: n.name
        for n in tables.species_names
        if n.local_language_id == SPANISH_LANGUAGE_ID and n.pokemon_species_id in species
    }
    by_name = {
        normalize_name(names[p.species_id]): IndexedPokemon(
            slug=p.identifier, evolution_chain=species[p.species_id].evolution_chain_id
        )
        for p in tables.pokemon
        if p.is_default and p.species_id in names
    }
    chain_by_species = {s.identifier: s.evolution_chain_id for s in species.values()}
    return PokemonIndex(by_name=by_name, chain_by_species=chain_by_species)
