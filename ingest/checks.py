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
    CatalogGame,
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
    MissingData,
    Origin,
    Platform,
    Playability,
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

GEN_3_GAMES = frozenset({"ruby", "sapphire", "emerald", "firered", "leafgreen"})
GEN_4_GAMES = frozenset({"diamond", "pearl", "platinum", "heartgold", "soulsilver"})
# Games of the target generations (scope): they have existence and arrival rows (RN-03).
TARGET_GENERATION_GAMES = GEN_3_GAMES | GEN_4_GAMES
# Games with curated data: mechanics, arrival rule and key battles (RF-05).
CURATED_GAMES = TARGET_GENERATION_GAMES
# Key battles of each game (RN-17): 8 gyms, the Elite Four and the Champion; in Hoenn, the
# villain boss of the version (both in Emerald) and Wally (CA-88, CA-89). First and last.
KEY_BATTLES = {
    "firered": (13, "Brock", "Azul"),
    "leafgreen": (13, "Brock", "Azul"),
    "ruby": (15, "Petra", "Máximo"),
    "sapphire": (15, "Petra", "Máximo"),
    "emerald": (16, "Petra", "Plubio"),
    # In Sinnoh, the villain boss and Barry (CA-88, CA-89).
    "diamond": (15, "Roco", "Cintia"),
    "pearl": (15, "Roco", "Cintia"),
    "platinum": (15, "Roco", "Cintia"),
    # In Johto, Archer and Silver; nothing of Kanto (CA-95, CA-96).
    "heartgold": (15, "Pegaso", "Lance"),
    "soulsilver": (15, "Pegaso", "Lance"),
}
SPECIES_COUNT = 493
# Species up to each generation: a game has those of its generation and earlier (RN-03).
SPECIES_UP_TO = {3: 386, 4: SPECIES_COUNT}
EXPECTED_COUNTS: dict[type[ReferenceModel], int] = {
    Generation: 4,
    VersionGroup: 10,
    Game: 16,
    Type: 17,
    Species: SPECIES_COUNT,
    Pokemon: SPECIES_COUNT,
    GamePokemon: len(GEN_3_GAMES) * SPECIES_UP_TO[3] + len(GEN_4_GAMES) * SPECIES_UP_TO[4],
    # day_night_cycle and contests; from the 4th generation, also evolution_places (CA-97)
    GameMechanic: len(GEN_3_GAMES) * 2 + len(GEN_4_GAMES) * 3,
    KeyBattle: sum(count for count, _first, _last in KEY_BATTLES.values()),
    # Three per game of the 2nd to 4th generations and of Red and Blue; Pikachu in Yellow.
    GameStarter: (3 + len(TARGET_GENERATION_GAMES) + 2) * 3 + 1,
    # national, kanto, original-johto, hoenn, original-sinnoh, extended-sinnoh, updated-johto
    Pokedex: 7,
    GamePokedex: 16,
    # Every ordered pair within the 1st-2nd, the 3rd and the 4th generation; the Pal Park, from
    # each game of the 3rd to each of the 4th.
    GameTransfer: 6 * 5 + 5 * 4 + 5 * 4 + 5 * 5,
    EventPokemon: 3 * 1 + 3 * 2 + 5 * 4 + 3 * 5 + 2 * 8,
    CatalogGame: 36,  # CA-90
}
SPECIES_BY_POKEDEX = {
    "national": SPECIES_COUNT,
    "kanto": 151,
    "original-johto": 251,
    "hoenn": 202,
    "original-sinnoh": 151,
    "extended-sinnoh": 210,
    "updated-johto": 256,
}
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
        "headbutt",
        "honey-tree",
        "pokemon-ranger",
    }
)
# Known arrivals before completing each game (CA-28).
EXPECTED_ARRIVAL = (
    # FireRed: only the Kanto Pokédex, and no evolution to a later species.
    ("firered", "bulbasaur", True),
    ("firered", "vaporeon", True),
    ("firered", "golbat", True),
    ("firered", "chansey", True),  # Happiny is of the 4th generation: Chansey hatches
    ("firered", "raichu", False),  # hatches as Pichu, not in the Kanto Pokédex
    ("firered", "pikachu", False),
    ("firered", "clefairy", False),  # hatches as Cleffa
    ("firered", "crobat", False),  # 2nd generation evolution
    ("firered", "espeon", False),
    ("firered", "blissey", False),
    # Ruby: any species can be received, and evolutions are not restricted.
    ("ruby", "bulbasaur", True),
    ("ruby", "raichu", True),
    ("ruby", "crobat", True),
    ("ruby", "treecko", True),
    # Emerald: only the Hoenn Pokédex.
    ("emerald", "treecko", True),
    ("emerald", "raichu", True),  # Pichu is in the Hoenn Pokédex
    ("emerald", "crobat", True),
    ("emerald", "bulbasaur", False),
    ("emerald", "chikorita", False),
    # Diamond, Pearl and Platinum: any species, and evolutions are not restricted.
    ("diamond", "bulbasaur", True),
    ("platinum", "garchomp", True),
    ("platinum", "crobat", True),
    # HeartGold and SoulSilver: the same.
    ("heartgold", "garchomp", True),
    ("soulsilver", "bulbasaur", True),
)
# 15 types in the 1st generation, 17 from the 2nd: one factor per pair.
EFFICACY_PAIRS_BY_GENERATION = {1: 15 * 15, 2: 17 * 17, 3: 17 * 17, 4: 17 * 17}


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
    expected = {"azurill", "wynaut", "budew", "chingling", "bonsly", "mime-jr", "happiny"}
    expected |= {"munchlax", "mantyke"}
    if marked != expected:
        return [f"bebés de incienso {sorted(marked)}, se esperaban {sorted(expected)}"]
    return []


