"""The real FireRed extract of the engine as a reference.sqlite, for the API tests.

``write_firered(data_dir)`` loads ``tests/core/fixtures/firered.json`` (see its README) with the
models of ``db/reference``, as the ingest would: the 140 forms that can arrive, their lines,
egg groups and evolution steps, the 3rd generation type chart and the 13 key battles. The
origins are those of a real load: mechanics and arrival inferred, the rest automatic. A test
changes them with a ``Load``, or edits ``firered_data()`` before writing it.

It also writes the Pokédex of FireRed and LeafGreen for those forms, from the extract of the
Pokédex scenario (``tests/core/fixtures/pokedex_firered.json``): their numbers, their
encounters in both games (the places named by their identifier), the transfers between them,
the event Pokémon and LeafGreen's starters.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlmodel import Session, create_engine

from db.reference import (
    BattleCategory,
    Encounter,
    EventPokemon,
    EvolutionStep,
    Game,
    GameMechanic,
    GamePokedex,
    GamePokemon,
    GameStarter,
    GameTransfer,
    Generation,
    IngestRun,
    KeyBattle,
    KeyBattlePokemon,
    Location,
    Origin,
    Pokedex,
    PokedexNumber,
    Pokemon,
    PokemonType,
    Species,
    SpeciesEggGroup,
    Type,
    TypeEfficacy,
    VersionGroup,
    create_reference_schema,
)

FIXTURE = Path(__file__).resolve().parents[1] / "core" / "fixtures" / "firered.json"
POKEDEX_FIXTURE = FIXTURE.with_name("pokedex_firered.json")
GAME = "firered"
VERSION_GROUP = "firered-leafgreen"
LOADED_AT = datetime(2026, 10, 4, 10, 0, 0, tzinfo=UTC)
MECHANICS = ("contests", "day_night_cycle")
SECOND_GENERATION_TYPES = {"steel", "dark"}

# Rivals of the key battles that cannot arrive at FireRed, so they are not in the extract.
RIVAL_DEX = {"pikachu": 25, "raichu": 26, "hitmonlee": 106, "hitmonchan": 107, "jynx": 124}

# The extract's JSON: nested dicts and lists, as ``tests/core/scenario.py`` reads it.
type ScenarioData = dict[str, Any]


@cache
def _raw() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def firered_data() -> ScenarioData:
    """A copy of the extract, to change before writing it."""
    data: ScenarioData = json.loads(_raw())
    _add_missing_rivals(data)
    return data


def _add_missing_rivals(data: ScenarioData) -> None:
    """Rivals outside the extract, as forms that exist in FireRed but cannot arrive."""
    known = {p["slug"] for p in data["pokemon"]}
    for battle in data["key_battles"]:
        for rival in battle["rivals"]:
            slug = rival["pokemon"]
            if slug in known:
                continue
            known.add(slug)
            data["pokemon"].append(
                {
                    "slug": slug,
                    "species": slug,
                    "name": slug.title(),
                    "dex_number": RIVAL_DEX[slug],
                    "generation": 1,
                    "types": rival["types"],
                    "evolution_chain": 1000 + RIVAL_DEX[slug],
                    "stages": [
                        {
                            "pokemon": slug,
                            "species": slug,
                            "is_baby": False,
                            "requires_incense": False,
                        }
                    ],
                    "line_egg_groups": ["field"],
                    "evolution_steps": [],
                    "region": None,
                    "is_legendary": False,
                    "is_mythical": False,
                    "exists_in_game": True,
                    "can_arrive": False,
                }
            )


@dataclass(frozen=True)
class Load:
    """What the load proposes; by default, as a real load does.

    ``battle_origins`` changes the origin of some key battles, by slug (``firered-misty``); a
    pending one loses its team. ``arrival`` changes the proposal of whether some forms can
    arrive.
    """

    mechanic_origin: Origin = Origin.INFERRED
    arrival_origin: Origin = Origin.INFERRED
    battle_origins: Mapping[str, Origin] = field(default_factory=dict)
    arrival: Mapping[str, bool] = field(default_factory=dict)


def write_firered(
    data_dir: Path, data: ScenarioData | None = None, load: Load | None = None
) -> Path:
    """Writes ``data`` (the extract by default) as ``data_dir/reference.sqlite``.

    As the ingest does, rows are written without enforcing foreign keys, in any order, and
    checked at the end.
    """
    data = data or firered_data()
    load = load or Load()
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "reference.sqlite"
    path.unlink(missing_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    create_reference_schema(engine)
    with Session(engine) as session:
        _write(session, data, load)
        session.commit()
        broken = session.connection().execute(text("PRAGMA foreign_key_check")).all()
    engine.dispose()
    assert not broken, f"claves foráneas rotas: {broken}"
    return path


def _write(session: Session, data: ScenarioData, load: Load) -> None:
    generation = data["game"]["generation"]
    pokemon = data["pokemon"]
    last = max([generation, *(p["generation"] for p in pokemon)])
    session.add_all(Generation(number=n, slug=f"generation-{n}") for n in range(1, last + 1))
    session.add_all(
        Type(slug=t, name_es=t.title(), generation=2 if t in SECOND_GENERATION_TYPES else 1)
        for t in data["types"]
    )
    session.add(VersionGroup(slug=VERSION_GROUP, generation=generation, order=11))
    for slug, order in ((GAME, 10), ("leafgreen", 11)):
        session.add(
            Game(
                slug=slug,
                name_es=slug.title(),
                version_group=VERSION_GROUP,
                generation=generation,
                release_order=order,
                has_breeding=True,
                is_target=True,
            )
        )
    session.add_all(
        TypeEfficacy(generation=generation, attacking=a, defending=d, factor=f)
        for a, d, f in data["type_efficacy"]
    )
    _write_pokemon(session, pokemon, generation, load)
    _write_pokedex(session, {p["slug"] for p in pokemon if p["region"] is None})
    # LeafGreen's starters too, so its Pokédex gives them as gifts that depend on the starter.
    session.add_all(
        GameStarter(game="leafgreen", pokemon=slug) for slug in data["game"]["starters"]
    )
    for mechanic in MECHANICS:
        value = mechanic in data["game"]["mechanics"]
        session.add(
            GameMechanic(
                game=GAME,
                mechanic=mechanic,
                value=None if load.mechanic_origin is Origin.PENDING else value,
                origin=load.mechanic_origin,
                fact_key=f"mechanic:{GAME}:{mechanic}",
            )
        )
    session.add_all(GameStarter(game=GAME, pokemon=slug) for slug in data["game"]["starters"])
    for order, battle in enumerate(data["key_battles"], start=1):
        origin = load.battle_origins.get(battle["slug"], Origin.AUTOMATIC)
        session.add(
            KeyBattle(
                slug=battle["slug"],
                game=GAME,
                category=BattleCategory(battle["category"]),
                trainer_name=battle["trainer"],
                order=order,
                origin=origin,
                fact_key=f"battle:{GAME}:{battle['slug'].removeprefix(GAME + '-')}",
            )
        )
        if origin is not Origin.PENDING:
            session.add_all(
                KeyBattlePokemon(battle=battle["slug"], position=i, pokemon=r["pokemon"])
                for i, r in enumerate(battle["rivals"], start=1)
            )
    session.add(
        IngestRun(
            started_at=LOADED_AT,
            finished_at=LOADED_AT,
            pokeapi_commit=data["source"]["pokeapi"]["commit"],
            games=[GAME],
        )
    )


def _write_pokemon(
    session: Session, pokemon: list[dict[str, Any]], generation: int, load: Load
) -> None:
    species: dict[str, Species] = {}
    egg_groups: set[tuple[str, str]] = set()
    steps: list[tuple[str, str, str, str]] = []
    for p in pokemon:
        previous = None
        for stage in p["stages"]:
            if stage["species"] not in species:
                species[stage["species"]] = Species(
                    slug=stage["species"],
                    dex_number=p["dex_number"] if stage["species"] == p["species"] else 0,
                    name_es=stage["species"].title(),
                    generation=p["generation"],
                    evolves_from=previous,
                    evolution_chain=p["evolution_chain"],
                    is_baby=stage["is_baby"],
                    requires_incense=stage["requires_incense"],
                    is_legendary=False,
                    is_mythical=False,
                )
            previous = stage["species"]
        own = species[p["species"]]
        own.dex_number = p["dex_number"]
        own.name_es = p["name"]
        own.generation = p["generation"]
        own.is_legendary = p["is_legendary"]
        own.is_mythical = p["is_mythical"]
        egg_groups |= {(p["species"], group) for group in p["line_egg_groups"]}
        for step in p["evolution_steps"]:
            key = (step["from"], step["to"], step["trigger"], json.dumps(step["conditions"]))
            if key not in steps:
                steps.append(key)
    session.add_all(species.values())
    session.add_all(SpeciesEggGroup(species=s, egg_group=g) for s, g in sorted(egg_groups))
    for pokeapi_id, p in enumerate(pokemon, start=1):
        slug = p["slug"]
        session.add(
            Pokemon(
                slug=slug,
                species=p["species"],
                name_es=p["name"],
                is_default=p["region"] is None,
                region=p["region"],
                pokeapi_id=pokeapi_id,
            )
        )
        session.add_all(
            PokemonType(pokemon=slug, generation=max(generation, p["generation"]), slot=i, type=t)
            for i, t in enumerate(p["types"], start=1)
        )
        can_arrive = load.arrival.get(slug, p["can_arrive"])
        session.add(
            GamePokemon(
                game=GAME,
                pokemon=slug,
                exists_in_game=p["exists_in_game"],
                exists_origin=Origin.AUTOMATIC,
                can_arrive=None if load.arrival_origin is Origin.PENDING else can_arrive,
                arrival_origin=load.arrival_origin,
            )
        )
    session.add_all(
        EvolutionStep(
            version_group=VERSION_GROUP,
            from_pokemon=a,
            to_pokemon=b,
            trigger=trigger,
            conditions=json.loads(conditions),
        )
        for a, b, trigger, conditions in steps
    )


def _write_pokedex(session: Session, forms: set[str]) -> None:
    """The Pokédex of FireRed and LeafGreen with the species of ``forms``, their base forms."""
    data = json.loads(POKEDEX_FIXTURE.read_text(encoding="utf-8"))
    species = [s for s in data["species"] if s["species"] in forms]
    session.add(Pokedex(slug="national"))
    session.add_all(GamePokedex(game=g, pokedex="national") for g in (GAME, "leafgreen"))
    session.add_all(
        PokedexNumber(pokedex="national", species=s["species"], number=s["number"]) for s in species
    )
    encounters = {GAME: {s["species"]: s["encounters"] for s in species}}
    for source in data["sources"]:
        if source["game"] == "leafgreen":
            encounters["leafgreen"] = {k: v for k, v in source["encounters"].items() if k in forms}
    places: dict[str, str | None] = {}
    for game, by_species in encounters.items():
        for slug, rows in by_species.items():
            for location, area, method, rarity, conditions, event_item in rows:
                places[location] = event_item
                session.add(
                    Encounter(
                        game=game,
                        location=location,
                        area=area,
                        pokemon=slug,
                        method=method,
                        conditions=conditions,
                        rarity=rarity,
                        min_level=5,
                        max_level=5,
                    )
                )
    session.add_all(
        Location(slug=slug, name_en=slug.replace("-", " ").title(), event_item=item)
        for slug, item in places.items()
    )
    session.add_all(
        [
            GameTransfer(from_game="leafgreen", to_game=GAME),
            GameTransfer(from_game=GAME, to_game="leafgreen"),
        ]
    )
    session.add_all(EventPokemon(game=GAME, pokemon=s["species"]) for s in species if s["is_event"])
