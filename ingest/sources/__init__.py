"""Data sources of the ingest: each one turns external data into reference.sqlite rows.

The adapters (PokeAPI CSV, curated YAML, WikiDex) live in the subpackages; how each source is
interpreted is in the load design (docs/02-ddt/carga-datos.md).
"""

from collections.abc import Iterable, Sequence
from typing import Protocol

from db.reference import ReferenceModel
from ingest.blockers import Blocker


class Source(Protocol):
    """A data source of the ingest.

    ``rows`` yields validated, normalised rows ready to be stored. Rows of different tables
    can come in any order: the loader checks foreign keys once all rows are in. What the
    source cannot handle without a new version is left out of the rows and reported in
    ``blockers`` (ADR-0008).
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

    @property
    def blockers(self) -> Sequence[Blocker]:
        """What blocked the load in this source; complete once ``rows`` has been consumed."""
        ...
