"""Covers of the games and WikiDex sources: GET /api/games/{game}/cover, ``cover_url`` and
``cover_source_url``, and ``source_url`` of the key battles (RF-18, ADR-0011, ADR-0004).

The covers belong to their owners and are never versioned (ADR-0011): these tests use a minimal
PNG built in ``tests/ingest/test_sprites.py``.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from db.reference import Origin
from db.sqlite import create_sqlite_engine
from tests.api.conftest import ClientFactory
from tests.api.factories import GameRow, form, reference_database
from tests.api.scenario import Load, write_firered
from tests.ingest.test_sprites import PNG

COVERS = "cache/wikidex/covers"
FIRERED_SOURCE = "https://www.wikidex.net/wiki/Archivo:Car%C3%A1tula_de_Rojo_Fuego.png"


def _cover(data_dir: Path, game: str) -> str:
    """Writes the reduced cover of ``game`` in the cache of ``data_dir``; its relative path."""
    relative = f"{COVERS}/{game}-256.png"
    path = data_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG)
    return relative


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    """FireRed and Red (not a target) with cover, LeafGreen without."""
    reference_database(
        data_dir,
        pokemon=[form("vulpix", ("fire",), dex=37, past={1: ("fire",)})],
        games=[
            GameRow(
                "red",
                generation=1,
                version_group="red-blue",
                is_target=False,
                has_breeding=False,
                cover=_cover(data_dir, "red"),
                cover_source="Archivo:Carátula de Pokémon Rojo.jpg",
            ),
            GameRow(
                "firered",
                release_order=10,
                cover=_cover(data_dir, "firered"),
                cover_source="Archivo:Carátula de Rojo Fuego.png",
            ),
            GameRow("leafgreen", release_order=11),
        ],
    )
    return make_client()


# --- The cover ---------------------------------------------------------------------------------


@pytest.mark.parametrize("game", ["firered", "red"], ids=["target", "not-a-target"])
def test_the_cover_is_served_from_the_data_directory(client: TestClient, game: str) -> None:
    """Any loaded game has its cover, also those that are not a target (Hall of Fame)."""
    response = client.get(f"/api/games/{game}/cover")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "public, max-age=86400"
    assert response.content == PNG


@pytest.mark.parametrize("game", ["leafgreen", "stadium"], ids=["without-cover", "unknown"])
def test_no_cover_is_a_404(client: TestClient, game: str) -> None:
    assert client.get(f"/api/games/{game}/cover").status_code == 404


def test_a_cover_missing_on_disk_is_a_404(client: TestClient, data_dir: Path) -> None:
    """The cache was deleted after the load: the game is shown without cover, no error."""
    (data_dir / COVERS / "firered-256.png").unlink()
    assert client.get("/api/games/firered/cover").status_code == 404


def test_a_cover_outside_the_data_directory_is_not_served(
    make_client: ClientFactory, data_dir: Path, tmp_path: Path
) -> None:
    secret = tmp_path / "secret.png"
    secret.write_bytes(PNG)
    reference_database(data_dir, games=[GameRow("firered", cover="../secret.png")])

    assert make_client().get("/api/games/firered/cover").status_code == 404


# --- cover_url and cover_source_url in the responses -------------------------------------------


def test_the_games_give_their_cover_and_its_source(client: TestClient) -> None:
    games = client.get("/api/games", params={"all": "true"}).json()
    covers = {g["game"]: (g["cover_url"], g["cover_source_url"]) for g in games}

    assert covers == {
        "red": (
            "/api/games/red/cover",
            "https://www.wikidex.net/wiki/Archivo:Car%C3%A1tula_de_Pok%C3%A9mon_Rojo.jpg",
        ),
        "firered": ("/api/games/firered/cover", FIRERED_SOURCE),
        "leafgreen": (None, None),
    }


def test_the_hall_of_fame_gives_the_cover_of_each_game(client: TestClient) -> None:
    for game in ("red", "leafgreen"):
        body = {"game": game, "completed_on": "2026-05-01", "members": ["vulpix"]}
        assert client.post("/api/hall-of-fame", json=body).status_code == 201
    entries = client.get("/api/hall-of-fame").json()

    assert [(e["game"], e["cover_url"], e["cover_source_url"] is not None) for e in entries] == [
        ("red", "/api/games/red/cover", True),
        ("leafgreen", None, False),
    ]


def test_a_hall_of_fame_game_no_longer_loaded_has_no_cover(
    client: TestClient, make_client: ClientFactory, data_dir: Path
) -> None:
    body = {"game": "red", "completed_on": "2026-05-01", "members": ["vulpix"]}
    client.post("/api/hall-of-fame", json=body)
    (data_dir / "reference.sqlite").unlink()
    reference_database(data_dir, pokemon=[form("vulpix", ("fire",), dex=37)])

    [entry] = make_client().get("/api/hall-of-fame").json()

    assert (entry["game_name"], entry["cover_url"], entry["cover_source_url"]) == (
        "red",
        None,
        None,
    )


# --- source_url of the key battles -------------------------------------------------------------


@pytest.mark.rn("RN-18")
def test_the_review_links_each_key_battle_to_its_wikidex_revision(
    make_client: ClientFactory, data_dir: Path
) -> None:
    """RN-18: the review shows where an unverified key battle team comes from (ADR-0004)."""
    write_firered(
        data_dir,
        load=Load(
            battle_origins={"firered-misty": Origin.INFERRED, "firered-brock": Origin.INFERRED}
        ),
    )
    engine = create_sqlite_engine(data_dir / "reference.sqlite")
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE key_battle SET source_page = 'Misty', source_revision = 3508255 "
                "WHERE slug = 'firered-misty'"
            )
        )
    engine.dispose()
    client = make_client()
    client.put("/api/favorites/vulpix")

    facts = {f["fact_key"]: f for f in client.get("/api/games/firered/review").json()["facts"]}

    assert facts["battle:firered:misty"]["source_url"] == (
        "https://www.wikidex.net/index.php?title=Misty&oldid=3508255"
    )
    assert facts["battle:firered:brock"]["source_url"] is None
    assert all(f["source_url"] is None for f in facts.values() if f["kind"] != "key_battle")
