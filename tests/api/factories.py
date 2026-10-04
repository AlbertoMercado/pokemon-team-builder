"""Builders of reference.sqlite files for the API tests.

Each test creates the reference data it needs in a temporary data directory, with the models of
``db/reference``, as ``tests/core/builders.py`` does for the engine:
``reference_database(data_dir, pokemon=[form("vulpix-alola", ("ice",), dex=37)])``.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from db.reference import (
    Game,
    Generation,
    IngestRun,
    Pokemon,
    PokemonType,
    Species,
    Type,
    VersionGroup,
    create_reference_schema,
)
from db.sqlite import create_sqlite_engine

LOADED_AT = datetime(2026, 10, 4, 10, 0, 0, tzinfo=UTC)
TYPES = (
    "normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost", "fire",
    "water", "grass", "electric", "psychic", "ice", "dragon", "steel", "dark",
)  # fmt: skip


@dataclass(frozen=True)
class Form:
    """A form to load; ``types`` maps each generation to the types it has in it."""

    slug: str
    dex: int
    types: dict[int, tuple[str, ...]]
    name: str = ""
    species: str = ""
    region: str | None = None


def form(
    slug: str,
    types: tuple[str, ...] = ("normal",),
    *,
    dex: int = 1,
    species: str = "",
    region: str | None = None,
    past: dict[int, tuple[str, ...]] | None = None,
) -> Form:
    """A form with ``types`` in the 3rd generation and, optionally, other types before."""
    return Form(
        slug,
        dex,
        {**(past or {}), 3: types},
        slug.replace("-", " ").title(),
        species or slug,
        region,
    )


@dataclass(frozen=True)
class GameRow:
    slug: str
    generation: int = 3
    version_group: str = "firered-leafgreen"
    is_target: bool = True
    has_breeding: bool = True
    release_order: int = 1


DEFAULT_GAMES = (
    GameRow("firered", release_order=10),
    GameRow("leafgreen", release_order=11),
)


def reference_database(
    data_dir: Path,
    *,
    pokemon: Sequence[Form] = (),
    games: Sequence[GameRow] = DEFAULT_GAMES,
    pokeapi_commit: str | None = "bc92d3b",
) -> Path:
    """A reference.sqlite with the 3 first generations, the given forms and games, and the
    record of its load."""
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "reference.sqlite"
    engine = create_sqlite_engine(path)
    create_reference_schema(engine)
    with Session(engine) as session:
        session.add_all(Generation(number=n, slug=f"generation-{n}") for n in (1, 2, 3))
        session.add_all(Type(slug=t, name_es=t.title(), generation=1) for t in TYPES)
        groups = {(g.version_group, g.generation) for g in games}
        session.add_all(
            VersionGroup(slug=slug, generation=gen, order=i)
            for i, (slug, gen) in enumerate(sorted(groups), start=1)
        )
        session.flush()
        session.add_all(
            Game(
                slug=g.slug,
                name_es=g.slug.title(),
                version_group=g.version_group,
                generation=g.generation,
                release_order=g.release_order,
                has_breeding=g.has_breeding,
                is_target=g.is_target,
            )
            for g in games
        )
        for f in pokemon:
            if session.get(Species, f.species) is None:
                session.add(
                    Species(
                        slug=f.species,
                        dex_number=f.dex,
                        name_es=f.species.title(),
                        generation=1,
                        evolution_chain=f.dex,
                        is_baby=False,
                        is_legendary=False,
                        is_mythical=False,
                    )
                )
                session.flush()
            session.add(
                Pokemon(
                    slug=f.slug,
                    species=f.species,
                    name_es=f.name,
                    is_default=f.region is None,
                    region=f.region,
                )
            )
            session.flush()
            for generation, types in f.types.items():
                session.add_all(
                    PokemonType(pokemon=f.slug, generation=generation, slot=slot, type=t)
                    for slot, t in enumerate(types, start=1)
                )
        session.add(
            IngestRun(
                started_at=LOADED_AT,
                finished_at=LOADED_AT,
                pokeapi_commit=pokeapi_commit,
                games=[g.slug for g in games],
            )
        )
        session.commit()
    engine.dispose()
    return path
