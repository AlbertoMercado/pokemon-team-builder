"""Sprites of the forms, from the PokeAPI/sprites repository pinned to a commit (ADR-0010).

Each sprite is downloaded once, file by file (the repository is about 10 GB), and kept in a
permanent cache, ``<data-dir>/cache/pokeapi-sprites/<commit>/<pokeapi_id>.png``: files of a
pinned commit never change. The images belong to their owners, so the cache is never
versioned (CA-56). A sprite that cannot be obtained is not an error: the form is loaded
without image and the load report says so.
"""

import time
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path, PurePosixPath

import httpx

from ingest.sources.pokeapi.download import Downloader

RAW_SPRITE_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/{commit}/sprites/pokemon/{pokeapi_id}.png"
)
# The CDN of GitHub does not publish a rate limit; requests are spaced anyway.
MIN_SECONDS_BETWEEN_REQUESTS = 0.2
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HTTP_NOT_FOUND = 404


class MissingReason(StrEnum):
    """Why a form has no sprite. The values are the texts of the load report."""

    NOT_FOUND = "no está en el repositorio de imágenes"
    NOT_PNG = "la descarga no es una imagen PNG"
    UNAVAILABLE = "no está en la caché y no se ha podido descargar"


class MissingSpriteError(Exception):
    """The sprite of a form could not be obtained."""

    def __init__(self, pokeapi_id: int, reason: MissingReason) -> None:
        super().__init__(f"imagen {pokeapi_id}: {reason}")
        self.reason = reason


class SpriteCache:
    """Sprites of one commit of PokeAPI/sprites, downloaded on first use.

    ``downloader`` is ``None`` in offline mode: only cached sprites are used. After a failure
    that is not a missing file (no connection, timeout, a server error), downloading stops for
    the rest of the load, so an unreachable server does not cost one timeout per form.
    ``clock`` and ``sleep`` can be replaced in tests.
    """

    def __init__(
        self,
        data_dir: Path,
        commit: str,
        downloader: Downloader | None,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.data_dir = data_dir
        self.commit = commit
        self._relative_directory = PurePosixPath("cache", "pokeapi-sprites", commit)
        self._downloader = downloader
        self._clock = clock
        self._sleep = sleep
        self._last_request: float | None = None

    def image(self, pokeapi_id: int) -> str:
        """Path of the sprite relative to the data directory, downloading it if needed.

        Raises ``MissingSpriteError`` if it is not cached and cannot be downloaded.
        """
        relative = self._relative_directory / f"{pokeapi_id}.png"
        target = self.data_dir / relative
        if not target.exists():
            self._download(pokeapi_id, target)
        return relative.as_posix()

    def _download(self, pokeapi_id: int, target: Path) -> None:
        if self._downloader is None:
            raise MissingSpriteError(pokeapi_id, MissingReason.UNAVAILABLE)
        self._wait_for_rate_limit()
        url = RAW_SPRITE_URL.format(commit=self.commit, pokeapi_id=pokeapi_id)
        try:
            content = self._downloader(url)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == HTTP_NOT_FOUND:
                raise MissingSpriteError(pokeapi_id, MissingReason.NOT_FOUND) from error
            self._downloader = None
            raise MissingSpriteError(pokeapi_id, MissingReason.UNAVAILABLE) from error
        except httpx.HTTPError as error:
            self._downloader = None
            raise MissingSpriteError(pokeapi_id, MissingReason.UNAVAILABLE) from error
        if not content.startswith(PNG_SIGNATURE):
            raise MissingSpriteError(pokeapi_id, MissingReason.NOT_PNG)
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(f"{target.name}.part")
        partial.write_bytes(content)
        partial.replace(target)  # never leave a half-written image in the cache

    def _wait_for_rate_limit(self) -> None:
        now = self._clock()
        if self._last_request is not None:
            remaining = MIN_SECONDS_BETWEEN_REQUESTS - (now - self._last_request)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request = self._clock()
