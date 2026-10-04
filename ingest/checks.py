"""Checks of the first load (CA-11): expected counts and known cases.

They run on the freshly built database, before it replaces the previous one. A failed check
means the data is not what the data load plan expects (for example, because the PokeAPI
schema changed), so the load is rejected. See docs/02-ddt/plan-carga-datos.md, section
"Comprobaciones de la carga".
"""

from collections.abc import Callable, Sequence

from sqlalchemy import func
from sqlmodel import Session, col, select

from db.reference import (
    EvolutionStep,
    Game,
    GamePokemon,
    Generation,
    Pokemon,
    PokemonType,
    ReferenceModel,
    Species,
    SpeciesEggGroup,
    Type,
    TypeEfficacy,
    VersionGroup,
)

type Check = Callable[[Session], list[str]]

TARGET_GAMES = frozenset({"ruby", "sapphire", "emerald", "firered", "leafgreen"})
SPECIES_COUNT = 386
EXPECTED_COUNTS: dict[type[ReferenceModel], int] = {
    Generation: 3,
    VersionGroup: 7,
    Game: 11,
    Type: 17,
    Species: SPECIES_COUNT,
    Pokemon: SPECIES_COUNT,
    GamePokemon: len(TARGET_GAMES) * SPECIES_COUNT,
}
# 15 types in the 1st generation, 17 from the 2nd: one factor per pair.
EFFICACY_PAIRS_BY_GENERATION = {1: 15 * 15, 2: 17 * 17, 3: 17 * 17}


def check_counts(session: Session) -> list[str]:
    problems = []
    for model, expected in EXPECTED_COUNTS.items():
        count = session.exec(select(func.count()).select_from(model)).one()
        if count != expected:
            problems.append(f"{model.__tablename__}: {count} filas, se esperaban {expected}")
    for generation, expected in EFFICACY_PAIRS_BY_GENERATION.items():
        query = select(func.count()).select_from(TypeEfficacy)
        count = session.exec(query.where(TypeEfficacy.generation == generation)).one()
        if count != expected:
            problems.append(
                f"type_efficacy: {count} pares en la generación {generation}, "
                f"se esperaban {expected}"
            )
    return problems


def check_target_games(session: Session) -> list[str]:
    targets = set(session.exec(select(Game.slug).where(col(Game.is_target))).all())
    if targets != TARGET_GAMES:
        return [f"juegos objetivo {sorted(targets)}, se esperaban {sorted(TARGET_GAMES)}"]
    return []


def _types(session: Session, pokemon: str, generation: int) -> list[str]:
    query = (
        select(PokemonType.type)
        .where(PokemonType.pokemon == pokemon, PokemonType.generation == generation)
        .order_by(col(PokemonType.slot))
    )
    return list(session.exec(query).all())


def check_types_by_generation(session: Session) -> list[str]:
    """Known type changes (RN-10)."""
    expected = [
        ("clefairy", 3, ["normal"]),  # Fairy only from the 6th generation
        ("magnemite", 1, ["electric"]),  # Steel only from the 2nd generation
        ("magnemite", 2, ["electric", "steel"]),
        ("bulbasaur", 3, ["grass", "poison"]),
    ]
    problems = []
    for pokemon, generation, types in expected:
        found = _types(session, pokemon, generation)
        if found != types:
            problems.append(
                f"{pokemon} en la generación {generation}: {found}, se esperaba {types}"
            )
    return problems


def check_type_chart(session: Session) -> list[str]:
    """Known type chart changes (RN-10)."""
    expected = [
        (1, "ghost", "psychic", 0),  # 1st generation bug
        (3, "ghost", "psychic", 200),
        (3, "ghost", "steel", 50),  # Steel resists Ghost up to the 5th generation
        (1, "poison", "bug", 200),
    ]
    problems = []
    for generation, attacking, defending, factor in expected:
        found = session.exec(
            select(TypeEfficacy.factor).where(
                TypeEfficacy.generation == generation,
                TypeEfficacy.attacking == attacking,
                TypeEfficacy.defending == defending,
            )
        ).first()
        if found != factor:
            problems.append(
                f"{attacking} contra {defending} en la generación {generation}: {found}, "
                f"se esperaba {factor}"
            )
    return problems


def _steps(session: Session, group: str, origin: str, evolved: str) -> list[EvolutionStep]:
    query = select(EvolutionStep).where(
        EvolutionStep.version_group == group,
        EvolutionStep.from_pokemon == origin,
        EvolutionStep.to_pokemon == evolved,
    )
    return list(session.exec(query).all())


def check_evolutions(session: Session) -> list[str]:
    """Known evolution steps (RN-15, RN-20)."""
    problems = []
    if _steps(session, "red-blue", "pichu", "pikachu"):
        problems.append("pichu → pikachu no debería existir en Rojo y Azul")
    expected = [
        ("gold-silver", "pichu", "pikachu", "level-up", "minimum_happiness"),
        ("firered-leafgreen", "haunter", "gengar", "trade", None),
        ("ruby-sapphire", "wurmple", "silcoon", "level-up", "percentage_chance"),
        ("emerald", "nincada", "shedinja", "shed", None),
        ("ruby-sapphire", "feebas", "milotic", "level-up", "minimum_beauty"),
    ]
    for group, origin, evolved, trigger, condition in expected:
        steps = _steps(session, group, origin, evolved)
        if [step.trigger for step in steps] != [trigger]:
            problems.append(f"{origin} → {evolved} en {group}: {steps}, se esperaba {trigger}")
        elif condition is not None and condition not in steps[0].conditions:
            problems.append(f"{origin} → {evolved} en {group}: falta la condición {condition}")
    return problems


def check_breeding_data(session: Session) -> list[str]:
    """Data that RN-11 needs."""
    problems = []
    mewtwo = session.get(Species, "mewtwo")
    if mewtwo is None or not mewtwo.is_legendary:
        problems.append("mewtwo debería ser legendario")
    ditto = session.exec(
        select(SpeciesEggGroup.egg_group).where(SpeciesEggGroup.species == "ditto")
    ).all()
    if list(ditto) != ["ditto"]:
        problems.append(f"ditto: grupos huevo {list(ditto)}, se esperaba ['ditto']")
    return problems


FIRST_LOAD_CHECKS: Sequence[Check] = (
    check_counts,
    check_target_games,
    check_types_by_generation,
    check_type_chart,
    check_evolutions,
    check_breeding_data,
)
