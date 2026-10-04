"""Data sources of the ingest: each one turns external data into reference.sqlite rows.

Adapters (PokeAPI CSV, curated YAML, WikiDex) are added in the following phases of the
data load plan (docs/02-ddt/plan-carga-datos.md).
"""

from collections.abc import Iterable
from typing import Protocol

from db.reference import ReferenceModel


class Source(Protocol):
    """A data source of the ingest.

    ``rows`` yields validated, normalised rows ready to be stored. Rows of different tables
    can come in any order: the loader checks foreign keys once all rows are in.
    """

    @property
    def name(self) -> str:
        """Short name used in the load report, e.g. ``pokeapi``."""
        ...

    @property
    def pokeapi_commit(self) -> str | None:
        """PokeAPI commit the data comes from, or ``None`` if the source is not PokeAPI."""
        ...

    def rows(self) -> Iterable[ReferenceModel]:
        """Yield the rows this source contributes."""
        ...
