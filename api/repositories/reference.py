"""Reads of reference.sqlite: forms, their current types and the target games."""

from collections.abc import Iterable
from dataclasses import dataclass

from sqlmodel import Session, col, func, select

from db.reference import Game, Pokemon, PokemonType, Species


@dataclass(frozen=True)
class PokemonRow:
    """A form with its species' number and its types in the latest loaded generation."""

    slug: str
    name: str
    dex_number: int
    types: tuple[str, ...]


def pokemon_exists(reference: Session, slug: str) -> bool:
    return reference.get(Pokemon, slug) is not None


def pokemon_rows(reference: Session, slugs: Iterable[str]) -> list[PokemonRow]:
    """The given forms, in canonical order (National Pokédex number, then form)."""
    wanted = list(slugs)
    if not wanted:
        return []
    forms = reference.exec(
        select(Pokemon, Species)
        .join(Species, col(Species.slug) == col(Pokemon.species))
        .where(col(Pokemon.slug).in_(wanted))
    ).all()
    latest = (
        select(PokemonType.pokemon, func.max(PokemonType.generation).label("generation"))
        .where(col(PokemonType.pokemon).in_(wanted))
        .group_by(col(PokemonType.pokemon))
        .subquery()
    )
    types: dict[str, list[str]] = {}
    for row in reference.exec(
        select(PokemonType)
        .join(
            latest,
            (col(PokemonType.pokemon) == latest.c.pokemon)
            & (col(PokemonType.generation) == latest.c.generation),
        )
        .order_by(col(PokemonType.slot))
    ):
        types.setdefault(row.pokemon, []).append(row.type)
    rows = [
        PokemonRow(p.slug, p.name_es, s.dex_number, tuple(types.get(p.slug, ()))) for p, s in forms
    ]
    return sorted(rows, key=lambda r: (r.dex_number, r.slug))


def target_games(reference: Session) -> list[Game]:
    """Games that can be the target: target games that allow breeding (RF-05, CA-29)."""
    return list(
        reference.exec(
            select(Game)
            .where(col(Game.is_target), col(Game.has_breeding))
            .order_by(col(Game.release_order))
        )
    )
