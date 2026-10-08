"""PokeAPI source of the ingest, on a real extract of the pinned CSV dump (no network).

The rules checked here are described in docs/02-ddt/carga-datos.md, section
"Cómo se interpreta el volcado de PokeAPI".
"""

import csv
import dataclasses
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlmodel import Session, col, select

from db.reference import (
    Encounter,
    EvolutionStep,
    Game,
    GamePokemon,
    GameStarter,
    Location,
    Origin,
    Pokedex,
    PokedexNumber,
    Pokemon,
    PokemonType,
    Species,
    SpeciesEggGroup,
    Type,
    TypeEfficacy,
)
from db.sqlite import create_sqlite_engine
from ingest.checks import (
    FIRST_LOAD_CHECKS,
    check_counts,
    check_key_battles,
    check_starters,
    check_target_games,
)
from ingest.load import build_reference
from ingest.sources.curated import (
    CuratedData,
    CuratedDataError,
    CuratedSource,
    read_curated,
    read_pinned_commits,
)
from ingest.sources.curated.schemas import (
    ArrivalFile,
    ArrivalRule,
    LocationEntry,
    LocationsFile,
    StartersFile,
)
from ingest.sources.pokeapi import PokeapiCsvSource
from ingest.sources.pokeapi.download import CsvCache, MissingCsvError
from ingest.sources.pokeapi.rows import CsvSchemaError
from ingest.sources.pokeapi.transform import TransformError

COMMIT = "bc92d3b6029ef1abe9e7ad424c400b338f3c11fe"
SPRITES_COMMIT = "8491ffde1b247e4de574d4bb8e24b7bd9fa876fa"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "pokeapi"
REPOSITORY = Path(__file__).resolve().parents[2]
REPOSITORY_CURATED = read_curated(REPOSITORY / "data" / "curated")
with (FIXTURES / COMMIT / "locations.csv").open(encoding="utf-8") as _file:
    EXTRACT_LOCATIONS = {row["identifier"] for row in csv.DictReader(_file)}
# Of the starters, the extract only has Venusaur, and only some of the curated locations.
CURATED = dataclasses.replace(
    REPOSITORY_CURATED,
    starters=StartersFile(games={"firered": ["venusaur"]}),
    locations=LocationsFile(
        locations={
            slug: entry
            for slug, entry in REPOSITORY_CURATED.locations.locations.items()
            if slug in EXTRACT_LOCATIONS
        }
    ),
)


def _offline_source(cache_dir: Path = FIXTURES, curated: CuratedData = CURATED) -> PokeapiCsvSource:
    return PokeapiCsvSource(CsvCache(cache_dir, COMMIT, downloader=None), curated)


@pytest.fixture(scope="module")
def loaded(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Session]:
    """Database built from the extract, shared by the read-only tests of this module."""
    target = tmp_path_factory.mktemp("pokeapi") / "reference.sqlite"
    report = build_reference([_offline_source(), CuratedSource(CURATED)], target)
    assert report.succeeded, report.errors
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _types(session: Session, pokemon: str, generation: int) -> list[str]:
    query = (
        select(PokemonType.type)
        .where(PokemonType.pokemon == pokemon, PokemonType.generation == generation)
        .order_by(col(PokemonType.slot))
    )
    return list(session.exec(query).all())


def _factor(session: Session, generation: int, attacking: str, defending: str) -> int | None:
    return session.exec(
        select(TypeEfficacy.factor).where(
            TypeEfficacy.generation == generation,
            TypeEfficacy.attacking == attacking,
            TypeEfficacy.defending == defending,
        )
    ).first()


def _steps(session: Session, group: str, evolved: str) -> list[EvolutionStep]:
    query = select(EvolutionStep).where(
        EvolutionStep.version_group == group, EvolutionStep.to_pokemon == evolved
    )
    return list(session.exec(query).all())


# --- Pinned commit and cache ---------------------------------------------------------------


def test_repository_pins_full_commits() -> None:
    commits = read_pinned_commits(REPOSITORY / "data" / "curated" / "pokeapi.yaml")
    assert commits.commit == COMMIT
    assert commits.sprites_commit == SPRITES_COMMIT


