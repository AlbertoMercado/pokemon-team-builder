"""Reads of reference.sqlite: forms, their current types, the target games and what a game's
context needs (docs/02-ddt/plan-api.md, "Construcción del GameContext")."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from sqlmodel import Session, col, func, select

from db.reference import (
    EvolutionStep,
    Game,
    GameMechanic,
    GamePokemon,
    KeyBattle,
    KeyBattlePokemon,
    Pokemon,
    PokemonType,
    Species,
    SpeciesEggGroup,
    Type,
    TypeEfficacy,
)


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


def target_game(reference: Session, slug: str) -> Game | None:
    """The game ``slug`` if it can be the target (RF-05, CA-29)."""
    game = reference.get(Game, slug)
    if game is None or not (game.is_target and game.has_breeding):
        return None
    return game


def types_until(reference: Session, generation: int) -> Sequence[Type]:
    """The types that exist in ``generation`` (Steel and Dark appear in the 2nd)."""
    return reference.exec(
        select(Type).where(col(Type.generation) <= generation).order_by(col(Type.slug))
    ).all()


def type_efficacies(reference: Session, generation: int) -> Sequence[TypeEfficacy]:
    return reference.exec(select(TypeEfficacy).where(TypeEfficacy.generation == generation)).all()


def all_species(reference: Session) -> Sequence[Species]:
    return reference.exec(select(Species)).all()


def all_forms(reference: Session) -> Sequence[Pokemon]:
    return reference.exec(select(Pokemon)).all()


def all_form_types(reference: Session) -> Sequence[PokemonType]:
    """The types of every form in every generation, by slot."""
    return reference.exec(select(PokemonType).order_by(col(PokemonType.slot))).all()


def all_egg_groups(reference: Session) -> Sequence[SpeciesEggGroup]:
    return reference.exec(select(SpeciesEggGroup)).all()


def evolution_steps(reference: Session, version_group: str) -> Sequence[EvolutionStep]:
    """The evolution steps that apply in ``version_group``, in load order."""
    return reference.exec(
        select(EvolutionStep)
        .where(EvolutionStep.version_group == version_group)
        .order_by(col(EvolutionStep.id))
    ).all()


def game_pokemon(reference: Session, game: str) -> Sequence[GamePokemon]:
    return reference.exec(select(GamePokemon).where(GamePokemon.game == game)).all()


def game_mechanics(reference: Session, game: str) -> Sequence[GameMechanic]:
    return reference.exec(
        select(GameMechanic).where(GameMechanic.game == game).order_by(col(GameMechanic.mechanic))
    ).all()


def key_battles(reference: Session, game: str) -> Sequence[KeyBattle]:
    """The key battles of ``game`` in their order."""
    return reference.exec(
        select(KeyBattle).where(KeyBattle.game == game).order_by(col(KeyBattle.order))
    ).all()


def key_battle_pokemon(reference: Session, game: str) -> Sequence[KeyBattlePokemon]:
    """The Pokémon of every key battle of ``game``, in the order of each team."""
    return reference.exec(
        select(KeyBattlePokemon)
        .join(KeyBattle, col(KeyBattle.slug) == col(KeyBattlePokemon.battle))
        .where(KeyBattle.game == game)
        .order_by(col(KeyBattlePokemon.battle), col(KeyBattlePokemon.position))
    ).all()


def all_games(reference: Session) -> dict[str, Game]:
    """Every loaded game, target or not, by slug: any can be in the Hall of Fame (RF-12)."""
    return {game.slug: game for game in reference.exec(select(Game))}


def types_in_generation(
    reference: Session, slugs: Iterable[str], generation: int
) -> dict[str, tuple[str, ...]]:
    """The types of the given forms in ``generation``; a form without them is left out."""
    wanted = list(set(slugs))
    rows = reference.exec(
        select(PokemonType)
        .where(col(PokemonType.pokemon).in_(wanted), PokemonType.generation == generation)
        .order_by(col(PokemonType.slot))
    )
    types: dict[str, list[str]] = {}
    for row in rows:
        types.setdefault(row.pokemon, []).append(row.type)
    return {slug: tuple(found) for slug, found in types.items()}
