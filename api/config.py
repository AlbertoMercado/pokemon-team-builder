"""Configuration of the API: where the two SQLite files are (docs/05-operacion/api.md)."""

import os
from dataclasses import dataclass
from pathlib import Path

DATA_DIR_VARIABLE = "PTB_DATA_DIR"
DEFAULT_DATA_DIR = Path("data")


@dataclass(frozen=True)
class Settings:
    """``data_dir`` holds reference.sqlite (written by the ingest) and user.sqlite."""

    data_dir: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(Path(os.environ.get(DATA_DIR_VARIABLE, DEFAULT_DATA_DIR)))

    @property
    def reference_path(self) -> Path:
        return self.data_dir / "reference.sqlite"

    @property
    def user_path(self) -> Path:
        return self.data_dir / "user.sqlite"
