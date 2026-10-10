"""Build the FireRed Pokédex extract of reference.sqlite used by the Pokédex real scenario.

Usage (from the repository root, after a real load):

    uv run python tests/core/fixtures/extract_pokedex_firered.py data/reference.sqlite

It writes ``tests/core/fixtures/pokedex_firered.json`` with what
``tests/core/pokedex_scenario.py`` needs to build a ``PokedexContext``: the game, every
species of its Pokédex with its number, egg groups, evolution steps in the game, encounters
and whether it is an event Pokémon, its starters, and the games that can send Pokémon to
FireRed with their encounters and starters. Forms become species, as the Pokédex counts them
(RN-22). See the README next to this script.
"""

import json
import sqlite3
import sys
from pathlib import Path

GAME = "firered"
OUTPUT = Path(__file__).resolve().parent / "pokedex_firered.json"


def _rows(db: sqlite3.Connection, sql: str, *params: object) -> list[sqlite3.Row]:
    return list(db.execute(sql, params))


def _encounters(db: sqlite3.Connection, game: str) -> dict[str, list[list[object]]]:
    """Encounters of ``game`` by species, as ``[location, area, method, rarity, conditions,
    event_item]``."""
    rows = _rows(
        db,
        "SELECT p.species, e.location, e.area, e.method, e.rarity, e.conditions, l.event_item "
        "FROM encounter e JOIN pokemon p ON p.slug = e.pokemon "
        "JOIN location l ON l.slug = e.location WHERE e.game = ? "
        "ORDER BY p.species, e.location, e.area, e.method, e.conditions",
        game,
    )
    result: dict[str, list[list[object]]] = {}
    for r in rows:
        result.setdefault(r["species"], []).append(
            [
                r["location"],
                r["area"],
                r["method"],
                r["rarity"],
                json.loads(r["conditions"]),
                r["event_item"],
            ]
        )
    return result


def _starters(db: sqlite3.Connection, game: str) -> list[str]:
    """The species received as the game's starter: the first stage of each line (CA-87)."""
    result = []
    for row in _rows(
        db,
        "SELECT p.species FROM game_starter g JOIN pokemon p ON p.slug = g.pokemon "
        "WHERE g.game = ?",
        game,
    ):
        species = row["species"]
        while True:
            [current] = _rows(db, "SELECT evolves_from FROM species WHERE slug = ?", species)
            if current["evolves_from"] is None:
                break
            species = current["evolves_from"]
        result.append(species)
    return sorted(result)


def extract(db: sqlite3.Connection) -> dict[str, object]:
    [game] = _rows(db, "SELECT * FROM game WHERE slug = ?", GAME)
    [run] = _rows(db, "SELECT pokeapi_commit FROM ingest_run")
    mechanics = _rows(db, "SELECT mechanic FROM game_mechanic WHERE game = ? AND value", GAME)
    dex = _rows(
        db,
        "SELECT s.slug, n.number, s.generation, s.requires_incense FROM game_pokedex g "
        "JOIN pokedex_number n ON n.pokedex = g.pokedex JOIN species s ON s.slug = n.species "
        "WHERE g.game = ? ORDER BY n.number",
        GAME,
    )
    in_dex = {r["slug"] for r in dex}
    steps = _rows(
        db,
        "SELECT a.species AS from_species, b.species AS to_species, e.trigger, e.conditions "
        "FROM evolution_step e JOIN pokemon a ON a.slug = e.from_pokemon "
        "JOIN pokemon b ON b.slug = e.to_pokemon "
        "WHERE e.version_group = ? AND a.is_default AND b.is_default ORDER BY e.id",
        game["version_group"],
    )
    events = {
        r["species"]
        for r in _rows(
            db,
            "SELECT p.species FROM event_pokemon e JOIN pokemon p ON p.slug = e.pokemon "
            "WHERE e.game = ?",
            GAME,
        )
    }
    encounters = _encounters(db, GAME)
    species = []
    for r in dex:
        egg_groups = _rows(
            db,
            "SELECT egg_group FROM species_egg_group WHERE species = ? ORDER BY 1",
            r["slug"],
        )
        species.append(
            {
                "species": r["slug"],
                "number": r["number"],
                "generation": r["generation"],
                "egg_groups": [e["egg_group"] for e in egg_groups],
                "requires_incense": bool(r["requires_incense"]),
                "evolutions": [
                    {
                        "from": s["from_species"],
                        "trigger": s["trigger"],
                        "conditions": json.loads(s["conditions"]),
                    }
                    for s in steps
                    if s["to_species"] == r["slug"] and s["from_species"] in in_dex
                ],
                "encounters": encounters.get(r["slug"], []),
                "is_event": r["slug"] in events,
            }
        )
    sources = [
        {
            "game": t["from_game"],
            "max_species_generation": t["max_species_generation"],
            "starters": _starters(db, t["from_game"]),
            "encounters": _encounters(db, t["from_game"]),
        }
        for t in _rows(
            db,
            "SELECT t.* FROM game_transfer t JOIN game g ON g.slug = t.from_game "
            "WHERE t.to_game = ? ORDER BY g.release_order, g.slug",
            GAME,
        )
    ]
    return {
        "source": {"game": GAME, "pokeapi": {"commit": run["pokeapi_commit"]}},
        "game": {
            "slug": GAME,
            "generation": game["generation"],
            "mechanics": [r["mechanic"] for r in mechanics],
            "has_breeding": bool(game["has_breeding"]),
            "starters": _starters(db, GAME),
        },
        "species": species,
        "sources": sources,
    }


def _dumps(data: dict[str, object]) -> str:
    """Indented JSON with each encounter on one line, so a new load gives a readable diff."""
    compact: list[str] = []

    def mark(value: object) -> object:
        if isinstance(value, dict):
            return {k: mark(v) for k, v in value.items()}
        if isinstance(value, list) and value and isinstance(value[0], list):
            compact.extend(json.dumps(row, ensure_ascii=False) for row in value)
            return [f"@{len(compact) - len(value) + i}@" for i in range(len(value))]
        if isinstance(value, list):
            return [mark(v) for v in value]
        return value

    text = json.dumps(mark(data), ensure_ascii=False, indent=1)
    for index, row in enumerate(compact):
        text = text.replace(f'"@{index}@"', row, 1)
    return text


def main() -> None:
    db = sqlite3.connect(sys.argv[1])
    db.row_factory = sqlite3.Row
    data = extract(db)
    OUTPUT.write_text(_dumps(data) + "\n", encoding="utf-8")
    species, sources = data["species"], data["sources"]
    assert isinstance(species, list)
    assert isinstance(sources, list)
    print(f"{OUTPUT}: {len(species)} especies, {len(sources)} juegos de origen")


if __name__ == "__main__":
    main()
