"""Curated data: versioned YAML files in ``data/curated/`` (ADR-0005).

``read_curated`` reads and validates every file. ``CuratedSource`` loads the rows that come
only from curated data (game mechanics, starters, the Pokédex of each game, transfers and
event Pokémon). The PokeAPI source also uses the curated data for incense babies, arrival
proposals and locations, and the WikiDex source for the list of key battles.
See docs/02-ddt/datos-curados.md.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from db.reference import (
    EventPokemon,
    EvolutionMethod,
    GameMechanic,
    GamePokedex,
    GameStarter,
    GameTransfer,
    MethodKind,
    Origin,
    ReferenceModel,
)
from ingest.blockers import Blocker
from ingest.sources.curated.schemas import (
    ArrivalFile,
    ArrivalRule,
    BreedingFile,
    CatalogFile,
    CoversFile,
    EventsFile,
    EvolutionMethodsFile,
    GamesFile,
    KeyBattlesFile,
    LocationsFile,
    PinnedCommitFile,
    PokedexFile,
    StartersFile,
    TransfersFile,
)


class CuratedDataError(Exception):
    """A curated file is missing or invalid."""


@dataclass(frozen=True)
class CuratedData:
    """Every curated file, already validated."""

    pokeapi_commit: str
    sprites_commit: str
    games: GamesFile
    breeding: BreedingFile
    arrival: ArrivalFile
    starters: StartersFile
    key_battles: list[KeyBattlesFile]
    pokedex: PokedexFile
    transfers: TransfersFile
    events: EventsFile
    locations: LocationsFile
    evolution_methods: EvolutionMethodsFile
    catalog: CatalogFile

    def arrival_rule(self, game: str) -> ArrivalRule | None:
        return self.arrival.games.get(game)


def _read[M: BaseModel](path: Path, model: type[M]) -> M:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        return model.model_validate(content)
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise CuratedDataError(f"{path}: {error}") from error


def read_pinned_commits(path: Path) -> PinnedCommitFile:
    """Read and validate the pinned commits of ``pokeapi.yaml``."""
    return _read(path, PinnedCommitFile)


def read_covers(path: Path) -> CoversFile:
    """Read and validate ``covers.yaml``, the cover of each game in WikiDex (ADR-0011)."""
    return _read(path, CoversFile)


def read_curated(directory: Path) -> CuratedData:
    """Read and validate every curated file of ``directory``."""
    commits = read_pinned_commits(directory / "pokeapi.yaml")
    return CuratedData(
        pokeapi_commit=commits.commit,
        sprites_commit=commits.sprites_commit,
        games=_read(directory / "games.yaml", GamesFile),
        breeding=_read(directory / "breeding.yaml", BreedingFile),
        arrival=_read(directory / "arrival.yaml", ArrivalFile),
        starters=_read(directory / "starters.yaml", StartersFile),
        key_battles=[
            _read(path, KeyBattlesFile)
            for path in sorted((directory / "key_battles").glob("*.yaml"))
        ],
        pokedex=_read(directory / "pokedex.yaml", PokedexFile),
        transfers=_read(directory / "transfers.yaml", TransfersFile),
        events=_read(directory / "events.yaml", EventsFile),
        locations=_read(directory / "locations.yaml", LocationsFile),
        evolution_methods=_read(directory / "evolution_methods.yaml", EvolutionMethodsFile),
        catalog=_read(directory / "catalog.yaml", CatalogFile),
    )


class CuratedSource:
    """Ingest source of the rows that only come from curated data: game mechanics, starters,
    the Pokédex of each game, transfers, event Pokémon and the catalog of evolution methods."""

    name = "curated"
    pokeapi_commit = None
    blockers: tuple[Blocker, ...] = ()

    def __init__(self, curated: CuratedData) -> None:
        self._curated = curated

    def rows(self) -> Iterable[ReferenceModel]:
        for game, mechanics in self._curated.games.games.items():
            for mechanic, entry in mechanics.items():
                yield GameMechanic(
                    game=game,
                    mechanic=mechanic,
                    value=entry.value,
                    origin=Origin(entry.origin),
                    fact_key=f"mechanic:{game}:{mechanic}",
                )
        for game, starters in self._curated.starters.games.items():
            for pokemon in starters:
                yield GameStarter(game=game, pokemon=pokemon)
        for game, pokedexes in self._curated.pokedex.games.items():
            for pokedex in pokedexes:
                yield GamePokedex(game=game, pokedex=pokedex)
        for (from_game, to_game), limit in transfer_pairs(self._curated.transfers).items():
            yield GameTransfer(from_game=from_game, to_game=to_game, max_species_generation=limit)
        events = {
            (game, pokemon)
            for group in self._curated.events.events
            for game in group.games
            for pokemon in group.pokemon
        }
        for game, pokemon in sorted(events):
            yield EventPokemon(game=game, pokemon=pokemon)
        catalog = self._curated.evolution_methods
        for kind, methods in (
            (MethodKind.TRIGGER, catalog.triggers),
            (MethodKind.CONDITION, catalog.conditions),
        ):
            for name, method in methods.items():
                yield EvolutionMethod(
                    kind=kind,
                    name=name,
                    category=method.category,
                    reason=method.reason,
                    requires_mechanic=method.requires_mechanic,
                    unless_learnt_by_level=method.unless_learnt_by_level,
                )


def transfer_pairs(transfers: TransfersFile) -> dict[tuple[str, str], int | None]:
    """Every ordered pair of games of a group, with its species limit.

    A pair in several groups keeps the least restrictive limit: none, or the latest
    generation.
    """
    pairs: dict[tuple[str, str], int | None] = {}
    for group in transfers.groups:
        for from_game in group.games:
            for to_game in group.games:
                if from_game == to_game:
                    continue
                pair = (from_game, to_game)
                limit = group.max_species_generation
                if pair in pairs:
                    previous = pairs[pair]
                    limit = None if previous is None or limit is None else max(previous, limit)
                pairs[pair] = limit
    return pairs
