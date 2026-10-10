"""/api/pokedex: the Pokédex of the completed games (RF-20 to RF-24, RN-22 to RN-26).

A small reference.sqlite with FireRed and LeafGreen, which can send Pokémon to each other,
and seven species that cover each way of obtaining: a starter (Bulbasaur), its evolution
(Ivysaur), a wild Pokémon (Pikachu) and its baby (Pichu), one exclusive to LeafGreen
(Sandshrew), an event (Mew) and one only from a spin-off (Jirachi). The rules themselves are
tested in ``tests/core/pokedex/``.
"""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from db.reference import (
    Encounter,
    EventPokemon,
    EvolutionStep,
    GamePokedex,
    GameStarter,
    GameTransfer,
    Location,
    Pokedex,
    PokedexNumber,
    Species,
    SpeciesEggGroup,
)
from db.sqlite import create_sqlite_engine
from tests.api.conftest import ClientFactory
from tests.api.factories import form, reference_database

POKEDEX = "/api/pokedex"
POKEMON = [
    form("bulbasaur", ("grass", "poison"), dex=1),
    form("ivysaur", ("grass", "poison"), dex=2),
    form("pikachu", ("electric",), dex=25),
    form("sandshrew", ("ground",), dex=27),
    form("mew", ("psychic",), dex=151),
    form("pichu", ("electric",), dex=172),
    form("jirachi", ("steel", "psychic"), dex=385),
]
EGG_GROUPS = {
    "bulbasaur": "monster",
    "ivysaur": "monster",
    "pikachu": "field",
    "sandshrew": "field",
    "mew": "no-eggs",
    "pichu": "no-eggs",
    "jirachi": "no-eggs",
}


def _pokedex_data(path: Path) -> None:
    """The Pokédex rows of the ingest over the forms of ``reference_database``."""
    engine = create_sqlite_engine(path)
    with Session(engine) as session:
        for species, previous in (("ivysaur", "bulbasaur"), ("pikachu", "pichu")):
            row = session.get(Species, species)
            assert row is not None
            row.evolves_from = previous
            session.add(row)
        session.add_all(SpeciesEggGroup(species=s, egg_group=g) for s, g in EGG_GROUPS.items())
        session.add_all(
            [
                EvolutionStep(
                    version_group="firered-leafgreen",
                    from_pokemon="bulbasaur",
                    to_pokemon="ivysaur",
                    trigger="level-up",
                    conditions={"minimum_level": 16},
                ),
                EvolutionStep(
                    version_group="firered-leafgreen",
                    from_pokemon="pichu",
                    to_pokemon="pikachu",
                    trigger="level-up",
                    conditions={"minimum_happiness": 220},
                ),
                Pokedex(slug="national"),
            ]
        )
        session.flush()
        session.add_all(
            [
                *(GamePokedex(game=g, pokedex="national") for g in ("firered", "leafgreen")),
                *(
                    PokedexNumber(pokedex="national", species=f.species, number=f.dex)
                    for f in POKEMON
                ),
                Location(slug="pallet-town", name_es="Pueblo Paleta", name_en="Pallet Town"),
                Location(slug="viridian-forest", name_es="Bosque Verde", name_en="Viridian Forest"),
                Location(slug="kanto-route-4", name_en="Route 4"),
                Location(slug="pyrite-town", name_en="Pyrite Town"),
            ]
        )
        session.flush()  # without relationships, SQLAlchemy does not order the inserts
        session.add_all(
            [
                _encounter("firered", "pallet-town", "bulbasaur", "gift"),
                _encounter("firered", "viridian-forest", "pikachu", "walk", 5),
                _encounter("leafgreen", "kanto-route-4", "sandshrew", "walk", 25),
                _encounter("firered", "pyrite-town", "jirachi", "colosseum-bonus-disc-us"),
                GameTransfer(from_game="leafgreen", to_game="firered"),
                GameTransfer(from_game="firered", to_game="leafgreen"),
                EventPokemon(game="firered", pokemon="mew"),
                GameStarter(game="firered", pokemon="ivysaur"),  # its line's last stage here
            ]
        )
        session.commit()
    engine.dispose()


def _encounter(game: str, location: str, pokemon: str, method: str, rarity: int = 100) -> Encounter:
    return Encounter(
        game=game,
        location=location,
        pokemon=pokemon,
        method=method,
        conditions=[],
        rarity=rarity,
        min_level=5,
        max_level=5,
    )


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    _pokedex_data(reference_database(data_dir, pokemon=POKEMON))
    return make_client()


