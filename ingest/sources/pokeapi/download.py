"""Download of the PokeAPI CSV dump pinned to a commit, with a permanent local cache.

Files of a pinned commit never change, so a cached file is never downloaded again
(ADR-0004). The cache lives in ``<data-dir>/cache/pokeapi/<commit>/``.
"""

from collections.abc import Callable
from pathlib import Path

import httpx

RAW_CSV_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/{commit}/data/v2/csv/{name}.csv"
# HTTP headers must be ASCII.
USER_AGENT = (
    "pokemon-team-builder/0.1 "
    "(personal non-profit app; https://github.com/AlbertoMercado/pokemon-team-builder)"
)
DOWNLOAD_TIMEOUT_SECONDS = 60.0

type Downloader = Callable[[str], bytes]


class MissingCsvError(Exception):
    """A CSV file is not cached and downloading is disabled."""


def download(url: str) -> bytes:
    """Download ``url`` with a descriptive User-Agent. Raises on HTTP errors."""
    response = httpx.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=DOWNLOAD_TIMEOUT_SECONDS,
        follow_redirects=True,
    )
    response.raise_for_status()
    return response.content


class CsvCache:
    """CSV files of one PokeAPI commit, downloaded on first use.

    ``downloader`` is ``None`` in offline mode: a file that is not cached is an error.
    """

    def __init__(self, cache_dir: Path, commit: str, downloader: Downloader | None) -> None:
        self.directory = cache_dir / commit
        self.commit = commit
        self._downloader = downloader

    def path(self, name: str) -> Path:
        """Local path of ``<name>.csv``, downloading it first if needed."""
        target = self.directory / f"{name}.csv"
        if target.exists():
            return target
        if self._downloader is None:
            raise MissingCsvError(
                f"{name}.csv no está en la caché ({target}) y la descarga está desactivada"
            )
        content = self._downloader(RAW_CSV_URL.format(commit=self.commit, name=name))
        self.directory.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(f"{target.name}.part")
        partial.write_bytes(content)
        partial.replace(target)  # never leave a half-written file in the cache
        return target