def test_invalid_pinned_commit_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "pokeapi.yaml"
    path.write_text(f"commit: bc92d3b\nsprites_commit: {SPRITES_COMMIT}\n", encoding="utf-8")
    with pytest.raises(CuratedDataError):  # abbreviated SHA
        read_pinned_commits(path)


def test_missing_sprites_commit_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "pokeapi.yaml"
    path.write_text(f"commit: {COMMIT}\n", encoding="utf-8")
    with pytest.raises(CuratedDataError, match="sprites_commit"):
        read_pinned_commits(path)


def test_cache_downloads_once_and_reuses_the_file(tmp_path: Path) -> None:
    requested: list[str] = []

    def fake_download(url: str) -> bytes:
        requested.append(url)
        return b"id,identifier\n1,generation-i\n"

    cache = CsvCache(tmp_path, COMMIT, fake_download)
    first = cache.path("generations")
    second = cache.path("generations")

    assert first == second == tmp_path / COMMIT / "generations.csv"
    assert first.read_text(encoding="utf-8").startswith("id,identifier")
    assert requested == [
        f"https://raw.githubusercontent.com/PokeAPI/pokeapi/{COMMIT}/data/v2/csv/generations.csv"
    ]


def test_offline_cache_fails_on_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(MissingCsvError, match=r"generations\.csv"):
        CsvCache(tmp_path, COMMIT, downloader=None).path("generations")


# --- Schema validation ---------------------------------------------------------------------


def _copy_fixtures(tmp_path: Path) -> Path:
    shutil.copytree(FIXTURES / COMMIT, tmp_path / COMMIT)
    return tmp_path / COMMIT


def test_missing_column_fails_the_load(tmp_path: Path) -> None:
    species = _copy_fixtures(tmp_path) / "pokemon_species.csv"
    lines = species.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace("is_legendary", "legendary")
    species.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(CsvSchemaError, match="is_legendary"):
        _offline_source(tmp_path).read_tables()


def test_unknown_evolution_condition_fails_the_load(tmp_path: Path) -> None:
    """A new kind of condition must be reviewed for RN-15 and RN-20 before loading it."""
    evolution = _copy_fixtures(tmp_path) / "pokemon_evolution.csv"
    lines = evolution.read_text(encoding="utf-8").splitlines()
    lines = [lines[0] + ",needs_full_moon", *(line + ",1" for line in lines[1:])]
    evolution.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(CsvSchemaError, match="needs_full_moon"):
        _offline_source(tmp_path).read_tables()


# --- Games ---------------------------------------------------------------------------------


def test_loads_the_games_of_the_first_three_generations(loaded: Session) -> None:
    games = {game.slug: game for game in loaded.exec(select(Game)).all()}

    assert len(games) == 11  # without Colosseum, XD and the Japan-only versions
    assert games["firered"].name_es == "Rojo Fuego"
    # The extract has no key battles: no game is complete, so none is a target (CA-67).
    assert not any(game.is_target for game in games.values())
    assert {slug for slug, game in games.items() if not game.has_breeding} == {
        "red",
        "blue",
        "yellow",
    }


# --- Species and forms ---------------------------------------------------------------------


def test_only_default_forms_of_loaded_species(loaded: Session) -> None:
    pokemon = set(loaded.exec(select(Pokemon.slug)).all())

    assert "deoxys-normal" in pokemon
    assert not {"deoxys-attack", "raichu-alola", "slowbro-galar", "happiny"} & pokemon
    assert loaded.exec(select(Pokemon).where(Pokemon.slug == "pikachu")).one().name_es == "Pikachu"


def test_each_form_keeps_its_pokeapi_id(loaded: Session) -> None:
    """The id of the form names its sprite (ADR-0010); it is not always the Pokédex number."""
    ids = dict(loaded.exec(select(Pokemon.slug, Pokemon.pokeapi_id)).all())

    assert ids["pikachu"] == 25
    assert ids["deoxys-normal"] == 386


