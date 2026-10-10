"""Checks of the first load (CA-11): expected counts and known cases.

They run on the freshly built database, before it replaces the previous one. A failed check
means the data is not what the load design expects (for example, because the PokeAPI
schema changed), so the load is rejected. See docs/02-ddt/carga-datos.md, section
"Comprobaciones de la carga".
"""

from collections.abc import Callable, Sequence

from sqlalchemy import func
from sqlmodel import Session, col, select

from db.reference import (
    Encounter,
    EventPokemon,
    EvolutionStep,
    Game,
    GameMechanic,
    GamePokedex,
    GamePokemon,
    GameStarter,
    GameTransfer,
    Generation,
    KeyBattle,
    KeyBattlePokemon,
    Location,
    Origin,
    Pokedex,
    PokedexNumber,
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
KEY_BATTLES_PER_GAME = 13
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
    GameStarter: len(TARGET_GAMES) * 3 + 5 * 3 + 1,  # and the 1st and 2nd gen. (Yellow, 1)
    Pokedex: 4,  # national, kanto, original-johto and hoenn
    GamePokedex: 11,
    GameTransfer: 6 * 5 + 5 * 4,  # every ordered pair within the 1st-2nd and the 3rd gen.
    EventPokemon: 3 * 1 + 3 * 2 + 5 * 4,
}
SPECIES_BY_POKEDEX = {"national": SPECIES_COUNT, "kanto": 151, "original-johto": 251, "hoenn": 202}
# Encounter methods of the loaded games. ``core/`` classifies each of them (RN-26): a new one
# upstream must be reviewed before it is loaded.
ENCOUNTER_METHODS = frozenset(
    {
        "walk",
        "surf",
        "seaweed",
        "old-rod",
        "good-rod",
        "super-rod",
        "feebas-tile-fishing",
        "rock-smash",
        "headbutt-low",
        "headbutt-normal",
        "headbutt-high",
        "gift",
        "gift-egg",
        "npc-trade",
        "static",
        "pokeflute",
        "squirt-bottle",
        "wailmer-pail",
        "devon-scope",
        "roaming-grass",
        "roaming-water",
        "colosseum-bonus-disc-us",
        "colosseum-bonus-disc-jpn",
        "pokemon-channel-pal",
    }
)
# 15 types in the 1st generation, 17 from the 2nd: one factor per pair.
EFFICACY_PAIRS_BY_GENERATION = {1: 15 * 15, 2: 17 * 17, 3: 17 * 17}


def check_counts(session: Session) -> list[str]:
    problems = []
    for model, expected in EXPECTED_COUNTS.items():
        count = session.exec(select(func.count()).select_from(model)).one()
        if count != expected:
            problems.append(f"{model.__tablename__}: {count} filas, se esperaban {expected}")
    for pokedex, expected in SPECIES_BY_POKEDEX.items():
        query = select(func.count()).select_from(PokedexNumber)
        count = session.exec(query.where(PokedexNumber.pokedex == pokedex)).one()
        if count != expected:
            problems.append(f"Pokédex {pokedex}: {count} especies, se esperaban {expected}")
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
    """Only the complete games are target games (RF-05, CA-67): those with curated data."""
    targets = set(session.exec(select(Game.slug).where(col(Game.is_target))).all())
    if targets != CURATED_GAMES:
        return [f"juegos objetivo {sorted(targets)}, se esperaban {sorted(CURATED_GAMES)}"]
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


def check_starters(session: Session) -> list[str]:
    """Starters of every game, each the final evolution of its line there (RN-21, CA-87)."""
    problems = []
    expected = {
        "firered": {"venusaur", "charizard", "blastoise"},
        "emerald": {"sceptile", "blaziken", "swampert"},
        "yellow": {"raichu"},
        "crystal": {"meganium", "typhlosion", "feraligatr"},
    }
    for game, starters in expected.items():
        found = set(session.exec(select(GameStarter.pokemon).where(GameStarter.game == game)))
        if found != starters:
            problems.append(
                f"iniciales de {game}: {sorted(found)}, se esperaban {sorted(starters)}"
            )
    query = (
        select(GameStarter.game, GameStarter.pokemon)
        .distinct()
        .join(Game, col(Game.slug) == GameStarter.game)
        .join(
            EvolutionStep,
            (col(EvolutionStep.version_group) == Game.version_group)
            & (col(EvolutionStep.from_pokemon) == GameStarter.pokemon),
        )
    )
    for game, pokemon in session.exec(query).all():
        problems.append(f"{pokemon} no es una evolución final en {game}: no puede ser inicial")
    return problems


