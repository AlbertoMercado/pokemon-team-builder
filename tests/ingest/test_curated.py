"""Curated data (data/curated/*.yaml): schemas, the real files and the curated source
(ADR-0005, docs/02-ddt/datos-curados.md)."""

import csv
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from db.reference import (
    BattleCategory,
    EventPokemon,
    EvolutionMethod,
    GameMechanic,
    GamePokedex,
    GameStarter,
    GameTransfer,
    MethodCategory,
    MethodKind,
    Origin,
    TediumReason,
)
from ingest import cli
from ingest.sources.curated import CuratedDataError, CuratedSource, read_curated, transfer_pairs
from ingest.sources.curated.schemas import (
    ArrivalRule,
    BreedingFile,
    EvolutionMethodEntry,
    GamesFile,
    KeyBattlesFile,
    LocationEntry,
    MechanicValue,
    StartersFile,
    TransferGroup,
    TransfersFile,
)
from ingest.sources.pokeapi.transform import condition_keys

CURATED_DIR = Path(__file__).resolve().parents[2] / "data" / "curated"
EVOLUTION_TRIGGERS = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "pokeapi"
    / "bc92d3b6029ef1abe9e7ad424c400b338f3c11fe"
    / "evolution_triggers.csv"
)


def test_repository_curated_files_are_valid() -> None:
    curated = read_curated(CURATED_DIR)

    assert curated.breeding.incense_babies == {"azurill": "sea-incense", "wynaut": "lax-incense"}
    assert set(curated.games.games) == {"firered", "leafgreen"}
    # Every target game has its arrival rule (CA-28).
    assert set(curated.arrival.games) == {"ruby", "sapphire", "emerald", "firered", "leafgreen"}
    assert len(curated.starters.games) == 11  # every loaded game, for the Pokédex (CA-87)
    [firered_leafgreen] = curated.key_battles
    assert firered_leafgreen.games == ["firered", "leafgreen"]
    assert len(firered_leafgreen.battles) == 13  # Giovanni only as gym leader (CA-39)
    assert len(curated.pokedex.games) == 11  # RN-22: every loaded game
    assert curated.locations.locations["navel-rock"].event_item == "mysticticket"


# --- Schemas -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "origin"),
    [(None, "inferred"), (None, "automatic"), (True, "pending")],
)
def test_mechanic_value_is_missing_exactly_when_pending(value: bool | None, origin: str) -> None:
    with pytest.raises(ValidationError, match="pending"):
        MechanicValue.model_validate({"value": value, "origin": origin})


def test_unknown_mechanic_is_rejected() -> None:
    entry = {"value": True, "origin": "inferred"}
    with pytest.raises(ValidationError):
        GamesFile.model_validate({"games": {"firered": {"weather": entry}}})


def test_unknown_keys_are_rejected() -> None:
    """A typo in a curated file must not be silently ignored."""
    with pytest.raises(ValidationError):
        BreedingFile.model_validate({"incense_babies": {}, "incence_babies": {}})


@pytest.mark.parametrize(
    "rule",
    [
        {"origin": "inferred"},  # a proposal needs a Pokédex
        {"regional_pokedex": "kanto", "origin": "pending"},
    ],
)
def test_arrival_rule_pokedex_matches_its_origin(rule: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="pending"):
        ArrivalRule.model_validate(rule)


@pytest.mark.rn("RN-21")
@pytest.mark.parametrize(
    ("starters", "error"),
    [([], "at least 1"), (["venusaur", "venusaur"], "repetidos")],
)
def test_a_game_has_some_starters_without_repeats(starters: list[str], error: str) -> None:
    with pytest.raises(ValidationError, match=error):
        StartersFile.model_validate({"games": {"firered": starters}})


def test_key_battle_ids_are_unique_and_valid() -> None:
    battle = {"id": "brock", "category": "gym_leader", "trainer": "Brock", "wikidex_page": "Brock"}
    with pytest.raises(ValidationError, match="repetidos"):
        KeyBattlesFile.model_validate(
            {"games": ["firered"], "wikidex_section": "S", "battles": [battle, battle]}
        )
    with pytest.raises(ValidationError):
        KeyBattlesFile.model_validate(
            {"games": ["firered"], "wikidex_section": "S", "battles": [{**battle, "id": "B P"}]}
        )


def test_invalid_file_names_the_file(tmp_path: Path) -> None:
    shutil.copytree(CURATED_DIR, tmp_path / "curated")
    (tmp_path / "curated" / "breeding.yaml").write_text("incense_babies: [azurill]\n")

    with pytest.raises(CuratedDataError, match=r"breeding\.yaml"):
        read_curated(tmp_path / "curated")


def test_location_entry_needs_a_name_or_an_event_item() -> None:
    with pytest.raises(ValidationError, match="name_es, event_item"):
        LocationEntry(note="sin datos")


def test_transfer_group_rejects_repeated_games() -> None:
    with pytest.raises(ValidationError, match="repetidos"):
        TransferGroup(games=["firered", "firered"])