def _complete(client: TestClient, game: str = "firered", day: str = "2026-09-01") -> int:
    body = {"game": game, "completed_on": day, "members": ["pikachu"]}
    response = client.post("/api/hall-of-fame", json=body)
    assert response.status_code == 201, response.json()
    entry: int = response.json()["id"]
    return entry


def _start(client: TestClient, *registered: str, game: str = "firered") -> dict[str, Any]:
    response = client.put(f"{POKEDEX}/{game}/initial", json={"registered": list(registered)})
    assert response.status_code == 200, response.json()
    body: dict[str, Any] = response.json()
    return body


def _card(client: TestClient, species: str, game: str = "firered") -> dict[str, Any]:
    response = client.get(f"{POKEDEX}/{game}/pokemon/{species}")
    assert response.status_code == 200, response.json()
    body: dict[str, Any] = response.json()
    return body


def _kinds(card: dict[str, Any]) -> list[tuple[str, str | None]]:
    return [(m["kind"], m["game"] or m["pokemon"]) for m in card["methods"]]


def test_only_the_completed_games_have_a_pokedex(client: TestClient) -> None:
    """RF-20: one per game in the Hall of Fame, not started until its initial list."""
    assert client.get(POKEDEX).json() == []
    entry = _complete(client)
    assert client.get(POKEDEX).json() == [
        {
            "game": "firered",
            "game_name": "Firered",
            "cover_url": None,
            "hall_of_fame_entry": entry,
            "progress": {
                "registered": 0,
                "total": 7,
                "impossible": 1,  # Jirachi, only from a spin-off
                "percent": 0,
                "status": "not_started",
            },
        }
    ]
    assert client.get(f"{POKEDEX}/leafgreen").status_code == 404


@pytest.mark.rn("RN-22")
def test_the_initial_list_starts_the_pokedex(client: TestClient) -> None:
    """RF-21: the list in the Pokédex order, with what the user already has; only once."""
    _complete(client)
    listed = client.get(f"{POKEDEX}/firered").json()
    assert [s["species"] for s in listed["species"]][:3] == ["bulbasaur", "ivysaur", "pikachu"]
    first = listed["species"][0]
    assert {k: first[k] for k in ("number", "name", "pokemon", "types", "status")} == {
        "number": 1,
        "name": "Bulbasaur",
        "pokemon": "bulbasaur",
        "types": ["grass", "poison"],
        "status": None,
    }
    started = _start(client, "pikachu", "sandshrew")
    assert started["progress"] == {
        "registered": 2,
        "total": 7,
        "impossible": 1,
        "percent": 28,
        "status": "in_progress",
    }
    again = client.put(f"{POKEDEX}/firered/initial", json={"registered": []})
    assert again.status_code == 409
    jirachi = next(s for s in started["species"] if s["species"] == "jirachi")
    assert jirachi["automatically_impossible"] is True


def test_the_initial_list_only_takes_species_of_the_pokedex(client: TestClient) -> None:
    _complete(client)
    response = client.put(f"{POKEDEX}/firered/initial", json={"registered": ["missingno"]})
    assert response.status_code == 422
    assert "missingno" in response.json()["detail"]


@pytest.mark.rn("RN-23")
def test_the_objective_and_skipping_it(client: TestClient) -> None:
    """DDF: with Bulbasaur registered, Ivysaur, evolving Bulbasaur; skipped, Pikachu; skipping
    is not kept (CA-77)."""
    _complete(client)
    _start(client, "bulbasaur")
    objective = client.get(f"{POKEDEX}/firered/objective").json()["pokemon"]
    assert objective["species"] == "ivysaur"
    [evolve] = objective["methods"]
    assert {k: evolve[k] for k in ("kind", "pokemon", "pokemon_registered", "recommended")} == {
        "kind": "evolve",
        "pokemon": "bulbasaur",
        "pokemon_registered": True,
        "recommended": True,
    }
    assert evolve["evolution"] == {"trigger": "level-up", "conditions": {"minimum_level": 16}}
    skipped = client.get(f"{POKEDEX}/firered/objective", params={"skipped": "ivysaur"}).json()
    assert skipped["pokemon"]["species"] == "pikachu"
    assert client.get(f"{POKEDEX}/firered/objective").json()["pokemon"]["species"] == "ivysaur"


