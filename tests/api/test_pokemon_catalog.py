"""/api/pokemon: list, search and detail of the Pokémon (RF-01, RF-02, RN-05)."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from db.reference import EvolutionStep, VersionGroup
from db.sqlite import create_sqlite_engine
from tests.api.conftest import ClientFactory
from tests.api.factories import Form, form, reference_database
from tests.api.scenario import write_firered

CATALOG = "/api/pokemon"


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    write_firered(data_dir)
    return make_client()


def _names(client: TestClient, **params: str) -> list[str]:
    return [p["pokemon"] for p in client.get(CATALOG, params=params).json()["pokemon"]]


def _detail(client: TestClient, pokemon: str) -> dict[str, Any]:
    response = client.get(f"{CATALOG}/{pokemon}")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def test_every_form_in_pokedex_order(client: TestClient) -> None:
    """RF-01: number, name and types of each one."""
    body = client.get(CATALOG).json()
    assert body["total"] == len(body["pokemon"]) == 145
    assert body["pokemon"][0] == {
        "pokemon": "bulbasaur",
        "name": "Bulbasaur",
        "dex_number": 1,
        "types": ["grass", "poison"],
        "region": None,
        "favorite": False,
        "image_url": None,
    }
    numbers = [p["dex_number"] for p in body["pokemon"]]
    assert numbers == sorted(numbers)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("dragon", ["dragonair", "dragonite"]),
        ("DRAGON", ["dragonair", "dragonite"]),
        ("mr mime", ["mr-mime"]),  # by identifier, with a space for the hyphen
        ("gastly", ["gastly"]),
    ],
)
def test_search_by_name(client: TestClient, query: str, expected: list[str]) -> None:
    assert _names(client, q=query) == expected


def test_search_ignores_accents(make_client: ClientFactory, data_dir: Path) -> None:
    flabebe = Form("flabebe", 669, {3: ("grass",)}, name="Flabébé", species="flabebe")
    reference_database(data_dir, pokemon=[flabebe])
    client = make_client()
    assert _names(client, q="flabebe") == ["flabebe"]  # by name, without accents
    assert _names(client, q="FLABÉBÉ") == ["flabebe"]


def test_filter_by_current_type(client: TestClient) -> None:
    assert _names(client, type="dragon") == ["dratini", "dragonair", "dragonite"]
    assert _names(client, type="shadow") == []


def test_favourites_are_marked_and_can_be_filtered(client: TestClient) -> None:
    client.put("/api/favorites/dragonite")
    assert _names(client, favorite="true") == ["dragonite"]
    assert "dragonite" not in _names(client, favorite="false")
    assert client.get(CATALOG, params={"q": "dragonite"}).json()["pokemon"][0]["favorite"]


@pytest.mark.rn("RN-05")
def test_regional_forms_are_entries_of_their_own(
    make_client: ClientFactory, data_dir: Path
) -> None:
    """RF-01: «Vulpix» and «Vulpix de Alola» are different and clearly identified."""
    reference_database(
        data_dir,
        pokemon=[
            form("vulpix", ("fire",), dex=37),
            form("vulpix-alola", ("ice",), dex=37, species="vulpix", region="alola"),
        ],
    )
    body = make_client().get(CATALOG, params={"q": "vulpix"}).json()["pokemon"]
    assert [(p["pokemon"], p["types"], p["region"]) for p in body] == [
        ("vulpix", ["fire"], None),
        ("vulpix-alola", ["ice"], "alola"),
    ]


@pytest.mark.rn("RN-10")
def test_types_are_the_current_ones(make_client: ClientFactory, data_dir: Path) -> None:
    """RF-02: Magneton is Electric/Steel now, although it was only Electric in the 1st."""
    reference_database(
        data_dir, pokemon=[form("magneton", ("electric", "steel"), dex=82, past={1: ("electric",)})]
    )
    client = make_client()
    assert client.get(CATALOG).json()["pokemon"][0]["types"] == ["electric", "steel"]
    assert _detail(client, "magneton")["types"] == ["electric", "steel"]


@pytest.mark.rn("RN-09")
def test_detail_with_the_whole_line_and_how_it_evolves(client: TestClient) -> None:
    """RF-02: the favourite is the evolution to reach; the detail shows the line it needs."""
    client.put("/api/favorites/gengar")
    body = _detail(client, "haunter")
    assert (body["pokemon"], body["name"], body["dex_number"], body["types"]) == (
        "haunter",
        "Haunter",
        93,
        ["ghost", "poison"],
    )
    assert (body["species"], body["generation"], body["favorite"]) == ("haunter", 1, False)
    assert [(m["pokemon"], m["stage"], m["favorite"]) for m in body["line"]] == [
        ("gastly", 1, False),
        ("haunter", 2, False),
        ("gengar", 3, True),
    ]
    assert [(e["from_pokemon"], e["to_pokemon"], e["methods"]) for e in body["evolutions"]] == [
        ("gastly", "haunter", [{"trigger": "level-up", "conditions": {"minimum_level": 25}}]),
        ("haunter", "gengar", [{"trigger": "trade", "conditions": {}}]),
    ]
    assert {e["version_group"] for e in body["evolutions"]} == {"firered-leafgreen"}


def test_a_branched_line_has_every_branch(client: TestClient) -> None:
    body = _detail(client, "eevee")
    assert [m["pokemon"] for m in body["line"]] == ["eevee", "vaporeon", "jolteon", "flareon"]
    assert [e["to_pokemon"] for e in body["evolutions"]] == ["vaporeon", "jolteon", "flareon"]
    assert body["evolutions"][0]["methods"] == [
        {"trigger": "use-item", "conditions": {"trigger_item": "water-stone"}}
    ]


def test_a_pokemon_that_does_not_evolve(client: TestClient) -> None:
    body = _detail(client, "lapras")
    assert ([m["pokemon"] for m in body["line"]], body["evolutions"]) == (["lapras"], [])


def test_the_method_is_that_of_the_latest_version_group(
    make_client: ClientFactory, data_dir: Path
) -> None:
    """An evolution's method can change between games: the latest loaded one is shown."""
    write_firered(data_dir)
    engine = create_sqlite_engine(data_dir / "reference.sqlite")
    with Session(engine) as session:
        session.add(VersionGroup(slug="red-blue", generation=1, order=1))
        session.flush()
        session.add(
            EvolutionStep(
                version_group="red-blue",
                from_pokemon="gastly",
                to_pokemon="haunter",
                trigger="level-up",
                conditions={"minimum_level": 30},
            )
        )
        session.commit()
    engine.dispose()
    [first, _] = _detail(make_client(), "gengar")["evolutions"]
    assert (first["version_group"], first["methods"][0]["conditions"]) == (
        "firered-leafgreen",
        {"minimum_level": 25},
    )


def test_an_unknown_form_is_not_found(client: TestClient) -> None:
    assert client.get(f"{CATALOG}/missingno").status_code == 404


def test_without_reference_data_the_catalogue_is_unavailable(make_client: ClientFactory) -> None:
    assert make_client().get(CATALOG).status_code == 503
