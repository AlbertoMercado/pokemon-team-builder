"""WikiDex source of the ingest: cache and rate limit, team parsing and key battle rows,
on real pages cut down to their FireRed and LeafGreen section (no network)."""

import dataclasses
import json
from collections.abc import Mapping
from pathlib import Path

import httpx
import pytest

from db.reference import BattleCategory, KeyBattle, KeyBattlePokemon, Origin, ReferenceModel
from ingest.sources.curated import CuratedData, read_curated
from ingest.sources.curated.schemas import BattleEntry, KeyBattlesFile
from ingest.sources.pokeapi.index import IndexedPokemon, PokemonIndex, normalize_name
from ingest.sources.wikidex import WikidexDataError, WikidexSource
from ingest.sources.wikidex.fetch import PageCache, WikidexError, WikiPage, fetch_page
from ingest.sources.wikidex.parse import TeamMember, TeamParseError, find_section, team_variants

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "wikidex"
CURATED = read_curated(Path(__file__).resolve().parents[2] / "data" / "curated")
SECTION = "Pokémon Rojo Fuego y Pokémon Verde Hoja"


def _page(title: str) -> WikiPage:
    return PageCache(FIXTURES, fetcher=None).page(title)


def _section(title: str) -> str:
    return find_section(_page(title).wikitext, SECTION)


def _names(variants: list[list[TeamMember]]) -> list[list[str]]:
    return [[member.name for member in team] for team in variants]


# --- Cache and rate limit ------------------------------------------------------------------


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def test_cache_fetches_each_page_once(tmp_path: Path) -> None:
    fetched: list[str] = []

    def fetcher(title: str) -> WikiPage:
        fetched.append(title)
        return WikiPage(title=title, revision=1, wikitext="texto")

    cache = PageCache(tmp_path, fetcher)
    assert cache.page("Azul (personaje)").wikitext == "texto"
    assert cache.page("Azul (personaje)").wikitext == "texto"

    assert fetched == ["Azul (personaje)"]
    assert (tmp_path / "Azul%20%28personaje%29.json").exists()


def test_cache_waits_one_second_between_requests(tmp_path: Path) -> None:
    clock = FakeClock()
    cache = PageCache(
        tmp_path,
        lambda title: WikiPage(title=title, revision=1, wikitext=""),
        clock=clock,
        sleep=clock.sleep,
    )

    cache.page("Brock")
    clock.now += 0.25
    cache.page("Misty")
    cache.page("Brock")  # cached: no request, no wait

    assert clock.slept == [pytest.approx(0.75)]


def test_offline_cache_fails_on_a_missing_page(tmp_path: Path) -> None:
    with pytest.raises(WikidexError, match="Brock"):
        PageCache(tmp_path, fetcher=None).page("Brock")


