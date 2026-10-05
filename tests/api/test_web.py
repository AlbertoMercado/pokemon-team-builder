"""The compiled web served by the API at ``/`` (``api.web``): one process for both."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.config import DATA_DIR_VARIABLE, WEB_DIR_VARIABLE, Settings
from api.main import create_app

INDEX = "<!doctype html><title>pokemon-team-builder</title>"


@pytest.fixture
def web_dir(tmp_path: Path) -> Path:
    """A build of the web like ``npm run build`` writes it."""
    web = tmp_path / "dist"
    (web / "assets").mkdir(parents=True)
    (web / "index.html").write_text(INDEX, encoding="utf-8")
    (web / "assets" / "index-abc123.js").write_text("console.log(1)", encoding="utf-8")
    return web


@pytest.fixture
def client(tmp_path: Path, web_dir: Path) -> TestClient:
    return TestClient(create_app(Settings(tmp_path / "data", web_dir)))


def test_the_web_is_served_at_the_root(client: TestClient) -> None:
    with client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == INDEX
        asset = client.get("/assets/index-abc123.js")
        assert asset.status_code == 200
        assert asset.text == "console.log(1)"


@pytest.mark.parametrize("path", ["/pokemon/vulpix", "/juego/firered/resultado", "/favoritos"])
def test_the_routes_of_the_web_get_its_index(client: TestClient, path: str) -> None:
    """Reloading or linking a screen of the web opens the web, which shows that screen."""
    with client:
        response = client.get(path)
        assert response.status_code == 200
        assert response.text == INDEX


def test_the_web_does_not_cover_the_api(client: TestClient) -> None:
    with client:
        assert client.get("/api/openapi.json").json()["info"]["title"] == "pokemon-team-builder"
        # No reference data in this directory: the API's own answer, not the web.
        assert client.get("/api/meta").status_code == 503
        unknown = client.get("/api/nothing-here")
        assert unknown.status_code == 404
        assert unknown.json() == {"detail": "Not Found"}
        assert (
            client.get("/api/games/firered/nothing")
            .headers["content-type"]
            .startswith("application/json")
        )


def test_without_a_build_only_the_api_is_served(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(tmp_path / "data", tmp_path / "missing"))) as client:
        assert client.get("/").status_code == 404
        assert client.get("/api/openapi.json").status_code == 200


def test_the_web_directory_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DATA_DIR_VARIABLE, raising=False)
    monkeypatch.delenv(WEB_DIR_VARIABLE, raising=False)
    assert Settings.from_environment().web_dir == Path("web/dist")
    monkeypatch.setenv(WEB_DIR_VARIABLE, "/tmp/otra-web")
    assert Settings.from_environment().web_dir == Path("/tmp/otra-web")