def check_arrival_proposals(session: Session) -> list[str]:
    """Arrival proposals (CA-28): inferred in every game with an arrival rule and pending in the
    rest, with known cases of the rule of each one (docs/02-ddt/datos-requeridos.md,
    "Restricciones de llegada por juego")."""
    problems = []
    for game in CURATED_GAMES:
        query = select(func.count()).select_from(GamePokemon)
        wrong = session.exec(
            query.where(GamePokemon.game == game, GamePokemon.arrival_origin != Origin.INFERRED)
        ).one()
        if wrong:
            problems.append(f"{game}: {wrong} propuestas de llegada no son inferidas")
    for game in TARGET_GENERATION_GAMES - CURATED_GAMES:
        query = select(func.count()).select_from(GamePokemon)
        wrong = session.exec(
            query.where(GamePokemon.game == game, GamePokemon.arrival_origin != Origin.PENDING)
        ).one()
        if wrong:
            problems.append(f"{game}: {wrong} propuestas de llegada sin regla de llegada")
    for game, pokemon, can_arrive in EXPECTED_ARRIVAL:
        row = session.get(GamePokemon, (game, pokemon))
        if row is None or row.can_arrive is not can_arrive:
            found = None if row is None else row.can_arrive
            problems.append(f"llegada de {pokemon} a {game}: {found}, se esperaba {can_arrive}")
    return problems


