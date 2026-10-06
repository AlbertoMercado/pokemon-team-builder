"""Images of the forms: cache, download, trimming, artwork, missing images and the load
(ADR-0010).

The images belong to their owners and are never versioned (CA-56), so these tests build their
PNG files here: a transparent canvas with an opaque rectangle, like the figure of a sprite.
"""

import io
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
from PIL import Image
from sqlmodel import Session, select

from db.reference import IngestRun, Pokemon, ReferenceModel
from db.sqlite import create_sqlite_engine
from ingest.load import Images, build_reference
from ingest.sources.pokeapi.sprites import (
    ARTWORK_SIZE,
    MissingReason,
    MissingSpriteError,
    SpriteCache,
    reduced,
    trimmed,
)
from tests.ingest.test_load import FakeSource, _firered_rows

COMMIT = "8491ffde1b247e4de574d4bb8e24b7bd9fa876fa"
REPOSITORY = Path(__file__).resolve().parents[2]
CACHE = f"cache/pokeapi-sprites/{COMMIT}"
RAW = f"https://raw.githubusercontent.com/PokeAPI/sprites/{COMMIT}/sprites/pokemon"


def png(size: int = 96, figure: tuple[int, int, int, int] | None = (30, 20, 70, 70)) -> bytes:
    """A transparent ``size`` x ``size`` PNG with an opaque rectangle at ``figure`` (a box)."""
    image = Image.new("RGBA", (size, size))
    if figure is not None:
        image.paste((200, 50, 50, 255), figure)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def size_of(content: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(content)) as image:
        return image.size


PNG = png()
ARTWORK = png(475, (40, 20, 435, 455))


def _status_error(url: str, status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", url)
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"{status}", request=request, response=response)


@dataclass
class FakeDownloader:
    """Serves ``files`` by their path in ``sprites/pokemon`` (``37.png``,
    ``other/official-artwork/37.png``); anything else is a 404, unless ``error`` is set."""

    files: dict[str, bytes]
    error: Exception | None = None

    def __post_init__(self) -> None:
        self.requested: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.requested.append(url)
        if self.error is not None:
            raise self.error
        path = url.removeprefix(f"{RAW}/")
        if path not in self.files:
            raise _status_error(url, 404)
        return self.files[path]


def _both(*sprite_ids: int) -> dict[str, bytes]:
    """The sprite and the artwork of each form."""
    files = {f"{i}.png": PNG for i in sprite_ids}
    return files | {f"other/official-artwork/{i}.png": ARTWORK for i in sprite_ids}


def _cached(data_dir: Path, *sprite_ids: int) -> None:
    """Sprites as downloaded in a previous load, without their trimmed version or artwork."""
    directory = data_dir / CACHE
    directory.mkdir(parents=True)
    for sprite_id in sprite_ids:
        (directory / f"{sprite_id}.png").write_bytes(PNG)


def _reason(cache: SpriteCache, sprite_id: int) -> MissingReason:
    with pytest.raises(MissingSpriteError) as raised:
        cache.image(sprite_id)
    return raised.value.reason


# --- Processing --------------------------------------------------------------------------------


def test_trimming_keeps_only_the_figure() -> None:
    """The figure of a sprite fills about half of its canvas (CA-54): the lists show it alone."""
    assert size_of(trimmed(png(96, (30, 20, 70, 70)))) == (40, 50)


def test_trimming_an_empty_image_keeps_it() -> None:
    assert size_of(trimmed(png(96, None))) == (96, 96)


def test_the_artwork_is_reduced_keeping_its_proportions() -> None:
    assert size_of(reduced(png(475), ARTWORK_SIZE)) == (256, 256)
    assert size_of(reduced(png(64), ARTWORK_SIZE)) == (64, 64)  # never enlarged


# --- Cache and download ------------------------------------------------------------------------


def test_cached_sprite_is_trimmed_without_downloading(tmp_path: Path) -> None:
    _cached(tmp_path, 10103)
    downloader = FakeDownloader({})

    image = SpriteCache(tmp_path, COMMIT, downloader).image(10103)

    assert image == f"{CACHE}/trimmed/10103.png"
    assert size_of((tmp_path / image).read_bytes()) == (40, 50)
    assert downloader.requested == []


def test_sprite_is_downloaded_once_from_the_pinned_commit(tmp_path: Path) -> None:
    downloader = FakeDownloader({"37.png": PNG})
    cache = SpriteCache(tmp_path, COMMIT, downloader, sleep=lambda _: None)

    first = cache.image(37)
    second = cache.image(37)

    assert first == second == f"{CACHE}/trimmed/37.png"
    assert (tmp_path / CACHE / "37.png").read_bytes() == PNG  # the original stays in the cache
    assert downloader.requested == [f"{RAW}/37.png"]


