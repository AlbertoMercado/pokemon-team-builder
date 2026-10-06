"""Covers of the games, from WikiDex, with a permanent cache and a rate limit (RF-18, ADR-0011).

WikiDex declares its covers fair use only in its own articles: the application uses them
privately, never versions nor redistributes them, and can load without them (``--no-covers``).

The title of each cover is curated (``data/curated/covers.yaml``). Their URLs and ``sha1`` come
from one request to the MediaWiki API (``prop=imageinfo``); then each cover is downloaded once,
at most one request per second, with a descriptive User-Agent, and kept in
``<data-dir>/cache/wikidex/covers/``: ``<game>.json`` (where it comes from), the original and
``<game>-<size>.png``, reduced with Pillow, which is the one the application shows. To refresh a
cover, delete its files from the cache. A cover that cannot be obtained is not an error: the
game is loaded without it and the load report says so.
"""

import hashlib
import time
from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import NamedTuple

import httpx
from pydantic import BaseModel, ConfigDict, Field

from ingest.sources.pokeapi.download import DOWNLOAD_TIMEOUT_SECONDS, USER_AGENT, Downloader
from ingest.sources.pokeapi.sprites import reduced
from ingest.sources.wikidex.fetch import API_URL, MIN_SECONDS_BETWEEN_REQUESTS

COVER_SIZE = 256


class CoverMissing(StrEnum):
    """Why a game has no cover. The values are the texts of the load report."""

    NOT_CURATED = "no tiene portada en data/curated/covers.yaml"
    NOT_FOUND = "su fichero no está en WikiDex"
    NOT_IMAGE = "la descarga no es la imagen de WikiDex"
    UNAVAILABLE = "no está en la caché y no se ha podido descargar"


class CoverInfo(BaseModel):
    """Where a cover comes from: its file page in WikiDex, its URL and its ``sha1``."""

    model_config = ConfigDict(frozen=True)

    title: str
    url: str
    sha1: str


type InfoFetcher = Callable[[Sequence[str]], dict[str, CoverInfo | None]]


class CoverFetchers(NamedTuple):
    """How covers are obtained: the information of the files and their download."""

    info: InfoFetcher
    download: Downloader


class _ImageInfo(BaseModel):
    url: str
    sha1: str


class _Page(BaseModel):
    title: str
    missing: bool = False
    imageinfo: list[_ImageInfo] = []


class _Normalized(BaseModel):
    """A title the API changed: ``File:…`` to ``Archivo:…``, for example."""

    model_config = ConfigDict(populate_by_name=True)

    from_title: str = Field(alias="from")
    to: str


class _Query(BaseModel):
    pages: list[_Page] = []
    normalized: list[_Normalized] = []


class _Response(BaseModel):
    query: _Query