def test_pre_evolution_of_a_later_generation_is_left_out(loaded: Session) -> None:
    """Happiny is a 4th generation baby: in generations 1 to 3, Chansey is the first stage."""
    chansey = loaded.get(Species, "chansey")
    assert chansey is not None
    assert chansey.evolves_from is None
    blissey = loaded.get(Species, "blissey")
    assert blissey is not None
    assert blissey.evolves_from == "chansey"


def test_breeding_data(loaded: Session) -> None:
    def egg_groups(species: str) -> set[str]:
        query = select(SpeciesEggGroup.egg_group).where(SpeciesEggGroup.species == species)
        return set(loaded.exec(query).all())

    assert egg_groups("ditto") == {"ditto"}
    assert egg_groups("pichu") == {"no-eggs"}
    assert egg_groups("pikachu") == {"ground", "fairy"}
    mewtwo = loaded.get(Species, "mewtwo")
    azurill = loaded.get(Species, "azurill")
    assert mewtwo is not None
    assert mewtwo.is_legendary
    assert azurill is not None
    assert azurill.is_baby
    assert azurill.requires_incense  # from data/curated/breeding.yaml (CA-36)
    pichu = loaded.get(Species, "pichu")
    assert pichu is not None
    assert not pichu.requires_incense


# --- Types (RN-10) -------------------------------------------------------------------------


@pytest.mark.rn("RN-10")
def test_types_are_the_ones_of_each_generation(loaded: Session) -> None:
    assert _types(loaded, "clefairy", 3) == ["normal"]
    assert _types(loaded, "magnemite", 1) == ["electric"]
    assert _types(loaded, "magnemite", 2) == ["electric", "steel"]
    assert _types(loaded, "azurill", 3) == ["normal"]
    assert _types(loaded, "azurill", 2) == []  # it does not exist before the 3rd generation


@pytest.mark.rn("RN-10")
def test_type_chart_is_the_one_of_each_generation(loaded: Session) -> None:
    types_by_generation = {
        generation: loaded.exec(select(Type.slug).where(Type.generation <= generation)).all()
        for generation in (1, 3)
    }
    assert len(types_by_generation[1]) == 15
    assert len(types_by_generation[3]) == 17
    assert _factor(loaded, 1, "ghost", "psychic") == 0
    assert _factor(loaded, 3, "ghost", "psychic") == 200
    assert _factor(loaded, 3, "ghost", "steel") == 50
    assert _factor(loaded, 1, "poison", "bug") == 200
    assert _factor(loaded, 1, "steel", "normal") is None  # Steel does not exist yet


# --- Evolutions (RN-15, RN-20) -------------------------------------------------------------


def test_evolutions_apply_from_the_group_that_introduced_them(loaded: Session) -> None:
    assert _steps(loaded, "red-blue", "pikachu") == []  # Pichu arrives in Gold and Silver
    [pikachu] = _steps(loaded, "gold-silver", "pikachu")
    assert pikachu.from_pokemon == "pichu"
    assert pikachu.conditions == {"minimum_happiness": 220}


def test_regional_evolutions_are_not_loaded(loaded: Session) -> None:
    """Raichu's Alolan rows (Sun and Moon) never apply to generations 1 to 3."""
    [raichu] = _steps(loaded, "firered-leafgreen", "raichu")
    assert raichu.trigger == "use-item"
    assert raichu.conditions == {"trigger_item": "thunder-stone"}


@pytest.mark.rn("RN-15")
def test_tedious_evolution_data_is_kept_as_pokeapi_gives_it(loaded: Session) -> None:
    [gengar] = _steps(loaded, "firered-leafgreen", "gengar")
    [slowking] = _steps(loaded, "firered-leafgreen", "slowking")
    [espeon] = _steps(loaded, "ruby-sapphire", "espeon")
    [hitmontop] = _steps(loaded, "emerald", "hitmontop")
    [milotic] = _steps(loaded, "ruby-sapphire", "milotic")
    [shedinja] = _steps(loaded, "emerald", "shedinja")

    assert (gengar.trigger, gengar.conditions) == ("trade", {})
    assert (slowking.trigger, slowking.conditions) == ("trade", {"held_item": "kings-rock"})
    assert espeon.conditions == {"time_of_day": "day", "minimum_happiness": 160}
    assert hitmontop.conditions == {"minimum_level": 20, "relative_physical_stats": 0}
    assert milotic.conditions == {"minimum_beauty": 170}  # the trade method is from Black
    assert (shedinja.from_pokemon, shedinja.trigger) == ("nincada", "shed")