def _team(session: Session, battle: str) -> list[str]:
    query = (
        select(KeyBattlePokemon.pokemon)
        .where(KeyBattlePokemon.battle == battle)
        .order_by(col(KeyBattlePokemon.position))
    )
    return list(session.exec(query).all())


def check_key_battles(session: Session) -> list[str]:
    """Key battles and their teams (RN-17, CA-26, CA-38, CA-39)."""
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
            if battle.origin is not Origin.AUTOMATIC:
                problems.append(f"{battle.slug}: origen {battle.origin}, se esperaba automatic")
        giovanni = [b.category for b in battles if b.trainer_name == "Giovanni"]
        if giovanni != ["gym_leader"]:
            problems.append(f"{game}: Giovanni {giovanni}, se esperaba solo como líder (CA-39)")

    if _team(session, "firered-brock") != ["geodude", "onix"]:
        problems.append(f"equipo de firered-brock: {_team(session, 'firered-brock')}")
    # Without the starter (CA-26) and only what all three variants share (CA-38).
    champion = _team(session, "firered-champion")
    if champion != ["pidgeot", "alakazam", "rhydon"]:
        problems.append(f"equipo de firered-champion: {champion}")
    return problems


def check_pokedexes(session: Session) -> list[str]:
    """The Pokédex of each game (RN-22); their species are counted in ``check_counts``."""
    problems = []
    expected_pokedex = {"red": "kanto", "crystal": "original-johto", "firered": "national"}
    for game, pokedex in expected_pokedex.items():
        found = list(session.exec(select(GamePokedex.pokedex).where(GamePokedex.game == game)))
        if found != [pokedex]:
            problems.append(f"Pokédex de {game}: {found}, se esperaba {pokedex}")
    return problems


def _methods(session: Session, game: str, pokemon: str) -> set[tuple[str, tuple[str, ...]]]:
    query = select(Encounter.method, Encounter.conditions).where(
        Encounter.game == game, Encounter.pokemon == pokemon
    )
    return {(method, tuple(conditions)) for method, conditions in session.exec(query).all()}


def check_encounters(session: Session) -> list[str]:
    """Known ways of obtaining Pokémon (RN-26, plan of the Pokédex) and known methods."""
    problems = []
    methods = set(session.exec(select(Encounter.method).distinct()).all())
    if unknown := sorted(methods - ENCOUNTER_METHODS):
        problems.append(f"métodos de aparición sin clasificar: {unknown}")
    expected = [
        ("firered", "eevee", ("gift", ())),
        ("firered", "lapras", ("gift", ())),
        ("firered", "lapras", ("surf", ())),
        ("firered", "hitmonlee", ("gift", ())),
        ("firered", "omanyte", ("gift", ("item-helix-fossil",))),
        ("firered", "aerodactyl", ("gift", ("item-old-amber",))),
        ("firered", "snorlax", ("pokeflute", ())),
        ("firered", "zapdos", ("static", ())),
        (
            "firered",
            "raikou",
            ("roaming-grass", ("starter-squirtle", "story-progress-beat-elite-four-round-two")),
        ),
        ("firered", "ekans", ("walk", ())),
        ("gold", "suicune", ("roaming-grass", ("story-progress-awakened-beasts",))),
        ("gold", "togepi", ("gift-egg", ())),
    ]
    for game, pokemon, method in expected:
        if method not in _methods(session, game, pokemon):
            problems.append(f"{pokemon} en {game}: falta {method}")
    for game, pokemon in [("firered", "sandshrew"), ("firered", "mew")]:
        if found := _methods(session, game, pokemon):
            problems.append(f"{pokemon} no debería aparecer en {game}: {sorted(found)}")
    if session.get(EventPokemon, ("firered", "mew")) is None:
        problems.append("mew debería ser de evento en firered")
    navel_rock = session.get(Location, "navel-rock")
    if navel_rock is None or navel_rock.event_item != "mysticticket":
        problems.append("a navel-rock solo se debería llegar con el mysticticket")
    return problems


def check_transfers(session: Session) -> list[str]:
    """Transfers between games (RN-25)."""
    expected = {
        ("red", "gold"): 1,  # Time Capsule
        ("gold", "silver"): None,
        ("firered", "ruby"): None,
    }
    problems = []
    for pair, limit in expected.items():
        transfer = session.get(GameTransfer, pair)
        if transfer is None or transfer.max_species_generation != limit:
            problems.append(f"transferencia {pair}: {transfer}, se esperaba el límite {limit}")
    if session.get(GameTransfer, ("crystal", "emerald")) is not None:
        problems.append("de la 2.ª generación a la 3.ª no se puede transferir")
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
    check_starters,
    check_key_battles,
    check_pokedexes,
    check_encounters,
    check_transfers,
)
