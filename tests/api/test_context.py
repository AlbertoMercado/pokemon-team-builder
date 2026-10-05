"""The engine's GameContext built from reference.sqlite and the user's data (RN-10, RN-18)."""

import dataclasses
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session

from api.errors import NotFoundError
from api.services.context import GameReference, GameReferences, build_context
from core.domain import GameContext
from core.engine import generate
from core.review import FactValue
from core.rules.catalog import RuleSettings
from db.reference import Origin
from db.sqlite import create_sqlite_engine
from db.user import FactConfirmation, value_hash
from tests.api.scenario import Load, ScenarioData, firered_data, write_firered
from tests.core.scenario import FAVORITES, firered_context

DEFAULTS = RuleSettings.defaults()


def _load(
    data_dir: Path,
    data: ScenarioData | None = None,
    *,
    arrival_origin: Origin = Origin.INFERRED,
    battle_origins: Mapping[str, Origin] | None = None,
) -> GameReference:
    write_firered(
        data_dir, data, Load(arrival_origin=arrival_origin, battle_origins=battle_origins or {})
    )
    engine = create_sqlite_engine(data_dir / "reference.sqlite")
    try:
        with Session(engine) as session:
            return GameReferences().get(session, "firered")
    finally:
        engine.dispose()


def _confirmed(key: str, value: bool | list[str], proposal: FactValue | None) -> FactConfirmation:
    stored = list(proposal) if isinstance(proposal, tuple) else proposal
    return FactConfirmation(
        fact_key=key,
        game="firered",
        confirmed_value=value,
        proposed_value_hash=value_hash(stored),
        confirmed_at=datetime.now(UTC),
    )


def _context(
    game: GameReference,
    favorites: tuple[str, ...] = FAVORITES,
    confirmations: Mapping[str, FactConfirmation] | None = None,
) -> GameContext:
    return build_context(game, favorites, DEFAULTS, confirmations or {})


@pytest.fixture(scope="module")
def firered(tmp_path_factory: pytest.TempPathFactory) -> GameReference:
    return _load(tmp_path_factory.mktemp("data"))


@pytest.mark.rn("RN-10")
@pytest.mark.rn("RN-18")
def test_firered_context_matches_the_engine_scenario(firered: GameReference) -> None:
    """Built from the database, FireRed is the engine's real scenario, inferred proposals
    included, and the engine gives the same teams."""
    built = _context(firered)
    expected = firered_context()
    # The API adds the name of the game, for the explanations; the scenario has none.
    assert built.game == dataclasses.replace(expected.game, name="Firered")
    assert built.type_chart.types == tuple(sorted(expected.type_chart.types))
    assert dict(built.type_chart.factors) == dict(expected.type_chart.factors)
    assert sorted(built.favorites, key=str) == sorted(expected.favorites, key=str)
    assert built.key_battles == expected.key_battles
    arriving = {e.pokemon: e.availability for e in built.pool if e.availability.can_arrive}
    assert arriving == {e.pokemon: e.availability for e in expected.pool}
    assert generate(built).teams == generate(expected).teams


@pytest.mark.rn("RN-18")
def test_the_pool_is_unverified_until_its_data_is_confirmed(firered: GameReference) -> None:
    """CA-31: suggestions with inferred data are marked; confirming them verifies them."""
    pool = {e.pokemon.slug: e for e in _context(firered).pool}
    assert not pool["poliwrath"].verified
    key = "pokemon:firered:poliwrath:arrival"
    confirmed = _context(firered, confirmations={key: _confirmed(key, True, True)})
    assert {e.pokemon.slug: e for e in confirmed.pool}["poliwrath"].verified


@pytest.mark.rn("RN-18")
@pytest.mark.rn("RN-03")
def test_a_confirmed_value_replaces_the_proposal(firered: GameReference) -> None:
    """The DDF example: Raichu cannot arrive at FireRed; the user's value is the one used."""
    key = "pokemon:firered:raichu:arrival"
    [raichu] = _context(firered, ("raichu",)).favorites
    assert not raichu.availability.can_arrive
    corrected = _context(firered, ("raichu",), {key: _confirmed(key, True, False)})
    assert corrected.favorites[0].availability.can_arrive


@pytest.mark.rn("RN-18")
def test_a_confirmation_of_another_proposal_does_not_apply(firered: GameReference) -> None:
    key = "pokemon:firered:raichu:arrival"
    stale = _confirmed(key, True, True)  # answered a proposal the load no longer makes
    [raichu] = _context(firered, ("raichu",), {key: stale}).favorites
    assert not raichu.availability.can_arrive


