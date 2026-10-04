"""Build the FireRed extract of reference.sqlite used by the engine's real scenario.

Usage (from the repository root, after a real load):

    uv run python tests/core/fixtures/extract_firered.py data/reference.sqlite

It writes ``tests/core/fixtures/firered.json`` with the data ``tests/core/scenario.py`` needs
to build a ``GameContext``: the game and its mechanics, the 3rd generation type chart, every
form that can arrive at FireRed with its line, egg groups and evolution steps, and the key
battles with the types of each rival. See the README next to this script.
"""

import json
import sqlite3
import sys
from itertools import pairwise
from pathlib import Path

GAME = "firered"
OUTPUT = Path(__file__).resolve().parent / "firered.json"


def _rows(db: sqlite3.Connection, sql: str, *params: object) -> list[sqlite3.Row]:
    return list(db.execute(sql, params))


def _types(db: sqlite3.Connection, pokemon: str, generation: int) -> list[str]:
    rows = _rows(
        db,
        "SELECT type FROM pokemon_type WHERE pokemon = ? AND generation = ? ORDER BY slot",
        pokemon,
        generation,
    )
    return [row["type"] for row in rows]


def _default_form(db: sqlite3.Connection, species: str) -> str:
    [row] = _rows(db, "SELECT slug FROM pokemon WHERE species = ? AND is_default", species)
    return str(row["slug"])


def _pokemon(
    db: sqlite3.Connection, slug: str, generation: int, version_group: str
) -> dict[str, object]:
    [row] = _rows(
        db,
        "SELECT p.slug, p.species, p.region, s.name_es, s.dex_number, s.generation, "
        "s.evolution_chain, s.is_legendary, s.is_mythical, gp.exists_in_game, gp.can_arrive "
        "FROM pokemon p JOIN species s ON s.slug = p.species "
        "JOIN game_pokemon gp ON gp.pokemon = p.slug AND gp.game = ? WHERE p.slug = ?",
        GAME,
        slug,
    )
    line: list[sqlite3.Row] = []
    species: str | None = row["species"]
    while species is not None:
        [current] = _rows(db, "SELECT * FROM species WHERE slug = ?", species)
        line.insert(0, current)
        species = current["evolves_from"]
    stages = [
        {
            "pokemon": _default_form(db, s["slug"]),
            "species": s["slug"],
            "is_baby": bool(s["is_baby"]),
            "requires_incense": bool(s["requires_incense"]),
        }
        for s in line
    ]
    stage_slugs = [stage["pokemon"] for stage in stages]
    steps = [
        {
            "from": r["from_pokemon"],
            "to": r["to_pokemon"],
            "trigger": r["trigger"],
            "conditions": json.loads(r["conditions"]),
        }
        for a, b in pairwise(stage_slugs)
        for r in _rows(
            db,
            "SELECT * FROM evolution_step WHERE version_group = ? AND from_pokemon = ? "
            "AND to_pokemon = ? ORDER BY id",
            version_group,
            a,
            b,
        )
    ]
    egg_groups = _rows(
        db,
        "SELECT DISTINCT e.egg_group FROM species_egg_group e JOIN species s "
        "ON s.slug = e.species WHERE s.evolution_chain = ? ORDER BY e.egg_group",
        row["evolution_chain"],
    )
    return {
        "slug": row["slug"],
        "species": row["species"],
        "name": row["name_es"],
        "dex_number": row["dex_number"],
        "generation": row["generation"],
        "types": _types(db, slug, generation),
        "evolution_chain": row["evolution_chain"],
        "stages": stages,
        "line_egg_groups": [r["egg_group"] for r in egg_groups],
        "evolution_steps": steps,
        "region": row["region"],
        "is_legendary": bool(row["is_legendary"]),
        "is_mythical": bool(row["is_mythical"]),
        "exists_in_game": bool(row["exists_in_game"]),
        "can_arrive": bool(row["can_arrive"]),
    }


def extract(db: sqlite3.Connection) -> dict[str, object]:
    [game] = _rows(db, "SELECT * FROM game WHERE slug = ?", GAME)
    generation = game["generation"]
    [run] = _rows(db, "SELECT pokeapi_commit FROM ingest_run")
    types = [
        r["slug"] for r in _rows(db, "SELECT slug FROM type WHERE generation <= ?", generation)
    ]
    efficacy = _rows(
        db, "SELECT * FROM type_efficacy WHERE generation = ? ORDER BY 2, 3", generation
    )
    arriving = _rows(
        db,
        "SELECT gp.pokemon FROM game_pokemon gp JOIN pokemon p ON p.slug = gp.pokemon "
        "JOIN species s ON s.slug = p.species WHERE gp.game = ? AND gp.can_arrive "
        "ORDER BY s.dex_number, p.slug",
        GAME,
    )
    battles = []
    for battle in _rows(db, 'SELECT * FROM key_battle WHERE game = ? ORDER BY "order"', GAME):
        rivals = _rows(
            db,
            "SELECT pokemon FROM key_battle_pokemon WHERE battle = ? ORDER BY position",
            battle["slug"],
        )
        battles.append(
            {
                "slug": battle["slug"],
                "category": battle["category"],
                "trainer": battle["trainer_name"],
                "rivals": [
                    {"pokemon": r["pokemon"], "types": _types(db, r["pokemon"], generation)}
                    for r in rivals
                ],
            }
        )
    mechanics = _rows(db, "SELECT mechanic FROM game_mechanic WHERE game = ? AND value", GAME)
    return {
        "source": {"game": GAME, "pokeapi": {"commit": run["pokeapi_commit"]}},
        "game": {
            "slug": GAME,
            "generation": generation,
            "mechanics": [r["mechanic"] for r in mechanics],
        },
        "types": types,
        "type_efficacy": [[r["attacking"], r["defending"], r["factor"]] for r in efficacy],
        "pokemon": [
            _pokemon(db, r["pokemon"], generation, game["version_group"]) for r in arriving
        ],
        "key_battles": battles,
    }


def main() -> None:
    db = sqlite3.connect(sys.argv[1])
    db.row_factory = sqlite3.Row
    data = extract(db)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pokemon, battles = data["pokemon"], data["key_battles"]
    assert isinstance(pokemon, list)
    assert isinstance(battles, list)
    print(f"{OUTPUT}: {len(pokemon)} Pokémon, {len(battles)} combates clave")


if __name__ == "__main__":
    main()
