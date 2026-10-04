"""Shared test configuration.

Tests never use the network (docs/02-ddt/arquitectura.md, "Estrategia de pruebas"): any HTTP
request made through httpx's network transports fails, so a test that would download data
breaks loudly instead of silently depending on an external service. FastAPI's ``TestClient``
still works: it talks to the application in memory, through its own transport.
"""

from typing import NoReturn

import httpx
import httpx2
import pytest


class NetworkAccessError(RuntimeError):
    """A test tried to use the network."""


def _blocked(*args: object, **kwargs: object) -> NoReturn:
    raise NetworkAccessError("los tests no pueden usar la red")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", _blocked)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", _blocked)
    # httpx2 is what FastAPI's TestClient uses; its in-memory transport is not blocked.
    monkeypatch.setattr(httpx2.HTTPTransport, "handle_request", _blocked)
    monkeypatch.setattr(httpx2.AsyncHTTPTransport, "handle_async_request", _blocked)
