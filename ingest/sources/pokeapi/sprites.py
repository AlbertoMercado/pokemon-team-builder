"""Images of the forms, from the PokeAPI/sprites repository pinned to a commit (ADR-0010).

Two images per form, both downloaded once, file by file (the repository is about 10 GB), into
a permanent cache, ``<data-dir>/cache/pokeapi-sprites/<commit>/``:

- the **sprite** (``<pokeapi_id>.png``, 96 x 96 px), kept as downloaded, and its version
  **trimmed** to the figure (``trimmed/<pokeapi_id>.png``), which is the one the lists show:
  the figure of a sprite only fills about half of its canvas;
- the **official artwork** for the detail, reduced to ``ARTWORK_SIZE`` px when downloaded
  (``official-artwork-<size>/<pokeapi_id>.png``): the original is about 120 KB.

The images belong to their owners, so the cache is never versioned (CA-56). An image that
cannot be obtained is not an error: the form is loaded without it and the load report says so.
"""

import io
import time
from collections.abc import Callable
from enum import StrEnum
from functools import partial
from pathlib import Path, PurePosixPath

import httpx
from PIL import Image, UnidentifiedImageError

from ingest.sources.pokeapi.download import Downloader

RAW_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/{commit}/sprites/pokemon/{path}"
SPRITE_PATH = "{pokeapi_id}.png"
ARTWORK_PATH = "other/official-artwork/{pokeapi_id}.png"
# Shown at 160 px in the detail: 256 px keeps it sharp on high density screens.
ARTWORK_SIZE = 256
# The CDN of GitHub does not publish a rate limit; requests are spaced anyway.
MIN_SECONDS_BETWEEN_REQUESTS = 0.2
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HTTP_NOT_FOUND = 404


class MissingReason(StrEnum):
    """Why a form has no image. The values are the texts of the load report."""

    NOT_FOUND = "no está en el repositorio de imágenes"
    NOT_PNG = "la descarga no es una imagen PNG válida"
    UNAVAILABLE = "no está en la caché y no se ha podido descargar"


class MissingSpriteError(Exception):
    """An image of a form could not be obtained."""

    def __init__(self, pokeapi_id: int, reason: MissingReason) -> None:
        super().__init__(f"imagen {pokeapi_id}: {reason}")
        self.reason = reason


def trimmed(content: bytes) -> bytes:
    """The PNG cropped to its figure: without the transparent margin around it."""
    with Image.open(io.BytesIO(content)) as image:
        rgba = image.convert("RGBA")
    box = rgba.getchannel("A").getbbox()
    return _png(rgba.crop(box) if box is not None else rgba)


def reduced(content: bytes, size: int) -> bytes:
    """The PNG reduced to fit in ``size`` x ``size`` px, keeping its proportions."""
    with Image.open(io.BytesIO(content)) as image:
        rgba = image.convert("RGBA")
    rgba.thumbnail((size, size), Image.Resampling.LANCZOS)
    return _png(rgba)


def _png(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


class SpriteCache:
    """Images of one commit of PokeAPI/sprites, downloaded on first use.

    ``downloader`` is ``None`` in offline mode: only cached images are used. After a failure
    that is not a missing file (no connection, timeout, a server error), downloading stops for
    the rest of the load, so an unreachable server does not cost one timeout per image.
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
        """Path of the trimmed sprite relative to the data directory, built if needed.

        Raises ``MissingSpriteError`` if the sprite is not cached and cannot be downloaded.
        """
        sprite = self._relative_directory / f"{pokeapi_id}.png"
        if not (self.data_dir / sprite).exists():
            self._store(sprite, self._download(SPRITE_PATH, pokeapi_id))
        relative = self._relative_directory / "trimmed" / f"{pokeapi_id}.png"
        if not (self.data_dir / relative).exists():
            content = (self.data_dir / sprite).read_bytes()
            self._store(relative, self._processed(trimmed, content, pokeapi_id))
        return relative.as_posix()

    def artwork(self, pokeapi_id: int) -> str:
        """Path of the reduced official artwork relative to the data directory.

        Raises ``MissingSpriteError`` if it is not cached and cannot be downloaded.
        """
        directory = f"official-artwork-{ARTWORK_SIZE}"
        relative = self._relative_directory / directory / f"{pokeapi_id}.png"
        if not (self.data_dir / relative).exists():
            content = self._download(ARTWORK_PATH, pokeapi_id)
            reduce = partial(reduced, size=ARTWORK_SIZE)
            self._store(relative, self._processed(reduce, content, pokeapi_id))
        return relative.as_posix()

    def _download(self, path: str, pokeapi_id: int) -> bytes:
        if self._downloader is None:
            raise MissingSpriteError(pokeapi_id, MissingReason.UNAVAILABLE)
        self._wait_for_rate_limit()
        url = RAW_URL.format(commit=self.commit, path=path.format(pokeapi_id=pokeapi_id))
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
        return content

    @staticmethod
    def _processed(process: Callable[[bytes], bytes], content: bytes, pokeapi_id: int) -> bytes:
        try:
            return process(content)
        except (UnidentifiedImageError, OSError, ValueError) as error:
            raise MissingSpriteError(pokeapi_id, MissingReason.NOT_PNG) from error

    def _store(self, relative: PurePosixPath, content: bytes) -> None:
        target = self.data_dir / relative
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