def check_starters(session: Session) -> list[str]:
    """Starters of every game, each the final evolution of its line there (RN-21, CA-87)."""
    problems = []
    expected = {
        "firered": {"venusaur", "charizard", "blastoise"},
        "emerald": {"sceptile", "blaziken", "swampert"},
        "yellow": {"raichu"},
        "crystal": {"meganium", "typhlosion", "feraligatr"},
        "platinum": {"torterra", "infernape", "empoleon"},
        "heartgold": {"meganium", "typhlosion", "feraligatr"},
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
    """Key battles and their teams (RN-17, CA-26, CA-38, CA-39, CA-88, CA-89)."""
    problems = []
    for game, (count, first, last) in KEY_BATTLES.items():
        battles = session.exec(
            select(KeyBattle).where(KeyBattle.game == game).order_by(col(KeyBattle.order))
        ).all()
        found = (battles[0].trainer_name, battles[-1].trainer_name) if battles else ("", "")
        if (len(battles), *found) != (count, first, last):
            problems.append(
                f"{game}: {len(battles)} combates, de {found[0]!r} a {found[1]!r}; se esperaban "
                f"{count}, de {first!r} a {last!r}"
            )
        if [battle.order for battle in battles] != list(range(1, len(battles) + 1)):
            problems.append(f"{game}: los combates no van numerados del 1 en adelante")
        for battle in battles:
            if not _team(session, battle.slug):
                problems.append(f"{battle.slug}: no tiene Pokémon")
            if battle.origin is not Origin.AUTOMATIC:
                problems.append(f"{battle.slug}: origen {battle.origin}, se esperaba automatic")
    for game in ("firered", "leafgreen"):
        query = select(KeyBattle.category).where(
            KeyBattle.game == game, KeyBattle.trainer_name == "Giovanni"
        )
        giovanni = list(session.exec(query).all())
        if giovanni != ["gym_leader"]:
            problems.append(f"{game}: Giovanni {giovanni}, se esperaba solo como líder (CA-39)")

    expected_teams = {
        "firered-brock": ["geodude", "onix"],
        # Without the starter (CA-26) and only what all three variants share (CA-38).
        "firered-champion": ["pidgeot", "alakazam", "rhydon"],
        "ruby-roxanne": ["geodude", "nosepass"],
        "emerald-roxanne": ["geodude", "geodude", "nosepass"],
        # The last mandatory battle of each villain boss (CA-88) and of Wally (CA-89).
        "ruby-maxie": ["mightyena", "crobat", "camerupt"],
        "sapphire-archie": ["mightyena", "crobat", "sharpedo"],
        "emerald-wally": ["altaria", "delcatty", "magneton", "roselia", "gardevoir"],
        "diamond-cyrus": ["honchkrow", "gyarados", "crobat", "weavile"],
        "platinum-fantina": ["duskull", "haunter", "mismagius"],  # Platinum has its own teams
        "platinum-barry": ["staraptor", "heracross", "snorlax"],
        "heartgold-archer": ["houndour", "koffing", "houndoom"],  # CA-95
        # The gym battle, not the rematch of the next subsection.
        "heartgold-clair": ["gyarados", "dragonair", "dragonair", "kingdra"],
    }
    for slug, team in expected_teams.items():
        if _team(session, slug) != team:
            problems.append(f"equipo de {slug}: {_team(session, slug)}, se esperaba {team}")
    for slug in ("ruby-archie", "sapphire-maxie"):  # each version has its own boss
        if session.get(KeyBattle, slug) is not None:
            problems.append(f"{slug} no debería existir")
    return problems


def check_pokedexes(session: Session) -> list[str]:
    """The Pokédex of each game (RN-22); their species are counted in ``check_counts``."""
    problems = []
    expected_pokedex = {
        "red": "kanto",
        "crystal": "original-johto",
        "firered": "national",
        "platinum": "national",
        "soulsilver": "national",
    }
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
        ("diamond", "munchlax", ("honey-tree", ("honey-tree-group-c",))),
        ("diamond", "darkrai", ("static", ())),
        ("diamond", "turtwig", ("gift", ())),
    ]
    for game, pokemon, method in expected:
        if method not in _methods(session, game, pokemon):
            problems.append(f"{pokemon} en {game}: falta {method}")
    for game, pokemon in [("firered", "sandshrew"), ("firered", "mew")]:
        if found := _methods(session, game, pokemon):
            problems.append(f"{pokemon} no debería aparecer en {game}: {sorted(found)}")
    if session.get(EventPokemon, ("firered", "mew")) is None:
        problems.append("mew debería ser de evento en firered")
    for slug, item in (("navel-rock", "mysticticket"), ("newmoon-island", "member-card")):
        location = session.get(Location, slug)
        if location is None or location.event_item != item:
            problems.append(f"a {slug} solo se debería llegar con el {item}")
    return problems


