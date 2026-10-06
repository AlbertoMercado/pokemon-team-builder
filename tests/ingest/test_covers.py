"""Covers of the games from WikiDex: curated titles, information, cache, download and the load
(RF-18, ADR-0011).

The covers belong to their owners and are never versioned (CA-56): these tests build their
images here. The answer of the MediaWiki API is a real one, with metadata only.
"""

import hashlib
import io
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
from PIL import Image
from sqlmodel import Session, select

from db.reference import Game, ReferenceModel
from db.sqlite import create_sqlite_engine
from ingest import cli
from ingest.load import Images, build_reference
from ingest.sources.curated import CuratedDataError, read_covers
from ingest.sources.wikidex.covers import (
    COVER_SIZE,
    CoverCache,
    CoverFetchers,
    CoverInfo,
    CoverMissing,
    MissingCoverError,
    fetch_cover_info,
)
from tests.ingest.test_load import FakeSource, _firered_rows

REPOSITORY = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "wikidex"
COVERS = "cache/wikidex/covers"
FIRERED = "Archivo:Carátula de Rojo Fuego.png"
EMERALD = "Archivo:Caratula Esmeralda.jpg"


def jpeg(size: tuple[int, int] = (731, 739)) -> bytes:
    """A cover-like JPEG: an opaque image of ``size``."""
    output = io.BytesIO()
    Image.new("RGB", size, (200, 40, 40)).save(output, format="JPEG")
    return output.getvalue()


def size_of(content: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(content)) as image:
        return image.size


COVER = jpeg()


def _info(title: str, content: bytes = COVER) -> CoverInfo:
    name = title.removeprefix("Archivo:").replace(" ", "_")
    return CoverInfo(
        title=title,
        url=f"https://images.wikidexcdn.net/{name}",
        sha1=hashlib.sha1(content).hexdigest(),
    )


@dataclass
class FakeWikidex:
    """Information and files of the covers it knows; ``error`` makes every request fail and
    ``served`` replaces the content of every download."""

    files: dict[str, bytes]
    error: Exception | None = None
    served: bytes | None = None

    def __post_init__(self) -> None:
        self.info_requests: list[list[str]] = []
        self.downloads: list[str] = []

    def info(self, titles: Sequence[str]) -> dict[str, CoverInfo | None]:
        self.info_requests.append(list(titles))
        if self.error is not None:
            raise self.error
        return {t: _info(t, self.files[t]) if t in self.files else None for t in titles}

    def download(self, url: str) -> bytes:
        self.downloads.append(url)
        if self.error is not None:
            raise self.error
        if self.served is not None:
            return self.served
        for title, content in self.files.items():
            if url == _info(title, content).url:
                return content
        raise AssertionError(f"URL inesperada: {url}")

    def fetchers(self) -> CoverFetchers:
        return CoverFetchers(self.info, self.download)


def _cache(
    data_dir: Path,
    wikidex: FakeWikidex | None,
    titles: dict[str, str] | None = None,
    slept: list[float] | None = None,
) -> CoverCache:
    return CoverCache(
        data_dir,
        {"firered": FIRERED, "emerald": EMERALD} if titles is None else titles,
        None if wikidex is None else wikidex.fetchers(),
        sleep=(slept.append if slept is not None else lambda _: None),
    )


def _reason(cache: CoverCache, game: str) -> CoverMissing:
    with pytest.raises(MissingCoverError) as raised:
        cache.cover(game)
    return raised.value.reason


# --- Curated titles ----------------------------------------------------------------------------


def test_the_repository_curates_the_cover_of_every_loaded_game() -> None:
    covers = read_covers(REPOSITORY / "data" / "curated" / "covers.yaml").covers
    assert set(covers) == {
        "red", "blue", "yellow", "gold", "silver", "crystal",
        "ruby", "sapphire", "emerald", "firered", "leafgreen",
    }  # fmt: skip
    assert covers["firered"] == FIRERED


@pytest.mark.parametrize(
    "title", ["Carátula de Rojo Fuego.png", "Archivo:Rojo Fuego", "Archivo:Rojo|Fuego.png"]
)
def test_a_title_that_is_not_an_image_file_is_rejected(tmp_path: Path, title: str) -> None:
    path = tmp_path / "covers.yaml"
    path.write_text(f'covers:\n  firered: "{title}"\n', encoding="utf-8")
    with pytest.raises(CuratedDataError, match="firered"):
        read_covers(path)


