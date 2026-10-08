"""PokeAPI source: species, forms, types, type charts, egg groups, evolutions, games,
Pokédexes and encounters.

Reads the CSV dump of the PokeAPI repository pinned to the commit in
``data/curated/pokeapi.yaml`` (ADR-0004), and uses the curated data for incense babies and
arrival proposals. See docs/02-ddt/carga-datos.md.
"""

from collections.abc import Iterable
from functools import cached_property

from db.reference import ReferenceModel
from ingest.sources.curated import CuratedData
from ingest.sources.pokeapi.download import CsvCache
from ingest.sources.pokeapi.index import PokemonIndex, build_index
from ingest.sources.pokeapi.rows import (
    DexNumberRow,
    EggGroupRow,
    EncounterConditionRow,
    EncounterRow,
    EncounterSlotRow,
    EvolutionRow,
    GenerationRow,
    IdentifierRow,
    LocationAreaRow,
    LocationNameRow,
    PokedexRow,
    PokedexVersionGroupRow,
    PokemonFormRow,
    PokemonRow,
    PokemonTypePastRow,
    PokemonTypeRow,
    SpeciesEggGroupRow,
    SpeciesNameRow,
    SpeciesRow,
    TypeEfficacyPastRow,
    TypeEfficacyRow,
    TypeNameRow,
    TypeRow,
    VersionGroupRow,
    VersionNameRow,
    VersionRow,
    read_rows,
)
from ingest.sources.pokeapi.transform import PokeapiTables, build_rows


class PokeapiCsvSource:
    """Ingest source that builds rows from the PokeAPI CSV dump of one commit."""

    name = "pokeapi"

    def __init__(self, cache: CsvCache, curated: CuratedData) -> None:
        self._cache = cache
        self._curated = curated

    @property
    def pokeapi_commit(self) -> str:
        return self._cache.commit

    def rows(self) -> Iterable[ReferenceModel]:
        return build_rows(self.tables, self._curated)

    def index(self) -> PokemonIndex:
        """Loaded Pokémon by Spanish name, for the WikiDex source."""
        return build_index(self.tables)

    @cached_property
    def tables(self) -> PokeapiTables:
        """The CSV files, read once per load."""
        return self.read_tables()

    def read_tables(self) -> PokeapiTables:
        """Read (downloading if needed) and validate every CSV file the load uses."""
        c = self._cache
        return PokeapiTables(
            generations=read_rows(c.path("generations"), GenerationRow),
            version_groups=read_rows(c.path("version_groups"), VersionGroupRow),
            versions=read_rows(c.path("versions"), VersionRow),
            version_names=read_rows(c.path("version_names"), VersionNameRow),
            types=read_rows(c.path("types"), TypeRow),
            type_names=read_rows(c.path("type_names"), TypeNameRow),
            type_efficacy=read_rows(c.path("type_efficacy"), TypeEfficacyRow),
            type_efficacy_past=read_rows(c.path("type_efficacy_past"), TypeEfficacyPastRow),
            species=read_rows(c.path("pokemon_species"), SpeciesRow),
            species_names=read_rows(c.path("pokemon_species_names"), SpeciesNameRow),
            pokemon=read_rows(c.path("pokemon"), PokemonRow),
            pokemon_forms=read_rows(c.path("pokemon_forms"), PokemonFormRow),
            pokemon_types=read_rows(c.path("pokemon_types"), PokemonTypeRow),
            pokemon_types_past=read_rows(c.path("pokemon_types_past"), PokemonTypePastRow),
            egg_groups=read_rows(c.path("egg_groups"), EggGroupRow),
            species_egg_groups=read_rows(c.path("pokemon_egg_groups"), SpeciesEggGroupRow),
            evolutions=read_rows(c.path("pokemon_evolution"), EvolutionRow),
            evolution_triggers=read_rows(c.path("evolution_triggers"), IdentifierRow),
            items=read_rows(c.path("items"), IdentifierRow),
            locations=read_rows(c.path("locations"), IdentifierRow),
            moves=read_rows(c.path("moves"), IdentifierRow),
            regions=read_rows(c.path("regions"), IdentifierRow),
            pokedexes=read_rows(c.path("pokedexes"), PokedexRow),
            dex_numbers=read_rows(c.path("pokemon_dex_numbers"), DexNumberRow),
            pokedex_version_groups=read_rows(
                c.path("pokedex_version_groups"), PokedexVersionGroupRow
            ),
            location_names=read_rows(c.path("location_names"), LocationNameRow),
            location_areas=read_rows(c.path("location_areas"), LocationAreaRow),
            encounter_methods=read_rows(c.path("encounter_methods"), IdentifierRow),
            encounter_slots=read_rows(c.path("encounter_slots"), EncounterSlotRow),
            encounters=read_rows(c.path("encounters"), EncounterRow),
            encounter_condition_values=read_rows(
                c.path("encounter_condition_values"), IdentifierRow
            ),
            encounter_conditions=read_rows(
                c.path("encounter_condition_value_map"), EncounterConditionRow
            ),
        )