def check_transfers(session: Session) -> list[str]:
    """Transfers between games (RN-25)."""
    expected = {
        ("red", "gold"): 1,  # Time Capsule
        ("gold", "silver"): None,
        ("firered", "ruby"): None,
        ("diamond", "soulsilver"): None,
        ("emerald", "platinum"): None,  # Pal Park
    }
    problems = []
    for pair, limit in expected.items():
        transfer = session.get(GameTransfer, pair)
        if transfer is None or transfer.max_species_generation != limit:
            problems.append(f"transferencia {pair}: {transfer}, se esperaba el límite {limit}")
    if session.get(GameTransfer, ("crystal", "emerald")) is not None:
        problems.append("de la 2.ª generación a la 3.ª no se puede transferir")
    if session.get(GameTransfer, ("platinum", "emerald")) is not None:
        problems.append("de la 4.ª generación a la 3.ª no se puede transferir")
    return problems


def check_catalog(session: Session) -> list[str]:
    """The game catalogue (RF-25, CA-90): every loaded game is in it, and known cases."""
    problems = []
    catalog = {entry.game: entry for entry in session.exec(select(CatalogGame)).all()}
    loaded = set(session.exec(select(Game.slug)).all())
    if outside := sorted(loaded - set(catalog)):
        problems.append(f"juegos cargados que no están en el catálogo: {outside}")
    expected = {
        # game: (name, generation, platform, receives a bred Pokémon, playable, missing)
        "red": ("Rojo", 1, Platform.GAME_BOY, False, Playability.UNKNOWN, None),
        "firered": ("Rojo Fuego", 3, Platform.GAME_BOY_ADVANCE, True, Playability.UNKNOWN, []),
        "emerald": ("Esmeralda", 3, Platform.GAME_BOY_ADVANCE, True, Playability.UNKNOWN, []),
        "diamond": ("Diamante", 4, Platform.DS, True, Playability.UNKNOWN, []),
        "heartgold": ("Oro HeartGold", 4, Platform.DS, True, Playability.UNKNOWN, []),
        # Loaded but not of a target generation: no arrival, mechanics or key battles.
        "gold": (
            "Oro",
            2,
            Platform.GAME_BOY_COLOR,
            True,
            Playability.UNKNOWN,
            [MissingData.POKEMON, MissingData.MECHANICS, MissingData.KEY_BATTLES],
        ),
        "black": (
            "Negro",
            5,
            Platform.DS,
            True,
            Playability.UNKNOWN,
            [MissingData.GENERATION_NOT_LOADED],
        ),
        "legends-za": (
            "Leyendas: Z-A",
            9,
            Platform.SWITCH,
            True,
            Playability.YES,
            [MissingData.GENERATION_NOT_LOADED],
        ),
    }
    for game, (name, generation, platform, bred, playable, missing) in expected.items():
        entry = catalog.get(game)
        if entry is None:
            problems.append(f"{game} no está en el catálogo")
            continue
        found = (entry.name_es, entry.generation, entry.platform, entry.receives_bred)
        if found != (name, generation, platform, bred) or entry.playable_now != playable:
            problems.append(f"{game} en el catálogo: {entry}")
        if missing is not None and list(entry.missing) != missing:
            problems.append(f"a {game} le falta {entry.missing}, se esperaba {missing}")
    if "lets-go-pikachu" in catalog:
        problems.append("Let's Go Pikachu no debería estar en el catálogo (CA-90)")
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
    check_catalog,
)
