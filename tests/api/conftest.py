"""Fixtures of the API tests: an application over a temporary data directory."""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.config import Settings
from api.main import create_app

type ClientFactory = Callable[[], TestClient]


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def make_client(data_dir: Path) -> Iterator[ClientFactory]:
    """Starts the application on ``data_dir``; prepare the data before calling it."""
    clients: list[TestClient] = []

    def make() -> TestClient:
        client = TestClient(create_app(Settings(data_dir)))
        client.__enter__()  # runs the lifespan: migrations of user.sqlite
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.__exit__(None, None, None)
