"""Sprites of the forms: cache, download, missing images and the load (ADR-0010).

The images belong to their owners and are never versioned (CA-56), so these tests use a
minimal PNG built here instead of real sprites.
"""

import struct
import subprocess
import zlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
from sqlmodel import Session, select

from db.reference import IngestRun, Pokemon, ReferenceModel
from db.sqlite import create_sqlite_engine
from ingest.load import build_reference
from ingest.sources.pokeapi.sprites import (
    MissingReason,
    MissingSpriteError,
    SpriteCache,
)
from tests.ingest.test_load import FakeSource, _firered_rows

COMMIT = "8491ffde1b247e4de574d4bb8e24b7bd9fa876fa"
REPOSITORY = Path(__file__).resolve().parents[2]


def _png() -> bytes:
    """A valid 1x1 transparent PNG."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)  # 1x1, 8 bits, RGBA
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
        + chunk(b"IEND", b"")
    )


PNG = _png()


def _status_error(url: str, status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", url)
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"{status}", request=request, response=response)


@dataclass
class FakeDownloader:
    """Serves ``files`` by sprite id; any other id is a 404, unless ``error`` is set."""

    files: dict[int, bytes]
    error: Exception | None = None

    def __post_init__(self) -> None:
        self.requested: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.requested.append(url)
        if self.error is not None:
            raise self.error
        sprite_id = int(url.rsplit("/", 1)[1].removesuffix(".png"))
        if sprite_id not in self.files:
            raise _status_error(url, 404)
        return self.files[sprite_id]


def _cached(data_dir: Path, *sprite_ids: int) -> None:
    directory = data_dir / "cache" / "pokeapi-sprites" / COMMIT
    directory.mkdir(parents=True)
    for sprite_id in sprite_ids:
        (directory / f"{sprite_id}.png").write_bytes(PNG)


def _reason(cache: SpriteCache, sprite_id: int) -> MissingReason:
    with pytest.raises(MissingSpriteError) as raised:
        cache.image(sprite_id)
    return raised.value.reason


# --- Cache and download ----------------------------------------------------------------------


def test_cached_sprite_is_used_without_downloading(tmp_path: Path) -> None:
    _cached(tmp_path, 10103)
    downloader = FakeDownloader({})

    image = SpriteCache(tmp_path, COMMIT, downloader).image(10103)

    assert image == f"cache/pokeapi-sprites/{COMMIT}/10103.png"
    assert downloader.requested == []


def test_sprite_is_downloaded_once_from_the_pinned_commit(tmp_path: Path) -> None:
    downloader = FakeDownloader({37: PNG})
    cache = SpriteCache(tmp_path, COMMIT, downloader, sleep=lambda _: None)

    first = cache.image(37)
    second = cache.image(37)

    assert first == second == f"cache/pokeapi-sprites/{COMMIT}/37.png"
    assert (tmp_path / first).read_bytes() == PNG
    assert downloader.requested == [
        f"https://raw.githubusercontent.com/PokeAPI/sprites/{COMMIT}/sprites/pokemon/37.png"
    ]


def test_a_sprite_missing_in_the_repository_does_not_stop_the_others(tmp_path: Path) -> None:
    cache = SpriteCache(tmp_path, COMMIT, FakeDownloader({25: PNG}), sleep=lambda _: None)

    assert _reason(cache, 99999) is MissingReason.NOT_FOUND
    assert cache.image(25).endswith("/25.png")


def test_a_download_that_is_not_a_png_is_not_stored(tmp_path: Path) -> None:
    cache = SpriteCache(tmp_path, COMMIT, FakeDownloader({25: b"404: Not Found"}))

    assert _reason(cache, 25) is MissingReason.NOT_PNG
    assert not (tmp_path / "cache" / "pokeapi-sprites" / COMMIT / "25.png").exists()


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("sin conexión"),
        httpx.ReadTimeout("tiempo agotado"),
        _status_error("https://raw.githubusercontent.com/", 503),
    ],
    ids=["connection", "timeout", "server-error"],
)
def test_a_failing_server_stops_the_downloads_of_the_load(tmp_path: Path, error: Exception) -> None:
    downloader = FakeDownloader({}, error=error)
    cache = SpriteCache(tmp_path, COMMIT, downloader, sleep=lambda _: None)

    assert _reason(cache, 1) is MissingReason.UNAVAILABLE
    assert _reason(cache, 2) is MissingReason.UNAVAILABLE
    assert len(downloader.requested) == 1  # one failure, not one timeout per form


def test_offline_only_cached_sprites_are_used(tmp_path: Path) -> None:
    _cached(tmp_path, 1)
    cache = SpriteCache(tmp_path, COMMIT, downloader=None)

    assert cache.image(1).endswith("/1.png")
    assert _reason(cache, 2) is MissingReason.UNAVAILABLE


def test_downloads_are_spaced(tmp_path: Path) -> None:
    now = [100.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    cache = SpriteCache(
        tmp_path, COMMIT, FakeDownloader({1: PNG, 2: PNG}), clock=lambda: now[0], sleep=sleep
    )
    cache.image(1)
    cache.image(2)

    assert slept == [pytest.approx(0.2)]


# --- Load ------------------------------------------------------------------------------------


@dataclass
class _Forms:
    """FireRed rows plus Bulbasaur, so that the load has two forms."""

    name: str = "forms"
    pokeapi_commit: str | None = None

    def rows(self) -> Iterable[ReferenceModel]:
        rows = FakeSource(_firered_rows()).rows()
        return [
            *rows,
            Pokemon(
                slug="bulbasaur",
                species="bulbasaur",
                name_es="Bulbasaur",
                is_default=True,
                pokeapi_id=1,
            ),
        ]


def test_the_load_stores_the_sprite_of_each_form(tmp_path: Path) -> None:
    _cached(tmp_path, 1, 2)
    target = tmp_path / "reference.sqlite"

    report = build_reference(
        [_Forms()], target, sprites=SpriteCache(tmp_path, COMMIT, downloader=None)
    )

    assert report.succeeded, report.errors
    assert report.images == (2, 2)
    assert report.warnings == []
    assert "Imágenes: 2 de 2 formas" in report.render()
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        images = dict(session.exec(select(Pokemon.slug, Pokemon.image)).all())
        run = session.exec(select(IngestRun)).one()
    engine.dispose()
    assert images == {
        "bulbasaur": f"cache/pokeapi-sprites/{COMMIT}/1.png",
        "ivysaur": f"cache/pokeapi-sprites/{COMMIT}/2.png",
    }
    assert run.sprites_commit == COMMIT


def test_forms_without_sprite_are_loaded_with_a_warning(tmp_path: Path) -> None:
    _cached(tmp_path, 1)
    target = tmp_path / "reference.sqlite"

    report = build_reference(
        [_Forms()], target, sprites=SpriteCache(tmp_path, COMMIT, downloader=None)
    )

    assert report.succeeded, report.errors
    assert report.images == (1, 2)
    assert report.warnings == [
        "1 forma sin imagen, no está en la caché y no se ha podido descargar: ivysaur"
    ]
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        image = session.exec(select(Pokemon.image).where(Pokemon.slug == "ivysaur")).one()
    engine.dispose()
    assert image is None


def test_a_load_without_sprites_has_no_images(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"

    report = build_reference([_Forms()], target)

    assert report.succeeded, report.errors
    assert report.images is None
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        run = session.exec(select(IngestRun)).one()
    engine.dispose()
    assert run.sprites_commit is None


def test_the_sprite_cache_is_not_versioned() -> None:
    """CA-56: downloaded images never go to git."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", f"data/cache/pokeapi-sprites/{COMMIT}/25.png"],
        cwd=REPOSITORY,
        check=False,
    )
    assert result.returncode == 0
