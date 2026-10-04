"""The tests cannot use the network (tests/conftest.py), with any httpx entry point."""

import asyncio

import httpx
import httpx2
import pytest


def test_httpx_get_is_blocked() -> None:
    with pytest.raises(RuntimeError, match="no pueden usar la red"):
        httpx.get("https://pokeapi.co")


def test_httpx_client_is_blocked() -> None:
    with pytest.raises(RuntimeError, match="no pueden usar la red"), httpx.Client() as client:
        client.get("https://www.wikidex.net")


async def _fetch() -> None:
    async with httpx.AsyncClient() as client:
        await client.get("https://pokeapi.co")


def test_httpx_async_client_is_blocked() -> None:
    with pytest.raises(RuntimeError, match="no pueden usar la red"):
        asyncio.run(_fetch())


def test_httpx2_is_blocked() -> None:
    with pytest.raises(RuntimeError, match="no pueden usar la red"):
        httpx2.get("https://pokeapi.co")