def test_the_artwork_is_downloaded_once_and_reduced(tmp_path: Path) -> None:
    downloader = FakeDownloader(_both(37))
    cache = SpriteCache(tmp_path, COMMIT, downloader, sleep=lambda _: None)

    first = cache.artwork(37)
    second = cache.artwork(37)

    assert first == second == f"{CACHE}/official-artwork-{ARTWORK_SIZE}/37.png"
    assert size_of((tmp_path / first).read_bytes()) == (256, 256)
    assert downloader.requested == [f"{RAW}/other/official-artwork/37.png"]


def test_an_image_missing_in_the_repository_does_not_stop_the_others(tmp_path: Path) -> None:
    cache = SpriteCache(tmp_path, COMMIT, FakeDownloader({"25.png": PNG}), sleep=lambda _: None)

    assert _reason(cache, 99999) is MissingReason.NOT_FOUND
    assert cache.image(25).endswith("/25.png")


@pytest.mark.parametrize(
    "content", [b"404: Not Found", b"\x89PNG\r\n\x1a\nroto"], ids=["not-png", "broken-png"]
)
def test_a_download_that_is_not_a_valid_png_is_not_stored(tmp_path: Path, content: bytes) -> None:
    cache = SpriteCache(tmp_path, COMMIT, FakeDownloader({"25.png": content}))

    assert _reason(cache, 25) is MissingReason.NOT_PNG
    assert not (tmp_path / CACHE / "trimmed" / "25.png").exists()


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
    with pytest.raises(MissingSpriteError):
        cache.artwork(2)
    assert len(downloader.requested) == 1  # one failure, not one timeout per image


def test_offline_only_cached_images_are_used(tmp_path: Path) -> None:
    _cached(tmp_path, 1)
    cache = SpriteCache(tmp_path, COMMIT, downloader=None)

    assert cache.image(1).endswith("/trimmed/1.png")
    assert _reason(cache, 2) is MissingReason.UNAVAILABLE
    with pytest.raises(MissingSpriteError):
        cache.artwork(1)


def test_downloads_are_spaced(tmp_path: Path) -> None:
    now = [100.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    cache = SpriteCache(
        tmp_path, COMMIT, FakeDownloader(_both(1)), clock=lambda: now[0], sleep=sleep
    )
    cache.image(1)
    cache.artwork(1)

    assert slept == [pytest.approx(0.2)]


# --- Load --------------------------------------------------------------------------------------


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


def _images(target: Path) -> dict[str, tuple[str | None, str | None]]:
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        rows = session.exec(select(Pokemon.slug, Pokemon.image, Pokemon.artwork)).all()
    engine.dispose()
    return {slug: (image, artwork) for slug, image, artwork in rows}


def test_the_load_stores_the_images_of_each_form(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    sprites = SpriteCache(tmp_path, COMMIT, FakeDownloader(_both(1, 2)), sleep=lambda _: None)

    report = build_reference([_Forms()], target, images=Images(sprites=sprites))

    assert report.succeeded, report.errors
    assert (report.images, report.artworks) == ((2, 2), (2, 2))
    assert report.warnings == []
    assert "Imágenes: 2 de 2 formas" in report.render()
    assert "Ilustraciones: 2 de 2 formas" in report.render()
    artworks = f"{CACHE}/official-artwork-{ARTWORK_SIZE}"
    assert _images(target) == {
        "bulbasaur": (f"{CACHE}/trimmed/1.png", f"{artworks}/1.png"),
        "ivysaur": (f"{CACHE}/trimmed/2.png", f"{artworks}/2.png"),
    }
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        assert session.exec(select(IngestRun)).one().sprites_commit == COMMIT
    engine.dispose()


def test_forms_without_images_are_loaded_with_a_warning(tmp_path: Path) -> None:
    """Offline, with only Bulbasaur's sprite cached: no artwork at all, no sprite for Ivysaur."""
    _cached(tmp_path, 1)
    target = tmp_path / "reference.sqlite"

    report = build_reference(
        [_Forms()], target, images=Images(sprites=SpriteCache(tmp_path, COMMIT, downloader=None))
    )

    assert report.succeeded, report.errors
    assert (report.images, report.artworks) == ((1, 2), (0, 2))
    reason = "no está en la caché y no se ha podido descargar"
    assert report.warnings == [
        f"1 forma sin imagen, {reason}: ivysaur",
        f"2 formas sin ilustración, {reason}: bulbasaur, ivysaur",
    ]
    assert _images(target) == {
        "bulbasaur": (f"{CACHE}/trimmed/1.png", None),
        "ivysaur": (None, None),
    }


def test_a_load_without_sprites_has_no_images(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"

    report = build_reference([_Forms()], target)

    assert report.succeeded, report.errors
    assert report.images is None
    assert report.artworks is None
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        run = session.exec(select(IngestRun)).one()
    engine.dispose()
    assert run.sprites_commit is None


def test_the_sprite_cache_is_not_versioned() -> None:
    """CA-56: downloaded images never go to git."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", f"data/{CACHE}/trimmed/25.png"],
        cwd=REPOSITORY,
        check=False,
    )
    assert result.returncode == 0