def _fake_api(monkeypatch: pytest.MonkeyPatch, payload: Mapping[str, object]) -> list[str]:
    urls: list[str] = []

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        urls.append(url)
        request = httpx.Request("GET", url)
        return httpx.Response(200, content=json.dumps(payload).encode(), request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    return urls


def test_fetch_page_reads_the_api_response(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"parse": {"title": "Brock", "revid": 7, "wikitext": "{{Equipo}}"}}
    urls = _fake_api(monkeypatch, payload)

    page = fetch_page("Brock")

    assert page == WikiPage(title="Brock", revision=7, wikitext="{{Equipo}}")
    assert urls == ["https://www.wikidex.net/api.php"]


def test_fetch_page_reports_a_missing_page(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"error": {"code": "missingtitle", "info": "The page does not exist."}}
    _fake_api(monkeypatch, payload)

    with pytest.raises(WikidexError, match="does not exist"):
        fetch_page("Brok")


# --- Parsing -------------------------------------------------------------------------------


def test_single_team_without_labels() -> None:
    [team] = team_variants(_section("Brock"), None)
    assert [(m.position, m.name, m.level) for m in team] == [(1, "Geodude", 12), (2, "Onix", 14)]


def test_labelled_battles_of_one_section() -> None:
    section = _section("Giovanni")
    assert _names(team_variants(section, "En Silph S.A.")) == [
        ["Nidorino", "Rhyhorn", "Kangaskhan", "Nidoqueen"]
    ]
    assert _names(team_variants(section, "En el Gimnasio de Ciudad Verde")) == [
        ["Rhyhorn", "Dugtrio", "Nidoking", "Nidoqueen", "Rhyhorn"]
    ]


def test_variants_inside_a_tabber() -> None:
    variants = team_variants(_section("Azul (personaje)"), "Como campeón")
    assert [team[-1].name for team in variants] == ["Charizard", "Blastoise", "Venusaur"]
    assert all(len(team) == 6 for team in variants)


def test_missing_label_lists_the_available_ones() -> None:
    with pytest.raises(TeamParseError, match="En el Casino Rocket"):
        team_variants(_section("Giovanni"), "En la Torre Pokémon")


def test_section_with_labels_needs_one() -> None:
    with pytest.raises(TeamParseError, match="falta wikidex_team"):
        team_variants(_section("Giovanni"), None)


def test_disambiguation_page_is_recognised() -> None:
    with pytest.raises(TeamParseError, match="desambiguación"):
        find_section(_page("Bruno").wikitext, SECTION)


def test_section_must_not_be_ambiguous() -> None:
    wikitext = f"== {SECTION} ==\n{{{{Equipo|P1=Onix}}}}\n== {SECTION} ==\n"
    with pytest.raises(TeamParseError, match="2 secciones"):
        find_section(wikitext, SECTION)


# --- Source --------------------------------------------------------------------------------


def _index() -> PokemonIndex:
    """Index of the Pokémon on the test pages; starters share a line with their evolution."""
    lines = {
        "bulbasaur": 1,
        "venusaur": 1,
        "charmander": 2,
        "charizard": 2,
        "squirtle": 3,
        "blastoise": 3,
    }
    others = ["pidgeot", "alakazam", "rhydon", "exeggutor", "gyarados", "arcanine", "geodude"]
    others += ["onix", "nidorino", "rhyhorn", "kangaskhan", "nidoqueen"]
    chains = {**lines, **{slug: 100 + i for i, slug in enumerate(others)}}
    return PokemonIndex(
        by_name={
            normalize_name(slug): IndexedPokemon(slug=slug, evolution_chain=chain)
            for slug, chain in chains.items()
        },
        chain_by_species=chains,
    )


def _curated_with(*battles: BattleEntry) -> CuratedData:
    battles_file = KeyBattlesFile(
        games=["firered", "leafgreen"], wikidex_section=SECTION, battles=list(battles)
    )
    return dataclasses.replace(CURATED, key_battles=[battles_file])


def _rows(*battles: BattleEntry) -> list[ReferenceModel]:
    source = WikidexSource(_curated_with(*battles), PageCache(FIXTURES, None), _index)
    return list(source.rows())


BROCK = BattleEntry(
    id="brock", category=BattleCategory.GYM_LEADER, trainer="Brock", wikidex_page="Brock"
)
CHAMPION = BattleEntry(
    id="champion",
    category=BattleCategory.CHAMPION,
    trainer="Azul",
    wikidex_page="Azul (personaje)",
    wikidex_team="Como campeón",
    rival_starter_lines=["bulbasaur", "charmander", "squirtle"],
)


@pytest.mark.rn("RN-17")
def test_battle_rows_for_each_game() -> None:
    rows = _rows(BROCK)
    battles = [row for row in rows if isinstance(row, KeyBattle)]
    pokemon = [row for row in rows if isinstance(row, KeyBattlePokemon)]

    assert [(b.slug, b.order, b.origin) for b in battles] == [
        ("firered-brock", 1, Origin.AUTOMATIC),
        ("leafgreen-brock", 1, Origin.AUTOMATIC),
    ]
    assert battles[0].fact_key == "battle:firered:brock"
    assert (battles[0].source_page, battles[0].source_revision) == ("Brock", 3562807)
    firered = [(p.position, p.pokemon, p.level) for p in pokemon if p.battle == "firered-brock"]
    assert firered == [(1, "geodude", 12), (2, "onix", 14)]


@pytest.mark.rn("RN-17")
def test_rival_keeps_only_what_every_variant_shares() -> None:
    """CA-26: the starter is left out. CA-38: of the rest, only what is in all variants."""
    rows = _rows(CHAMPION)
    [battle, _] = [row for row in rows if isinstance(row, KeyBattle)]
    team = [
        row.pokemon
        for row in rows
        if isinstance(row, KeyBattlePokemon) and row.battle == "firered-champion"
    ]

    assert battle.origin is Origin.AUTOMATIC
    # Exeggutor, Gyarados and Arcanine depend on the starter: they do not count.
    assert team == ["pidgeot", "alakazam", "rhydon"]


def test_variants_without_common_pokemon_fail(tmp_path: Path) -> None:
    wikitext = (
        f"== {SECTION} ==\n; Final\n<tabber>\nA=\n{{{{Equipo|P1=Onix|NvP1=10}}}}\n"
        "|-|\nB=\n{{Equipo|P1=Geodude|NvP1=10}}\n</tabber>\n"
    )
    pages = PageCache(tmp_path, fetcher=None)
    page = WikiPage(title="Final", revision=1, wikitext=wikitext)
    pages.path("Final").write_text(page.model_dump_json(), encoding="utf-8")
    battle = BROCK.model_copy(update={"wikidex_page": "Final", "wikidex_team": "Final"})
    source = WikidexSource(_curated_with(battle), pages, _index)

    with pytest.raises(WikidexDataError, match="ningún Pokémon en común"):
        list(source.rows())


def test_unknown_pokemon_name_fails() -> None:
    giovanni = BattleEntry(
        id="giovanni-gym",
        category=BattleCategory.GYM_LEADER,
        trainer="Giovanni",
        wikidex_page="Giovanni",
        wikidex_team="En el Gimnasio de Ciudad Verde",
    )
    with pytest.raises(WikidexDataError, match="Dugtrio"):  # not in the test index
        _rows(giovanni)


def test_wrong_starter_lines_fail() -> None:
    wrong = CHAMPION.model_copy(update={"rival_starter_lines": ["bulbasaur"]})
    with pytest.raises(WikidexDataError, match="un inicial"):
        _rows(wrong)


def test_parse_errors_name_the_battle() -> None:
    wrong = BROCK.model_copy(update={"wikidex_team": "Revancha"})
    with pytest.raises(WikidexDataError, match=r"brock \(Brock\)"):
        _rows(wrong)