@pytest.mark.rn("RN-25")
def test_transfer_pairs_keep_the_least_restrictive_limit() -> None:
    """RN-25: Gold and Silver share the Time Capsule group (limit 1) and their own (none)."""
    pairs = transfer_pairs(
        TransfersFile(
            groups=[
                TransferGroup(games=["red", "gold", "silver"], max_species_generation=1),
                TransferGroup(games=["gold", "silver"]),
            ]
        )
    )

    assert pairs[("red", "gold")] == 1
    assert pairs[("gold", "red")] == 1
    assert pairs[("gold", "silver")] is None
    assert ("red", "red") not in pairs
    assert len(pairs) == 6


# --- Curated source ------------------------------------------------------------------------


def test_curated_source_rows() -> None:
    """Game mechanics, starters, the Pokédex of each game, transfers, event Pokémon and the
    catalog of evolution methods; key battles are loaded by the WikiDex source with their
    teams, and locations by PokeAPI's."""
    rows = list(CuratedSource(read_curated(CURATED_DIR)).rows())
    mechanics = [row for row in rows if isinstance(row, GameMechanic)]
    starters = [(row.game, row.pokemon) for row in rows if isinstance(row, GameStarter)]
    pokedexes = {row.game: row.pokedex for row in rows if isinstance(row, GamePokedex)}
    transfers = {
        (row.from_game, row.to_game): row.max_species_generation
        for row in rows
        if isinstance(row, GameTransfer)
    }
    events = {(row.game, row.pokemon) for row in rows if isinstance(row, EventPokemon)}
    methods = {(row.kind, row.name): row for row in rows if isinstance(row, EvolutionMethod)}

    assert len(mechanics) == 4
    assert len(starters) == 31  # 3 per game, 1 in Yellow
    assert len(rows) == (
        len(mechanics) + len(starters) + len(pokedexes) + len(transfers) + len(events)
    ) + len(methods)
    time_of_day = methods[(MethodKind.CONDITION, "time_of_day")]
    assert (time_of_day.reason, time_of_day.requires_mechanic) == (
        TediumReason.TIME_OF_DAY,
        "day_night_cycle",
    )
    assert methods[(MethodKind.CONDITION, "known_move")].unless_learnt_by_level
    assert (pokedexes["red"], pokedexes["gold"], pokedexes["firered"]) == (
        "kanto",
        "original-johto",
        "national",
    )
    assert transfers[("yellow", "crystal")] == 1  # Time Capsule
    assert transfers[("crystal", "gold")] is None
    assert ("crystal", "emerald") not in transfers
    assert ("firered", "mew") in events
    assert ("firered", "charizard") in starters
    assert ("emerald", "swampert") in starters
    assert ("yellow", "raichu") in starters
    day_night = next(m for m in mechanics if m.fact_key == "mechanic:firered:day_night_cycle")
    assert (day_night.value, day_night.origin) == (False, Origin.INFERRED)


def test_key_battles_point_to_their_wikidex_team() -> None:
    [battles_file] = read_curated(CURATED_DIR).key_battles
    battles = {battle.id: battle for battle in battles_file.battles}

    assert battles_file.wikidex_section == "Pokémon Rojo Fuego y Pokémon Verde Hoja"
    assert battles["giovanni-gym"].wikidex_team == "En el Gimnasio de Ciudad Verde"
    assert "giovanni-silph-co" not in battles  # CA-39
    assert battles["bruno"].wikidex_page == "Bruno (Alto Mando)"  # «Bruno» is a disambiguation
    assert battles["champion"].category is BattleCategory.CHAMPION
    assert battles["champion"].rival_starter_lines == ["bulbasaur", "charmander", "squirtle"]


def test_cli_reports_invalid_curated_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    curated = tmp_path / "curated"
    shutil.copytree(CURATED_DIR, curated)
    (curated / "arrival.yaml").write_text("games:\n  firered:\n    origin: inferred\n")
    monkeypatch.setattr(cli, "CURATED_DIR", curated)

    exit_code = cli.main(["--data-dir", str(tmp_path / "data"), "--offline"])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "ERROR en los datos curados" in output
    assert "arrival.yaml" in output


def test_every_evolution_method_of_pokeapi_is_catalogued() -> None:
    """CA-42: the 18 triggers and every condition of the pinned dump, also those not in the
    loaded games yet, so only a new commit of PokeAPI can block the load."""
    catalog = read_curated(CURATED_DIR).evolution_methods
    with EVOLUTION_TRIGGERS.open(encoding="utf-8") as file:
        triggers = {row["identifier"] for row in csv.DictReader(file)}

    assert len(triggers) == 18
    assert set(catalog.triggers) == triggers
    assert set(catalog.conditions) == set(condition_keys())


@pytest.mark.rn("RN-15")
def test_gender_is_not_tedious() -> None:
    """CA-43: it is bred until it has the right gender."""
    catalog = read_curated(CURATED_DIR).evolution_methods
    assert catalog.conditions["gender_id"].category is MethodCategory.EASY


@pytest.mark.parametrize(
    "entry",
    [{"category": "tedious"}, {"category": "easy", "reason": "trade"}],
)
def test_only_a_tedious_method_has_a_reason(entry: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="reason"):
        EvolutionMethodEntry.model_validate(entry)


def test_an_evolution_method_needs_a_known_mechanic() -> None:
    entry = {"category": "tedious", "reason": "other", "requires_mechanic": "weather"}
    with pytest.raises(ValidationError, match="requires_mechanic"):
        EvolutionMethodEntry.model_validate(entry)
