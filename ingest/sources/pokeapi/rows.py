"""Validated rows of the PokeAPI CSV files used by the load.

Each model declares the columns the load needs, named as in the CSV header. Reading a file
checks that those columns exist and that every value has the right type, so a schema change
upstream fails the load instead of loading wrong data (ADR-0004). Empty cells are read as
missing values.
"""

import csv
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError


class CsvSchemaError(Exception):
    """A CSV file does not have the expected columns or values."""


class CsvRow(BaseModel):
    """Base of every row model: immutable, extra columns ignored."""

    model_config = ConfigDict(frozen=True, extra="ignore")


def read_rows[R: BaseModel](path: Path, model: type[R]) -> list[R]:
    """Read and validate every row of a CSV file."""
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        header = set(reader.fieldnames or [])
        missing = sorted(set(model.model_fields) - header)
        if missing:
            raise CsvSchemaError(f"{path.name}: faltan las columnas {missing}")
        rows: list[R] = []
        for line, raw in enumerate(reader, start=2):
            values = {column: value for column, value in raw.items() if value != ""}
            try:
                rows.append(model.model_validate(values))
            except ValidationError as error:
                raise CsvSchemaError(f"{path.name}, línea {line}: {error}") from error
        return rows


# --- Games ---------------------------------------------------------------------------------


class GenerationRow(CsvRow):
    id: int
    identifier: str


class VersionGroupRow(CsvRow):
    id: int
    identifier: str
    generation_id: int
    order: int


class VersionRow(CsvRow):
    id: int
    version_group_id: int
    identifier: str


class VersionNameRow(CsvRow):
    version_id: int
    local_language_id: int
    name: str


# --- Types ---------------------------------------------------------------------------------


class TypeRow(CsvRow):
    id: int
    identifier: str
    generation_id: int


class TypeNameRow(CsvRow):
    type_id: int
    local_language_id: int
    name: str


class TypeEfficacyRow(CsvRow):
    damage_type_id: int
    target_type_id: int
    damage_factor: int


class TypeEfficacyPastRow(TypeEfficacyRow):
    """Factor that applied up to and including ``generation_id``."""

    generation_id: int


# --- Species and forms ---------------------------------------------------------------------


class SpeciesRow(CsvRow):
    id: int
    identifier: str
    generation_id: int
    evolves_from_species_id: int | None = None
    evolution_chain_id: int
    is_baby: bool
    is_legendary: bool
    is_mythical: bool


class SpeciesNameRow(CsvRow):
    pokemon_species_id: int
    local_language_id: int
    name: str


class PokemonRow(CsvRow):
    id: int
    identifier: str
    species_id: int
    is_default: bool


class PokemonFormRow(CsvRow):
    id: int
    pokemon_id: int
    is_default: bool


class PokemonTypeRow(CsvRow):
    pokemon_id: int
    type_id: int
    slot: int


class PokemonTypePastRow(PokemonTypeRow):
    """Types that applied up to and including ``generation_id``."""

    generation_id: int


class EggGroupRow(CsvRow):
    id: int
    identifier: str


class SpeciesEggGroupRow(CsvRow):
    species_id: int
    egg_group_id: int


# --- Pokédexes ----------------------------------------------------------------------------


class PokedexRow(CsvRow):
    id: int
    identifier: str


class DexNumberRow(CsvRow):
    species_id: int
    pokedex_id: int
    pokedex_number: int


class PokedexVersionGroupRow(CsvRow):
    pokedex_id: int
    version_group_id: int


# --- Encounters ----------------------------------------------------------------------------


class LocationNameRow(CsvRow):
    """``name`` is empty in a few rows that only have a subtitle."""

    location_id: int
    local_language_id: int
    name: str | None = None


class LocationAreaRow(CsvRow):
    """A part of a location; ``identifier`` is empty when the location has a single one."""

    id: int
    location_id: int
    identifier: str | None = None


class EncounterSlotRow(CsvRow):
    """``rarity`` is the probability, in percent, of the slot within its area and method."""

    id: int
    encounter_method_id: int
    rarity: int


class EncounterRow(CsvRow):
    id: int
    version_id: int
    location_area_id: int
    encounter_slot_id: int
    pokemon_id: int
    min_level: int
    max_level: int


class EncounterConditionRow(CsvRow):
    """A condition value of an encounter, such as ``time-night``."""

    encounter_id: int
    encounter_condition_value_id: int


# --- Evolutions ----------------------------------------------------------------------------


class IdentifierRow(CsvRow):
    """Rows of lookup tables whose only needed data is the identifier (items, moves…)."""

    id: int
    identifier: str


class EvolutionRow(BaseModel):
    """A row of ``pokemon_evolution.csv``.

    Unlike other rows, unknown columns are rejected when they have a value: a new kind of
    evolution condition upstream must be reviewed (and classified for RN-15 and RN-20)
    before it is loaded. ``is_default`` marks PokeAPI's canonical method and is not used.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: int
    evolved_species_id: int
    evolution_trigger_id: int
    version_group_id: int
    is_default: bool | None = None
    # Conditions; ``None`` when the cell is empty.
    trigger_item_id: int | None = None
    minimum_level: int | None = None
    gender_id: int | None = None
    location_id: int | None = None
    held_item_id: int | None = None
    time_of_day: str | None = None
    known_move_id: int | None = None
    known_move_type_id: int | None = None
    minimum_happiness: int | None = None
    minimum_beauty: int | None = None
    minimum_affection: int | None = None
    relative_physical_stats: int | None = None
    party_species_id: int | None = None
    party_type_id: int | None = None
    trade_species_id: int | None = None
    needs_overworld_rain: bool | None = None
    turn_upside_down: bool | None = None
    needs_multiplayer: bool | None = None
    near_special_rock: bool | None = None
    region_id: int | None = None
    required_pokemon_form_id: int | None = None
    evolved_pokemon_form_id: int | None = None
    used_move_id: int | None = None
    minimum_move_count: int | None = None
    minimum_steps: int | None = None
    minimum_damage_taken: int | None = None
    nature_bitmask: str | None = None
    condition_expression: str | None = None
    percentage_chance: int | None = None
