"""PokeAPI source: species, forms, types, type charts, egg groups, evolutions and games.

Reads the CSV dump of the PokeAPI repository pinned to the commit in
``data/curated/pokeapi.yaml`` (ADR-0004). See docs/02-ddt/plan-carga-datos.md.
"""

import re
from collections.abc import Iterable
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from db.reference import ReferenceModel
from ingest.sources.pokeapi.download import CsvCache
from ingest.sources.pokeapi.rows import (
    EggGroupRow,
    EvolutionRow,
    GenerationRow,
    IdentifierRow,
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

COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class PinnedCommit(BaseModel):
    """Content of ``data/curated/pokeapi.yaml``: the full SHA of the pinned commit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    commit: str = Field(pattern=COMMIT_PATTERN.pattern)


class PinnedCommitError(Exception):
    """``pokeapi.yaml`` is missing or invalid."""


def read_pinned_commit(path: Path) -> str:
    """Read and validate the pinned PokeAPI commit."""
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        return PinnedCommit.model_validate(content).commit
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise PinnedCommitError(f"{path}: {error}") from error


class PokeapiCsvSource:
    """Ingest source that builds rows from the PokeAPI CSV dump of one commit."""

    name = "pokeapi"

    def __init__(self, cache: CsvCache) -> None:
        self._cache = cache

    @property
    def pokeapi_commit(self) -> str:
        return self._cache.commit

    def rows(self) -> Iterable[ReferenceModel]:
        return build_rows(self.read_tables())

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
        )
