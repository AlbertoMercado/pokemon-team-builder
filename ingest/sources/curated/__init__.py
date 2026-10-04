"""Curated data: versioned YAML files in ``data/curated/`` (ADR-0005).

``read_curated`` reads and validates every file. ``CuratedSource`` loads the rows that come
only from curated data (game mechanics and the list of key battles); the PokeAPI source
also uses the curated data for incense babies and arrival proposals. See
docs/02-ddt/datos-curados.md.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from db.reference import GameMechanic, KeyBattle, Origin, ReferenceModel
from ingest.sources.curated.schemas import (
    ArrivalFile,
    ArrivalRule,
    BreedingFile,
    GamesFile,
    KeyBattlesFile,
    PinnedCommitFile,
)


class CuratedDataError(Exception):
    """A curated file is missing or invalid."""


@dataclass(frozen=True)
class CuratedData:
    """Every curated file, already validated."""

    pokeapi_commit: str
    games: GamesFile
    breeding: BreedingFile
    arrival: ArrivalFile
    key_battles: list[KeyBattlesFile]

    def arrival_rule(self, game: str) -> ArrivalRule | None:
        return self.arrival.games.get(game)


def _read[M: BaseModel](path: Path, model: type[M]) -> M:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        return model.model_validate(content)
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise CuratedDataError(f"{path}: {error}") from error


def read_pinned_commit(path: Path) -> str:
    """Read and validate the pinned PokeAPI commit of ``pokeapi.yaml``."""
    return _read(path, PinnedCommitFile).commit


def read_curated(directory: Path) -> CuratedData:
    """Read and validate every curated file of ``directory``."""
    return CuratedData(
        pokeapi_commit=read_pinned_commit(directory / "pokeapi.yaml"),
        games=_read(directory / "games.yaml", GamesFile),
        breeding=_read(directory / "breeding.yaml", BreedingFile),
        arrival=_read(directory / "arrival.yaml", ArrivalFile),
        key_battles=[
            _read(path, KeyBattlesFile)
            for path in sorted((directory / "key_battles").glob("*.yaml"))
        ],
    )


class CuratedSource:
    """Ingest source of the rows that only come from curated data."""

    name = "curated"
    pokeapi_commit = None

    def __init__(self, curated: CuratedData) -> None:
        self._curated = curated

    def rows(self) -> Iterable[ReferenceModel]:
        yield from self._mechanics()
        yield from self._key_battles()

    def _mechanics(self) -> Iterator[GameMechanic]:
        for game, mechanics in self._curated.games.games.items():
            for mechanic, entry in mechanics.items():
                yield GameMechanic(
                    game=game,
                    mechanic=mechanic,
                    value=entry.value,
                    origin=Origin(entry.origin),
                    fact_key=f"mechanic:{game}:{mechanic}",
                )

    def _key_battles(self) -> Iterator[KeyBattle]:
        """Key battles of each game; teams are pending until they are read (phase 5)."""
        for battles_file in self._curated.key_battles:
            for game in battles_file.games:
                for order, battle in enumerate(battles_file.battles, start=1):
                    yield KeyBattle(
                        slug=f"{game}-{battle.id}",
                        game=game,
                        category=battle.category,
                        trainer_name=battle.trainer,
                        order=order,
                        origin=Origin.PENDING,
                        fact_key=f"battle:{game}:{battle.id}",
                    )
