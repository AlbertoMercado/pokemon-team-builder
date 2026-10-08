"""Build the PokeAPI CSV extract used by the ingest tests.

Usage (from the repository root, with the full CSV dump of the pinned commit cached by a
real load):

    uv run python tests/ingest/fixtures/pokeapi/extract_pokeapi.py <full-csv-dir>

It writes ``tests/ingest/fixtures/pokeapi/<commit>/``: small files are copied whole and
large ones are filtered to the species in ``SPECIES`` (and the rows they reference); the
encounters, also to the loaded games. The species are chosen for their special cases; see the
README next to this script.
"""

import csv
import sys
from collections.abc import Callable
from pathlib import Path

COMMIT = "bc92d3b6029ef1abe9e7ad424c400b338f3c11fe"
OUTPUT = Path(__file__).resolve().parent / COMMIT

SPECIES = frozenset(
    {
        *(1, 2, 3),  # Bulbasaur line: plain level-up
        *(25, 26, 172),  # Pichu line: baby, friendship, item, Alolan Raichu rows
        *(35, 36, 173),  # Clefairy line: Normal until the 5th generation
        *(41, 42, 169),  # Zubat line: Crobat is a 2nd generation evolution
        *(79, 80, 199),  # Slowpoke line: trade with held item, Galarian rows
        *(81, 82),  # Magnemite line: Electric only in the 1st generation
        *(92, 93, 94),  # Gastly line: trade
        *(113, 242, 440),  # Chansey line: Happiny is a 4th generation baby
        132,  # Ditto: egg group "ditto"
        *(133, 134, 135, 136, 196, 197),  # Eevee: items, friendship and time of day
        150,  # Mewtwo: legendary
        *(183, 184, 298),  # Marill line: Azurill is an incense baby of the 3rd generation
        *(202, 360),  # Wobbuffet line: Wynaut is the other incense baby
        *(236, 106, 107, 237),  # Tyrogue: stat comparison
        *(265, 266, 267, 268, 269),  # Wurmple: random evolution
        *(290, 291, 292),  # Nincada: Shedinja by "shed"
        *(349, 350),  # Feebas: beauty, then trade with item in later generations
        386,  # Deoxys: default form "deoxys-normal", other forms not loaded; Birth Island
        23,  # Ekans: wild in FireRed, not in LeafGreen
        27,  # Sandshrew: not in FireRed (LeafGreen exclusive)
        *(100, 101),  # Voltorb, Electrode: several static ones in the Power Plant of Yellow
        131,  # Lapras: gift and surf in FireRed
        *(138, 140, 142),  # Omanyte, Kabuto, Aerodactyl: fossils
        143,  # Snorlax: Poké Flute
        145,  # Zapdos: static
        151,  # Mew: event, no encounter
        163,  # Hoothoot: only at night in Gold
        175,  # Togepi: gift egg
        *(243, 244, 245),  # Raikou, Entei, Suicune: roaming, by starter in FireRed
        249,  # Lugia: static in Navel Rock, reached only with an event item
        251,  # Celebi: event, spin-off bonus disc and Virtual Console
        385,  # Jirachi: spin-off methods only
    }
)
# Versions of the loaded games (red to leafgreen): the encounters of the rest are left out.
LOADED_VERSIONS = frozenset(str(version) for version in range(1, 12))
# Items handed out at events that curated locations need (locations.yaml).
EVENT_ITEMS = frozenset({"mysticticket", "auroraticket", "old-sea-map", "eon-ticket"})

WHOLE_FILES = (
    "generations",
    "version_groups",
    "versions",
    "version_names",
    "types",
    "type_names",
    "type_efficacy",
    "type_efficacy_past",
    "egg_groups",
    "evolution_triggers",
    "regions",
    "pokedexes",
    "pokedex_version_groups",
    "encounter_methods",
    "encounter_condition_values",
)

type Row = dict[str, str]


def read(source: Path, name: str) -> tuple[list[str], list[Row]]:
    with (source / f"{name}.csv").open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def write(name: str, header: list[str], rows: list[Row]) -> None:
    with (OUTPUT / f"{name}.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def keep(source: Path, name: str, predicate: Callable[[Row], bool]) -> list[Row]:
    header, rows = read(source, name)
    kept = [row for row in rows if predicate(row)]
    write(name, header, kept)
    return kept


def in_ids(ids: set[str]) -> Callable[[Row], bool]:
    return lambda row: row["id"] in ids


def main(source: Path) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in WHOLE_FILES:
        header, rows = read(source, name)
        write(name, header, rows)

    def in_species(column: str) -> Callable[[Row], bool]:
        return lambda row: int(row[column]) in SPECIES

    keep(source, "pokemon_species", in_species("id"))
    keep(
        source,
        "pokemon_species_names",
        lambda row: (
            int(row["pokemon_species_id"]) in SPECIES and row["local_language_id"] in {"7", "9"}
        ),
    )
    keep(source, "pokemon_egg_groups", in_species("species_id"))
    keep(source, "pokemon_dex_numbers", in_species("species_id"))
    pokemon_ids = {row["id"] for row in keep(source, "pokemon", in_species("species_id"))}
    for name in ("pokemon_forms", "pokemon_types", "pokemon_types_past"):
        keep(source, name, lambda row: row["pokemon_id"] in pokemon_ids)

    encounters = keep(
        source,
        "encounters",
        lambda row: row["version_id"] in LOADED_VERSIONS and row["pokemon_id"] in pokemon_ids,
    )
    encounter_ids = {row["id"] for row in encounters}
    keep(source, "encounter_condition_value_map", lambda row: row["encounter_id"] in encounter_ids)
    keep(source, "encounter_slots", in_ids({row["encounter_slot_id"] for row in encounters}))
    areas = keep(source, "location_areas", in_ids({row["location_area_id"] for row in encounters}))

    evolutions = keep(source, "pokemon_evolution", in_species("evolved_species_id"))

    def referenced(*columns: str) -> set[str]:
        return {row[column] for row in evolutions for column in columns if row[column]}

    items = referenced("trigger_item_id", "held_item_id")
    keep(source, "items", lambda row: row["id"] in items or row["identifier"] in EVENT_ITEMS)
    keep(source, "moves", in_ids(referenced("known_move_id", "used_move_id")))
    locations = {row["location_id"] for row in evolutions if row["location_id"]}
    locations |= {row["location_id"] for row in areas}
    keep(source, "locations", in_ids(locations))
    keep(
        source,
        "location_names",
        lambda row: row["location_id"] in locations and row["local_language_id"] in {"7", "9"},
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
