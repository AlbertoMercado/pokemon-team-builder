"""Images of the forms: GET /api/pokemon/{pokemon}/image and ``image_url`` (RF-17, ADR-0010).

The images belong to their owners and are never versioned (CA-56): these tests use a minimal
PNG built in ``tests/ingest/test_sprites.py``.
"""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from db.sqlite import create_sqlite_engine
from tests.api.conftest import ClientFactory
from tests.api.factories import form, reference_database
from tests.api.scenario import write_firered
from tests.core.scenario import FAVORITES
from tests.ingest.test_sprites import PNG

SPRITES = "cache/pokeapi-sprites/8491ffde1b247e4de574d4bb8e24b7bd9fa876fa"


def _sprite(data_dir: Path, name: str) -> str:
    """Writes a sprite in the cache of ``data_dir`` and returns its relative path."""
    relative = f"{SPRITES}/{name}"
    path = data_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG)
    return relative


@pytest.fixture
def client(make_client: ClientFactory, data_dir: Path) -> TestClient:
    """Vulpix with its sprite, Alolan Vulpix with its own and Gengar without one."""
    reference_database(
        data_dir,
        pokemon=[
            form("vulpix", ("fire",), dex=37, image=_sprite(data_dir, "37.png")),
            form(
                "vulpix-alola",
                ("ice",),
                dex=37,
                species="vulpix",
                region="alola",
                image=_sprite(data_dir, "10103.png"),
            ),
            form("gengar", ("ghost", "poison"), dex=94),
        ],
        sprites_commit="8491ffd",
    )
    return make_client()


# --- The image ---------------------------------------------------------------------------------


def test_the_image_is_served_from_the_data_directory(client: TestClient) -> None:
    response = client.get("/api/pokemon/vulpix-alola/image")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "public, max-age=86400"
    assert response.content == PNG


@pytest.mark.parametrize("pokemon", ["gengar", "missingno"], ids=["without-image", "unknown"])
def test_no_image_is_a_404(client: TestClient, pokemon: str) -> None:
    assert client.get(f"/api/pokemon/{pokemon}/image").status_code == 404


def test_an_image_missing_on_disk_is_a_404(client: TestClient, data_dir: Path) -> None:
    """The cache was deleted after the load: the form is shown without image, no error."""
    (data_dir / SPRITES / "37.png").unlink()
    assert client.get("/api/pokemon/vulpix/image").status_code == 404


def test_a_path_outside_the_data_directory_is_not_served(
    make_client: ClientFactory, data_dir: Path, tmp_path: Path
) -> None:
    secret = tmp_path / "secret.png"
    secret.write_bytes(PNG)
    reference_database(data_dir, pokemon=[form("vulpix", ("fire",), dex=37, image="../secret.png")])

    assert make_client().get("/api/pokemon/vulpix/image").status_code == 404


# --- image_url in the responses ----------------------------------------------------------------


def test_the_catalogue_gives_the_image_of_each_form(client: TestClient) -> None:
    """RN-05: each form has its own image, Vulpix and Alolan Vulpix are told apart."""
    body = client.get("/api/pokemon").json()
    images = {p["pokemon"]: p["image_url"] for p in body["pokemon"]}

    assert images == {
        "vulpix": "/api/pokemon/vulpix/image",
        "vulpix-alola": "/api/pokemon/vulpix-alola/image",
        "gengar": None,
    }


def test_the_detail_and_its_line_give_their_images(client: TestClient) -> None:
    detail = client.get("/api/pokemon/vulpix").json()

    assert detail["image_url"] == "/api/pokemon/vulpix/image"
    assert {m["pokemon"]: m["image_url"] for m in detail["line"]}["vulpix-alola"] == (
        "/api/pokemon/vulpix-alola/image"
    )


def test_favourites_give_their_images(client: TestClient) -> None:
    added = client.put("/api/favorites/vulpix-alola").json()
    client.put("/api/favorites/gengar")
    favorites = client.get("/api/favorites").json()["favorites"]

    assert added["image_url"] == "/api/pokemon/vulpix-alola/image"
    assert {f["pokemon"]: f["image_url"] for f in favorites} == {
        "vulpix-alola": "/api/pokemon/vulpix-alola/image",
        "gengar": None,
    }


def test_the_hall_of_fame_gives_the_images_of_the_team(client: TestClient) -> None:
    body = {"game": "firered", "completed_on": "2026-05-01", "members": ["vulpix", "gengar"]}
    entry = client.post("/api/hall-of-fame", json=body).json()

    assert [m["image_url"] for m in entry["members"]] == ["/api/pokemon/vulpix/image", None]


def test_meta_gives_the_commit_of_the_images(client: TestClient) -> None:
    assert client.get("/api/meta").json()["data"]["sprites_commit"] == "8491ffd"


def test_the_generation_gives_the_images_of_positions_and_suggestions(
    make_client: ClientFactory, data_dir: Path
) -> None:
    """Every form of the real FireRed scenario has an image except Lapras."""
    write_firered(data_dir)
    engine = create_sqlite_engine(data_dir / "reference.sqlite")
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE pokemon SET image = 'cache/' || slug || '.png' WHERE slug != 'lapras'")
        )
    engine.dispose()
    client = make_client()
    for slug in FAVORITES:
        client.put(f"/api/favorites/{slug}")
    client.post("/api/games/firered/review/accept-proposals")

    body: dict[str, Any] = client.post("/api/games/firered/generations").json()

    shown = [p for group in body["groups"] for position in group["positions"] for p in position]
    shown += [
        s["pokemon"]
        for group in body["groups"]
        for team in group["teams"]
        for slot in team["open_slots"]
        for s in slot["suggestions"]
    ]
    assert shown
    for pokemon in shown:
        expected = (
            None if pokemon["pokemon"] == "lapras" else f"/api/pokemon/{pokemon['pokemon']}/image"
        )
        assert pokemon["image_url"] == expected
    assert any(p["pokemon"] == "lapras" for p in shown)