@pytest.mark.rn("RN-23")
def test_no_objective_when_nothing_is_left(client: TestClient) -> None:
    _complete(client)
    _start(client, *(f.species for f in POKEMON if f.species != "jirachi"))
    assert client.get(f"{POKEDEX}/firered/objective").json() == {"pokemon": None}


@pytest.mark.rn("RN-24")
@pytest.mark.rn("RN-26")
def test_the_ways_of_each_pokemon(client: TestClient) -> None:
    """The starter is a gift that depends on the starter (CA-87); Pichu, bred from a wild
    Pikachu (form 4); Mew, an event."""
    _complete(client)
    bulbasaur = _card(client, "bulbasaur")
    [gift] = bulbasaur["methods"]
    assert gift["kind"] == "starter_gift"
    assert {k: gift["way"][k] for k in ("location", "location_name", "choice", "rarity")} == {
        "location": "pallet-town",
        "location_name": "Pueblo Paleta",
        "choice": "starter-bulbasaur",
        "rarity": 100,
    }
    assert _kinds(_card(client, "pichu")) == [("breed", "pikachu")]
    assert _kinds(_card(client, "mew")) == [("event", None)]


@pytest.mark.rn("RN-25")
def test_transfers_from_the_other_game(client: TestClient) -> None:
    """Sandshrew, exclusive to LeafGreen: transferred from it (form 5) and, with LeafGreen
    completed and Sandshrew registered there, from its Pokédex (form 2)."""
    _complete(client)
    [transfer] = _card(client, "sandshrew")["methods"]
    assert (transfer["kind"], transfer["game"], transfer["game_name"]) == (
        "transfer",
        "leafgreen",
        "Leafgreen",
    )
    assert transfer["way"]["location_name"] == "Route 4"  # no Spanish name: the English one
    _complete(client, "leafgreen", "2026-09-02")
    _start(client, "sandshrew", game="leafgreen")
    assert _kinds(_card(client, "sandshrew")) == [("transfer_registered", "leafgreen")]


def test_marks_need_the_initial_list(client: TestClient) -> None:
    _complete(client)
    response = client.put(f"{POKEDEX}/firered/pokemon/mew", json={"status": "impossible"})
    assert response.status_code == 409
    assert client.delete(f"{POKEDEX}/firered/pokemon/mew").status_code == 409


@pytest.mark.rn("RN-22")
def test_mark_choose_and_unmark(client: TestClient) -> None:
    """RF-22 to RF-24: impossible counts apart; a chosen way is kept and marked; unmarking
    removes both."""
    _complete(client)
    _start(client)
    impossible = client.put(f"{POKEDEX}/firered/pokemon/mew", json={"status": "impossible"})
    assert impossible.json()["status"] == "impossible"
    assert client.get(POKEDEX).json()[0]["progress"]["impossible"] == 2
    key = _card(client, "mew")["methods"][0]["key"]
    chosen = client.put(f"{POKEDEX}/firered/pokemon/mew", json={"chosen_method": key}).json()
    assert (chosen["status"], chosen["chosen_method"]) == ("impossible", key)
    assert chosen["methods"][0]["chosen"] is True
    wrong = client.put(f"{POKEDEX}/firered/pokemon/mew", json={"chosen_method": "breed:x"})
    assert wrong.status_code == 422
    assert client.put(f"{POKEDEX}/firered/pokemon/mew", json={}).status_code == 422
    assert client.delete(f"{POKEDEX}/firered/pokemon/mew").status_code == 204
    after = _card(client, "mew")
    assert (after["status"], after["chosen_method"]) == (None, None)


def test_unknown_species_is_not_found(client: TestClient) -> None:
    _complete(client)
    assert client.get(f"{POKEDEX}/firered/pokemon/missingno").status_code == 404


def test_removing_or_changing_the_game_of_the_entry_removes_its_pokedex(
    client: TestClient,
) -> None:
    """CA-68: the Pokédex belongs to its Hall of Fame entry."""
    entry = _complete(client)
    _start(client, "pikachu")
    client.patch(f"/api/hall-of-fame/{entry}", json={"game": "leafgreen"})
    assert client.get(f"{POKEDEX}/leafgreen").json()["progress"]["status"] == "not_started"
    _start(client, "pikachu", game="leafgreen")
    client.delete(f"/api/hall-of-fame/{entry}")
    assert client.get(POKEDEX).json() == []
    _complete(client, "leafgreen")
    assert client.get(f"{POKEDEX}/leafgreen").json()["progress"]["registered"] == 0