@pytest.mark.rn("RN-20")
def test_random_evolution_keeps_its_chance(loaded: Session) -> None:
    [silcoon] = _steps(loaded, "firered-leafgreen", "silcoon")
    assert silcoon.conditions["percentage_chance"] == 50
    assert "condition_expression" in silcoon.conditions


# --- Availability (RN-03) ------------------------------------------------------------------


def _arrival(session: Session, game: str, pokemon: str) -> tuple[bool | None, Origin]:
    row = session.get(GamePokemon, (game, pokemon))
    assert row is not None
    return row.can_arrive, row.arrival_origin


@pytest.mark.rn("RN-03")
def test_every_loaded_form_exists_in_every_target_game(loaded: Session) -> None:
    rows = loaded.exec(select(GamePokemon)).all()
    pokemon = loaded.exec(select(Pokemon.slug)).all()

    assert len(rows) == 5 * len(pokemon)
    assert all(row.exists_in_game and row.exists_origin is Origin.AUTOMATIC for row in rows)


@pytest.mark.rn("RN-03")
def test_arrival_is_proposed_from_the_kanto_pokedex_in_firered(loaded: Session) -> None:
    """CA-28: the stage that hatches and every stage up to the favourite are in Kanto."""
    assert _arrival(loaded, "firered", "bulbasaur") == (True, Origin.INFERRED)
    assert _arrival(loaded, "firered", "golbat") == (True, Origin.INFERRED)
    assert _arrival(loaded, "firered", "vaporeon") == (True, Origin.INFERRED)
    # Chansey hatches as Chansey: Happiny (4th generation) is not loaded.
    assert _arrival(loaded, "leafgreen", "chansey") == (True, Origin.INFERRED)
    # Pikachu and Raichu hatch as Pichu, which is not in the Kanto Pokédex.
    assert _arrival(loaded, "firered", "pikachu") == (False, Origin.INFERRED)
    assert _arrival(loaded, "firered", "raichu") == (False, Origin.INFERRED)
    # Crobat, Espeon and Blissey are 2nd generation evolutions.
    assert _arrival(loaded, "firered", "crobat") == (False, Origin.INFERRED)
    assert _arrival(loaded, "firered", "espeon") == (False, Origin.INFERRED)
    assert _arrival(loaded, "firered", "blissey") == (False, Origin.INFERRED)


def test_the_games_of_the_target_generation_are_proposed_as_target() -> None:
    """The source proposes the 3rd generation; the load then keeps the complete ones."""
    games = [row for row in _offline_source().rows() if isinstance(row, Game)]
    assert {game.slug for game in games if game.is_target} == {
        "ruby",
        "sapphire",
        "emerald",
        "firered",
        "leafgreen",
    }


@pytest.mark.rn("RN-03")
def test_arrival_without_rule_stays_pending(loaded: Session) -> None:
    rows = loaded.exec(select(GamePokemon).where(GamePokemon.game == "ruby")).all()
    assert rows
    assert all(row.can_arrive is None and row.arrival_origin is Origin.PENDING for row in rows)


def _with_arrival(game: str, pokedex: str) -> CuratedData:
    rule = ArrivalRule(regional_pokedex=pokedex, origin="inferred")
    return dataclasses.replace(CURATED, arrival=ArrivalFile(games={game: rule}))


@pytest.mark.rn("RN-03")
def test_incense_babies_are_skipped_as_egg_stage(tmp_path: Path) -> None:
    """CA-36: Azumarill hatches as Marill, so Azurill (3rd generation) does not matter.

    With the Johto Pokédex (Marill and Azumarill, not Azurill) as arrival rule, Azumarill
    can arrive, while Azurill itself cannot.
    """
    target = tmp_path / "reference.sqlite"
    source = _offline_source(curated=_with_arrival("ruby", "original-johto"))
    assert build_reference([source], target).succeeded
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        assert _arrival(session, "ruby", "azumarill") == (True, Origin.INFERRED)
        assert _arrival(session, "ruby", "azurill") == (False, Origin.INFERRED)
        assert _arrival(session, "ruby", "wobbuffet") == (True, Origin.INFERRED)
    engine.dispose()


