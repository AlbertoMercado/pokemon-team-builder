"""Configuration of the API: where the two SQLite files are and where the compiled web is
(docs/05-operacion/api.md)."""

import os
from dataclasses import dataclass
from pathlib import Path

DATA_DIR_VARIABLE = "PTB_DATA_DIR"
DEFAULT_DATA_DIR = Path("data")
WEB_DIR_VARIABLE = "PTB_WEB_DIR"
DEFAULT_WEB_DIR = Path("web/dist")


@dataclass(frozen=True)
class Settings:
    """``data_dir`` holds reference.sqlite (written by the ingest) and user.sqlite.

    ``web_dir`` is the build of the web (``npm run build``) that the API serves at ``/``;
    ``None``, or a directory without a build, serves only the API.
    """

    data_dir: Path
    web_dir: Path | None = None

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            Path(os.environ.get(DATA_DIR_VARIABLE, DEFAULT_DATA_DIR)),
            Path(os.environ.get(WEB_DIR_VARIABLE, DEFAULT_WEB_DIR)),
        )

    @property
    def reference_path(self) -> Path:
        return self.data_dir / "reference.sqlite"

    @property
    def user_path(self) -> Path:
        return self.data_dir / "user.sqlite"
