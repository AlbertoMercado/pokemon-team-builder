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
    GameMechanic,
    GamePokemon,
    Generation,
    KeyBattle,
    KeyBattlePokemon,
    Origin,
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
# Games with curated data so far (phase 4): mechanics, arrival rule and key battles.
CURATED_GAMES = frozenset({"firered", "leafgreen"})
KEY_BATTLES_PER_GAME = 15
RIVAL_TEAM_SIZE = 5  # the champion's 6 Pokémon minus the starter (CA-26)
SPECIES_COUNT = 386
EXPECTED_COUNTS: dict[type[ReferenceModel], int] = {
    Generation: 3,
    VersionGroup: 7,
    Game: 11,
    Type: 17,
    Species: SPECIES_COUNT,
    Pokemon: SPECIES_COUNT,
    GamePokemon: len(TARGET_GAMES) * SPECIES_COUNT,
    GameMechanic: len(CURATED_GAMES) * 2,  # day_night_cycle and contests
    KeyBattle: len(CURATED_GAMES) * KEY_BATTLES_PER_GAME,
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


def check_incense_babies(session: Session) -> list[str]:
    """Babies that only hatch with an incense (CA-36)."""
    marked = set(session.exec(select(Species.slug).where(col(Species.requires_incense))).all())
    if marked != {"azurill", "wynaut"}:
        return [f"bebés de incienso {sorted(marked)}, se esperaban ['azurill', 'wynaut']"]
    return []


def check_arrival_proposals(session: Session) -> list[str]:
    """Arrival proposals (CA-28): inferred where there is a rule, pending elsewhere."""
    problems = []
    for game in TARGET_GAMES:
        expected = Origin.INFERRED if game in CURATED_GAMES else Origin.PENDING
        query = select(func.count()).select_from(GamePokemon)
        wrong = session.exec(
            query.where(GamePokemon.game == game, GamePokemon.arrival_origin != expected)
        ).one()
        if wrong:
            problems.append(f"{game}: {wrong} propuestas de llegada no son {expected.value}")
    expected_arrival = {
        "bulbasaur": True,
        "vaporeon": True,
        "golbat": True,
        "chansey": True,  # Happiny is not loaded: Chansey hatches as Chansey
        "raichu": False,  # hatches as Pichu, not in the Kanto Pokédex
        "pikachu": False,
        "clefairy": False,  # hatches as Cleffa
        "crobat": False,  # 2nd generation evolution
        "espeon": False,
        "blissey": False,
    }
    for pokemon, can_arrive in expected_arrival.items():
        row = session.get(GamePokemon, ("firered", pokemon))
        if row is None or row.can_arrive is not can_arrive:
            found = None if row is None else row.can_arrive
            problems.append(f"llegada de {pokemon} a firered: {found}, se esperaba {can_arrive}")
    return problems


def _team(session: Session, battle: str, variant: int = 1) -> list[str]:
    query = (
        select(KeyBattlePokemon.pokemon)
        .where(KeyBattlePokemon.battle == battle, KeyBattlePokemon.variant == variant)
        .order_by(col(KeyBattlePokemon.position))
    )
    return list(session.exec(query).all())


def check_key_battles(session: Session) -> list[str]:
    """Key battles and their teams (RN-17, CA-26)."""
    problems = []
    for game in CURATED_GAMES:
        battles = session.exec(
            select(KeyBattle).where(KeyBattle.game == game).order_by(col(KeyBattle.order))
        ).all()
        first, last = (battles[0].trainer_name, battles[-1].trainer_name) if battles else ("", "")
        if (first, last) != ("Brock", "Azul"):
            problems.append(f"{game}: combates de {first!r} a {last!r}, se esperaba Brock y Azul")
        for battle in battles:
            if not _team(session, battle.slug):
                problems.append(f"{battle.slug}: no tiene Pokémon")
            expected = Origin.INFERRED if battle.category == "champion" else Origin.AUTOMATIC
            if battle.origin is not expected:
                problems.append(f"{battle.slug}: origen {battle.origin}, se esperaba {expected}")

    if _team(session, "firered-brock") != ["geodude", "onix"]:
        problems.append(f"equipo de firered-brock: {_team(session, 'firered-brock')}")
    starters = {"venusaur", "charizard", "blastoise", "ivysaur", "charmeleon", "wartortle"}
    for variant in (1, 2, 3):
        team = _team(session, "firered-champion", variant)
        if len(team) != RIVAL_TEAM_SIZE or starters & set(team):
            problems.append(f"firered-champion, variante {variant}: {team}")
    return problems


FIRST_LOAD_CHECKS: Sequence[Check] = (
    check_counts,
    check_target_games,
    check_types_by_generation,
    check_type_chart,
    check_evolutions,
    check_breeding_data,
    check_incense_babies,
    check_arrival_proposals,
    check_key_battles,
)