@pytest.mark.rn("RN-18")
def test_a_pending_value_is_possible_but_unverified(tmp_path: Path) -> None:
    game = _load(tmp_path, arrival_origin=Origin.PENDING)
    pool = {e.pokemon.slug: e for e in _context(game).pool}
    assert pool["raichu"].availability.can_arrive
    assert not pool["raichu"].verified


@pytest.mark.rn("RN-15")
@pytest.mark.rn("RN-18")
def test_confirmed_mechanics_are_the_game_mechanics(firered: GameReference) -> None:
    key = "mechanic:firered:day_night_cycle"
    ctx = _context(firered, confirmations={key: _confirmed(key, True, False)})
    assert ctx.game.mechanics == frozenset({"day_night_cycle"})


@pytest.mark.rn("RN-17")
@pytest.mark.rn("RN-18")
def test_key_battle_team_corrected_by_the_user(tmp_path: Path) -> None:
    """A pending battle has no team; once the user gives it, its rivals have their types."""
    game = _load(tmp_path, battle_origins={"firered-misty": Origin.PENDING})
    assert "firered-misty" not in [b.slug for b in _context(game).key_battles]
    key = "battle:firered:misty"
    ctx = _context(game, confirmations={key: _confirmed(key, ["staryu", "starmie"], None)})
    [misty] = [b for b in ctx.key_battles if b.slug == "firered-misty"]
    assert [(r.pokemon, r.types) for r in misty.rivals] == [
        ("staryu", ("water",)),
        ("starmie", ("water", "psychic")),
    ]


@pytest.mark.rn("RN-09")
@pytest.mark.rn("RN-05")
def test_a_regional_line_keeps_its_regional_stages(tmp_path: Path) -> None:
    data = firered_data()
    stage = {"is_baby": False, "requires_incense": False}
    shrew = {"pokemon": "sandshrew-alola", "species": "sandshrew", **stage}
    slash = {"pokemon": "sandslash-alola", "species": "sandslash", **stage}
    base = next(p for p in data["pokemon"] if p["slug"] == "sandslash")
    step = {"from": "sandshrew-alola", "to": "sandslash-alola", "trigger": "use-item"}
    alolan_types = ["ice", "steel"]
    data["pokemon"].append(
        {
            **base,
            "slug": "sandshrew-alola",
            "species": "sandshrew",
            "name": "Sandshrew de Alola",
            "dex_number": 27,
            "types": alolan_types,
            "region": "alola",
            "stages": [shrew],
            "evolution_steps": [],
        }
    )
    data["pokemon"].append(
        {
            **base,
            "slug": "sandslash-alola",
            "name": "Sandslash de Alola",
            "types": alolan_types,
            "region": "alola",
            "stages": [shrew, slash],
            "evolution_steps": [{**step, "conditions": {"trigger_item": "ice-stone"}}],
        }
    )
    game = _load(tmp_path, data)
    alolan = game.forms["sandslash-alola"]
    assert [s.pokemon for s in alolan.stages] == ["sandshrew-alola", "sandslash-alola"]
    assert [s.pokemon for s in game.forms["sandslash"].stages] == ["sandshrew", "sandslash"]


@pytest.mark.rn("RN-03")
@pytest.mark.rn("RN-10")
def test_a_pre_evolution_of_a_later_generation_does_not_exist_yet(tmp_path: Path) -> None:
    """Munchlax (4th generation) is not a stage of Snorlax in FireRed, and as a favourite it
    keeps its own types and is discarded by RN-03."""
    data = firered_data()
    snorlax = next(p for p in data["pokemon"] if p["slug"] == "snorlax")
    munchlax = {"pokemon": "munchlax", "species": "munchlax", "is_baby": True}
    munchlax_stage = {**munchlax, "requires_incense": True}
    snorlax["stages"].insert(0, munchlax_stage)
    data["pokemon"].append(
        {
            **snorlax,
            "slug": "munchlax",
            "species": "munchlax",
            "name": "Munchlax",
            "dex_number": 446,
            "generation": 4,
            "stages": [munchlax_stage],
            "evolution_steps": [],
        }
    )
    game = _load(tmp_path, data)
    assert [s.pokemon for s in game.forms["snorlax"].stages] == ["snorlax"]
    ctx = _context(game, ("munchlax", "snorlax"))
    assert "munchlax" not in [e.pokemon.slug for e in ctx.pool]
    [discard] = generate(ctx).discards
    assert (discard.pokemon, discard.reason) == ("munchlax", "generation")


def test_a_game_that_is_not_a_target_is_not_found(tmp_path: Path) -> None:
    write_firered(tmp_path)
    engine = create_sqlite_engine(tmp_path / "reference.sqlite")
    with Session(engine) as session, pytest.raises(NotFoundError, match="gold"):
        GameReferences().get(session, "gold")
    engine.dispose()