def fetch_cover_info(titles: Sequence[str]) -> dict[str, CoverInfo | None]:
    """URL and ``sha1`` of each file, by the title asked for; ``None`` if it does not exist."""
    response = httpx.get(
        API_URL,
        params={
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url|sha1",
            "titles": "|".join(titles),
        },
        headers={"User-Agent": USER_AGENT},
        timeout=DOWNLOAD_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    query = _Response.model_validate_json(response.content).query
    # The API answers with the canonical title, which may differ from the one asked for.
    canonical = {item.from_title: item.to for item in query.normalized}
    pages = {page.title: page for page in query.pages}
    found: dict[str, CoverInfo | None] = {}
    for title in titles:
        page = pages.get(canonical.get(title, title))
        if page is None or page.missing or not page.imageinfo:
            found[title] = None
        else:
            info = page.imageinfo[0]
            found[title] = CoverInfo(title=page.title, url=info.url, sha1=info.sha1)
    return found


class MissingCoverError(Exception):
    """The cover of a game could not be obtained."""

    def __init__(self, game: str, reason: CoverMissing) -> None:
        super().__init__(f"portada de {game}: {reason}")
        self.reason = reason


class CoverCache:
    """Covers of the games, downloaded on first use and then read from disk.

    ``fetchers`` is ``None`` in offline mode: only cached covers are used.
    After a failure that is not a missing file, downloading stops for the rest of the load.
    ``clock`` and ``sleep`` can be replaced in tests.
    """

    def __init__(
        self,
        data_dir: Path,
        titles: Mapping[str, str],
        fetchers: CoverFetchers | None,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.data_dir = data_dir
        self.titles = dict(titles)
        self._relative_directory = PurePosixPath("cache", "wikidex", "covers")
        self._fetch_info = fetchers.info if fetchers is not None else None
        self._downloader = fetchers.download if fetchers is not None else None
        self._clock = clock
        self._sleep = sleep
        self._last_request: float | None = None
        self._info: dict[str, CoverInfo | None] | None = None

    def cover(self, game: str) -> tuple[str, str]:
        """Path of the reduced cover relative to the data directory, and its WikiDex title.

        Raises ``MissingCoverError`` if the game has no curated cover or it cannot be obtained.
        """
        title = self.titles.get(game)
        if title is None:
            raise MissingCoverError(game, CoverMissing.NOT_CURATED)
        relative = self._relative_directory / f"{game}-{COVER_SIZE}.png"
        source = self._relative_directory / f"{game}.json"
        if (self.data_dir / relative).exists() and self._cached_title(source) == title:
            return relative.as_posix(), title
        info = self._info_of(game, title)
        content = self._download(game, info)
        try:
            cover = reduced(content, COVER_SIZE)
        except (OSError, ValueError) as error:
            raise MissingCoverError(game, CoverMissing.NOT_IMAGE) from error
        self._store(self._relative_directory / f"{game}-original", content)
        self._store(relative, cover)
        self._store(source, info.model_dump_json(indent=1).encode())
        return relative.as_posix(), title

    def _cached_title(self, source: PurePosixPath) -> str | None:
        """The title the cached cover was downloaded from: a change in the curated data
        downloads it again."""
        path = self.data_dir / source
        if not path.exists():
            return None
        return CoverInfo.model_validate_json(path.read_text(encoding="utf-8")).title

    def _info_of(self, game: str, title: str) -> CoverInfo:
        """The URL and ``sha1`` of the cover, asked for every curated title at once."""
        if self._info is None:
            if self._fetch_info is None:
                raise MissingCoverError(game, CoverMissing.UNAVAILABLE)
            self._wait_for_rate_limit()
            try:
                self._info = self._fetch_info(sorted(set(self.titles.values())))
            except httpx.HTTPError as error:
                self._fetch_info = self._downloader = None
                raise MissingCoverError(game, CoverMissing.UNAVAILABLE) from error
        info = self._info.get(title)
        if info is None:
            raise MissingCoverError(game, CoverMissing.NOT_FOUND)
        return info

    def _download(self, game: str, info: CoverInfo) -> bytes:
        if self._downloader is None:
            raise MissingCoverError(game, CoverMissing.UNAVAILABLE)
        self._wait_for_rate_limit()
        try:
            content = self._downloader(info.url)
        except httpx.HTTPError as error:
            self._downloader = None
            raise MissingCoverError(game, CoverMissing.UNAVAILABLE) from error
        if hashlib.sha1(content).hexdigest() != info.sha1:
            raise MissingCoverError(game, CoverMissing.NOT_IMAGE)
        return content

    def _store(self, relative: PurePosixPath, content: bytes) -> None:
        target = self.data_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(f"{target.name}.part")
        partial.write_bytes(content)
        partial.replace(target)  # never leave a half-written file in the cache

    def _wait_for_rate_limit(self) -> None:
        now = self._clock()
        if self._last_request is not None:
            remaining = MIN_SECONDS_BETWEEN_REQUESTS - (now - self._last_request)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request = self._clock()