def test_arrival_rule_for_a_game_that_is_not_a_target_fails() -> None:
    source = _offline_source(curated=_with_arrival("red", "kanto"))
    with pytest.raises(TransformError, match="red"):
        list(source.rows())


# --- Pokédexes and encounters (RN-22, RN-26) ----------------------------------------------


def _encounters(session: Session, game: str, pokemon: str) -> list[Encounter]:
    query = select(Encounter).where(Encounter.game == game, Encounter.pokemon == pokemon)
    return list(session.exec(query).all())


@pytest.mark.rn("RN-22")
def test_loads_the_national_pokedex_and_those_of_the_loaded_games(loaded: Session) -> None:
    """RN-22: the Pokédex of each game is one of these, in the order of their numbers."""
    assert set(loaded.exec(select(Pokedex.slug)).all()) == {
        "national",
        "kanto",
        "original-johto",
        "hoenn",
    }
    numbers = {(row.pokedex, row.species): row.number for row in loaded.exec(select(PokedexNumber))}
    assert numbers[("kanto", "mew")] == 151
    assert numbers[("national", "deoxys")] == 386
    assert numbers[("original-johto", "hoothoot")] == 15
    # Only loaded species: no Happiny in the National Pokédex.
    assert ("national", "happiny") not in numbers


@pytest.mark.rn("RN-26")
def test_gifts_fossils_and_roaming_keep_their_pokeapi_method_and_conditions(
    loaded: Session,
) -> None:
    """RN-26: the data to tell a gift, a fossil and a roaming Pokémon apart, as in the plan."""
    [eevee] = _encounters(loaded, "firered", "eevee")
    assert (eevee.method, eevee.location, eevee.area, eevee.rarity) == (
        "gift",
        "celadon-city",
        "celadon-mansion",
        100,
    )
    [omanyte] = _encounters(loaded, "firered", "omanyte")
    assert (omanyte.method, omanyte.conditions) == ("gift", ["item-helix-fossil"])
    # CA-80: which legendary dog roams depends on the starter.
    [raikou] = _encounters(loaded, "firered", "raikou")
    assert raikou.method == "roaming-grass"
    assert raikou.conditions == ["starter-squirtle", "story-progress-beat-elite-four-round-two"]
    assert {e.method for e in _encounters(loaded, "firered", "lapras")} == {"gift", "surf"}
    assert _encounters(loaded, "firered", "sandshrew") == []  # LeafGreen exclusive
    assert _encounters(loaded, "firered", "mew") == []  # event


@pytest.mark.rn("RN-26")
def test_slots_of_the_same_encounter_add_up_their_rarity_and_levels(loaded: Session) -> None:
    """RN-26 shows the probability in each zone: Ekans in Route 4 of FireRed has four slots,
    10 + 10 + 4 + 1 %, levels 6 to 12."""
    [route_4] = [
        e for e in _encounters(loaded, "firered", "ekans") if e.location == "kanto-route-4"
    ]
    assert (route_4.method, route_4.area, route_4.conditions) == ("walk", None, [])
    assert (route_4.rarity, route_4.min_level, route_4.max_level) == (25, 6, 12)


@pytest.mark.rn("RN-26")
def test_joined_rarity_is_capped_at_one_hundred(loaded: Session) -> None:
    """RN-26: several static Voltorb in the Power Plant of Yellow make one sure encounter."""
    static = [e for e in _encounters(loaded, "yellow", "voltorb") if e.method == "static"]
    assert static
    assert all(e.rarity == 100 for e in static)


@pytest.mark.rn("RN-26")
def test_each_time_of_day_is_its_own_encounter(loaded: Session) -> None:
    """RN-26, CA-81: in the 2nd generation the probability can change with the time."""
    times = {
        tuple(e.conditions) for e in _encounters(loaded, "gold", "hoothoot") if e.method == "walk"
    }
    assert ("time-night",) in times
    assert ("time-day",) not in times  # Hoothoot only comes out at night