# --- Information from the MediaWiki API ----------------------------------------------------------


def test_the_information_of_the_files_comes_from_one_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A real answer: two files, one missing and a title the API normalizes (File:)."""
    asked: list[dict[str, str]] = []

    def get(url: str, *, params: dict[str, str], **kwargs: object) -> httpx.Response:
        asked.append(params)
        content = (FIXTURES / "covers-imageinfo.json").read_bytes()
        return httpx.Response(200, content=content, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", get)
    titles = [
        FIRERED,
        EMERALD,
        "Archivo:Carátula que no existe.png",
        "File:Carátula de Verde Hoja.png",
    ]

    found = fetch_cover_info(titles)

    assert len(asked) == 1
    assert asked[0]["prop"] == "imageinfo"
    assert asked[0]["titles"] == "|".join(titles)
    emerald = found[EMERALD]
    assert emerald is not None
    assert emerald.sha1 == "4808309ec07c1aa85ecd44e645ec5a9b40a741c5"
    assert emerald.url.startswith("https://images.wikidexcdn.net/")
    assert found["Archivo:Carátula que no existe.png"] is None
    leafgreen = found["File:Carátula de Verde Hoja.png"]
    assert leafgreen is not None
    assert leafgreen.title == "Archivo:Carátula de Verde Hoja.png"


# --- Cache and download --------------------------------------------------------------------------


def test_a_cover_is_downloaded_once_and_reduced(tmp_path: Path) -> None:
    wikidex = FakeWikidex({FIRERED: COVER, EMERALD: jpeg((855, 861))})
    cache = _cache(tmp_path, wikidex)

    first = cache.cover("firered")
    second = cache.cover("firered")
    cache.cover("emerald")

    assert first == second == (f"{COVERS}/firered-{COVER_SIZE}.png", FIRERED)
    assert size_of((tmp_path / first[0]).read_bytes()) == (253, 256)
    assert (tmp_path / COVERS / "firered-original").read_bytes() == COVER
    assert wikidex.info_requests == [[EMERALD, FIRERED]]  # one request for every title
    assert len(wikidex.downloads) == 2


def test_cached_covers_need_no_request(tmp_path: Path) -> None:
    _cache(tmp_path, FakeWikidex({FIRERED: COVER, EMERALD: COVER})).cover("firered")
    wikidex = FakeWikidex({})

    assert _cache(tmp_path, wikidex).cover("firered")[1] == FIRERED
    assert wikidex.info_requests == []
    assert wikidex.downloads == []


def test_a_new_title_in_the_curated_data_downloads_the_cover_again(tmp_path: Path) -> None:
    _cache(tmp_path, FakeWikidex({FIRERED: COVER})).cover("firered")
    renamed = "Archivo:Portada de Rojo Fuego.png"
    wikidex = FakeWikidex({renamed: jpeg((400, 400))})

    path, title = _cache(tmp_path, wikidex, {"firered": renamed}).cover("firered")

    assert title == renamed
    assert size_of((tmp_path / path).read_bytes()) == (256, 256)
    assert len(wikidex.downloads) == 1


def test_a_game_without_curated_cover(tmp_path: Path) -> None:
    assert _reason(_cache(tmp_path, FakeWikidex({})), "ruby") is CoverMissing.NOT_CURATED


def test_a_file_missing_in_wikidex_does_not_stop_the_others(tmp_path: Path) -> None:
    cache = _cache(tmp_path, FakeWikidex({FIRERED: COVER}))

    assert _reason(cache, "emerald") is CoverMissing.NOT_FOUND
    assert cache.cover("firered")[1] == FIRERED


def test_a_download_that_does_not_match_its_sha1_is_not_stored(tmp_path: Path) -> None:
    wikidex = FakeWikidex({FIRERED: COVER}, served=b"<html>error</html>")

    assert _reason(_cache(tmp_path, wikidex), "firered") is CoverMissing.NOT_IMAGE
    assert not (tmp_path / COVERS / f"firered-{COVER_SIZE}.png").exists()


def test_a_file_that_is_not_an_image_is_not_stored(tmp_path: Path) -> None:
    """Its sha1 matches, but Pillow cannot read it."""
    assert _reason(_cache(tmp_path, FakeWikidex({FIRERED: b"no es una imagen"})), "firered") is (
        CoverMissing.NOT_IMAGE
    )


@pytest.mark.parametrize(
    "error",
    [httpx.ConnectError("sin conexión"), httpx.ReadTimeout("tiempo agotado")],
    ids=["connection", "timeout"],
)
def test_wikidex_not_answering_stops_the_downloads(tmp_path: Path, error: Exception) -> None:
    wikidex = FakeWikidex({FIRERED: COVER, EMERALD: COVER}, error=error)
    cache = _cache(tmp_path, wikidex)

    assert _reason(cache, "firered") is CoverMissing.UNAVAILABLE
    assert _reason(cache, "emerald") is CoverMissing.UNAVAILABLE
    assert len(wikidex.info_requests) == 1


def test_offline_only_cached_covers_are_used(tmp_path: Path) -> None:
    _cache(tmp_path, FakeWikidex({FIRERED: COVER})).cover("firered")
    cache = _cache(tmp_path, None)

    assert cache.cover("firered")[1] == FIRERED
    assert _reason(cache, "emerald") is CoverMissing.UNAVAILABLE


def test_requests_to_wikidex_are_spaced_one_second(tmp_path: Path) -> None:
    slept: list[float] = []
    _cache(tmp_path, FakeWikidex({FIRERED: COVER, EMERALD: COVER}), slept=slept).cover("firered")

    # Information and download one right after the other: the second waits about a second.
    assert len(slept) == 1
    assert slept[0] == pytest.approx(1.0, abs=0.05)


# --- Load ----------------------------------------------------------------------------------------


@dataclass
class _Games:
    """FireRed rows (one game)."""

    name: str = "games"
    pokeapi_commit: str | None = None

    def rows(self) -> Iterable[ReferenceModel]:
        return FakeSource(_firered_rows()).rows()


def _games(target: Path) -> dict[str, tuple[str | None, str | None]]:
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        rows = session.exec(select(Game.slug, Game.cover, Game.cover_source)).all()
    engine.dispose()
    return {slug: (cover, source) for slug, cover, source in rows}


def test_the_load_stores_the_cover_of_each_game(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    covers = _cache(tmp_path, FakeWikidex({FIRERED: COVER}))

    report = build_reference([_Games()], target, images=Images(covers=covers))

    assert report.succeeded, report.errors
    assert report.covers == (1, 1)
    assert report.warnings == []
    assert "Portadas: 1 de 1 juegos" in report.render()
    assert _games(target) == {"firered": (f"{COVERS}/firered-{COVER_SIZE}.png", FIRERED)}


def test_a_game_without_cover_is_loaded_with_a_warning(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    covers = _cache(tmp_path, FakeWikidex({}))

    report = build_reference([_Games()], target, images=Images(covers=covers))

    assert report.succeeded, report.errors
    assert report.covers == (0, 1)
    assert report.warnings == ["1 juego sin portada, su fichero no está en WikiDex: firered"]
    assert _games(target) == {"firered": (None, None)}


def test_a_load_without_covers_has_none(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"

    report = build_reference([_Games()], target)

    assert report.succeeded, report.errors
    assert report.covers is None
    assert "Portadas" not in report.render()


def test_the_cli_can_load_without_covers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """ADR-0011: if the application were published, it is loaded without covers."""

    def no_covers(data_dir: Path, offline: bool) -> CoverCache:
        raise AssertionError("con --no-covers no se preparan las portadas")

    monkeypatch.setattr(cli, "default_sources", lambda data_dir, offline: [_Games()])
    monkeypatch.setattr(cli, "default_sprites", lambda data_dir, offline: None)
    monkeypatch.setattr(cli, "default_covers", no_covers)
    monkeypatch.setattr(cli, "FIRST_LOAD_CHECKS", ())

    assert cli.main(["--data-dir", str(tmp_path), "--no-covers"]) == 0
    output = capsys.readouterr().out
    assert "Carga completada." in output
    assert "Portadas" not in output
