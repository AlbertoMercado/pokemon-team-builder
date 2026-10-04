"""Download of WikiDex pages through its MediaWiki API, with a local cache and a rate limit.

WikiDex is a community wiki: it is never queried in bulk and never without cache. Each page
is downloaded once (``action=parse&prop=wikitext``), at most one request per second, with a
descriptive User-Agent, and kept in ``<data-dir>/cache/wikidex/``. To refresh a page, delete
its cached file.
"""

import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict

from ingest.sources.pokeapi.download import DOWNLOAD_TIMEOUT_SECONDS, USER_AGENT

API_URL = "https://www.wikidex.net/api.php"
MIN_SECONDS_BETWEEN_REQUESTS = 1.0


class WikiPage(BaseModel):
    """Wikitext of a page and the revision it comes from."""

    model_config = ConfigDict(frozen=True)

    title: str
    revision: int
    wikitext: str


type PageFetcher = Callable[[str], WikiPage]


class WikidexError(Exception):
    """A page could not be obtained from WikiDex or its cache."""


class _ParseResult(BaseModel):
    title: str
    revid: int
    wikitext: str


class _ApiError(BaseModel):
    code: str
    info: str


class _ApiResponse(BaseModel):
    parse: _ParseResult | None = None
    error: _ApiError | None = None


def fetch_page(title: str) -> WikiPage:
    """Download the current wikitext of a page, following redirects."""
    response = httpx.get(
        API_URL,
        params={
            "action": "parse",
            "format": "json",
            "formatversion": "2",
            "prop": "wikitext|revid",
            "redirects": "1",
            "page": title,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=DOWNLOAD_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = _ApiResponse.model_validate_json(response.content)
    if data.parse is None:
        detail = data.error.info if data.error else "respuesta sin contenido"
        raise WikidexError(f"WikiDex no devuelve la página {title!r}: {detail}")
    return WikiPage(title=data.parse.title, revision=data.parse.revid, wikitext=data.parse.wikitext)


class PageCache:
    """WikiDex pages, downloaded on first use and then read from disk.

    ``fetcher`` is ``None`` in offline mode: a page that is not cached is an error.
    ``clock`` and ``sleep`` can be replaced in tests.
    """

    def __init__(
        self,
        directory: Path,
        fetcher: PageFetcher | None,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.directory = directory
        self._fetcher = fetcher
        self._clock = clock
        self._sleep = sleep
        self._last_request: float | None = None

    def path(self, title: str) -> Path:
        return self.directory / f"{quote(title, safe='')}.json"

    def page(self, title: str) -> WikiPage:
        target = self.path(title)
        if target.exists():
            return WikiPage.model_validate_json(target.read_text(encoding="utf-8"))
        if self._fetcher is None:
            raise WikidexError(
                f"La página {title!r} no está en la caché ({target}) y la descarga está desactivada"
            )
        self._wait_for_rate_limit()
        page = self._fetcher(title)
        self.directory.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(f"{target.name}.part")
        partial.write_text(page.model_dump_json(indent=1), encoding="utf-8")
        partial.replace(target)
        return page

    def _wait_for_rate_limit(self) -> None:
        now = self._clock()
        if self._last_request is not None:
            remaining = MIN_SECONDS_BETWEEN_REQUESTS - (now - self._last_request)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request = self._clock()