@pytest.mark.rn("RN-25")
def test_spin_off_methods_are_loaded_for_core_to_omit(loaded: Session) -> None:
    """RN-25: Jirachi only comes from spin-offs in Ruby, which core/ tells from its methods."""
    methods = {e.method for e in _encounters(loaded, "ruby", "jirachi")}
    assert methods == {"colosseum-bonus-disc-us", "pokemon-channel-pal"}


def test_locations_are_named_from_pokeapi_or_the_curated_data(loaded: Session) -> None:
    route_4 = loaded.get(Location, "kanto-route-4")
    assert route_4 is not None
    assert (route_4.name_es, route_4.name_en) == ("Ruta 4", "Route 4")  # curated
    route_119 = loaded.get(Location, "hoenn-route-119")
    assert route_119 is not None
    assert route_119.name_es == "Ruta 119"  # from PokeAPI
    navel_rock = loaded.get(Location, "navel-rock")
    assert navel_rock is not None
    assert (navel_rock.name_es, navel_rock.event_item) == ("Roca Ombligo", "mysticticket")


def _with_locations(**entries: LocationEntry) -> CuratedData:
    return dataclasses.replace(CURATED, locations=LocationsFile(locations=entries))


def test_location_without_spanish_name_is_loaded_with_a_warning(tmp_path: Path) -> None:
    target = tmp_path / "reference.sqlite"
    source = _offline_source(curated=_with_locations())

    report = build_reference([source, CuratedSource(CURATED)], target)

    assert report.succeeded, report.errors
    [warning] = [w for w in report.warnings if "sin nombre en español" in w]
    assert warning.startswith("110 lugares sin nombre en español")
    assert "azalea-town" in warning
    engine = create_sqlite_engine(target)
    with Session(engine) as session:
        route_4 = session.get(Location, "kanto-route-4")
        assert route_4 is not None
        assert (route_4.name_es, route_4.name_en) == (None, "Route 4")
    engine.dispose()


@pytest.mark.parametrize(
    ("entries", "message"),
    [
        ({"atlantis": LocationEntry(name_es="Atlántida")}, "atlantis"),
        ({"hoenn-route-119": LocationEntry(name_es="Ruta 119")}, "ya tiene nombre"),
        ({"navel-rock": LocationEntry(event_item="golden-ticket")}, "golden-ticket"),
    ],
)
def test_wrong_curated_locations_fail(entries: dict[str, LocationEntry], message: str) -> None:
    source = _offline_source(curated=_with_locations(**entries))
    with pytest.raises(TransformError, match=message):
        list(source.rows())


# --- Checks of the first load --------------------------------------------------------------


def test_first_load_checks_reject_an_incomplete_load(tmp_path: Path) -> None:
    """The extract has ~70 species, not 386: the counts check rejects it."""
    target = tmp_path / "reference.sqlite"

    report = build_reference([_offline_source()], target, FIRST_LOAD_CHECKS)

    assert not report.succeeded
    assert any("species" in error and "386" in error for error in report.errors)
    assert not target.exists()


def test_known_case_checks_pass_on_the_extract(loaded: Session) -> None:
    """Every problem of the extract is a count, a key battle (it has no WikiDex teams), a
    missing starter (it only has Venusaur) or, for lack of key battles, a target game."""
    problems = [problem for check in FIRST_LOAD_CHECKS for problem in check(loaded)]
    assert problems
    expected = check_counts(loaded) + check_key_battles(loaded) + check_starters(loaded)
    expected += check_target_games(loaded)
    assert set(problems) <= set(expected)


@pytest.mark.rn("RN-21")
def test_starters_check_requires_a_final_evolution(loaded: Session) -> None:
    """CA-59: a starter is the final evolution of its line, so Ivysaur cannot be one."""
    loaded.add(GameStarter(game="firered", pokemon="ivysaur"))
    loaded.flush()
    try:
        problems = check_starters(loaded)
    finally:
        loaded.rollback()

    assert "ivysaur no es una evolución final en firered: no puede ser inicial" in problems
    assert not any(problem.startswith("venusaur no es") for problem in problems)
