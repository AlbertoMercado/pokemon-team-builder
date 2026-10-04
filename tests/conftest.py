"""Shared test configuration.

Tests never use the network (docs/02-ddt/arquitectura.md, "Estrategia de pruebas"): any HTTP
request made through httpx fails, so a test that would download data breaks loudly instead
of silently depending on an external service.
"""

from typing import NoReturn

import httpx
import pytest


class NetworkAccessError(RuntimeError):
    """A test tried to use the network."""


def _blocked(*args: object, **kwargs: object) -> NoReturn:
    raise NetworkAccessError("los tests no pueden usar la red")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "get", _blocked)
    monkeypatch.setattr(httpx.Client, "send", _blocked)
