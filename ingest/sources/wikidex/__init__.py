"""WikiDex source: teams of the key battles listed in the curated data (RN-17).

For each curated battle, reads its trainer page (cached, rate limited), finds the team in
the games' section, translates the Spanish names to loaded forms, leaves out the rival's
starter (CA-26) and, if the team has variants, keeps the Pokémon common to all of them
(CA-38). See docs/02-ddt/plan-carga-datos.md and docs/02-ddt/datos-curados.md.
"""

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass

from db.reference import KeyBattle, KeyBattlePokemon, Origin, ReferenceModel
from ingest.sources.curated import CuratedData
from ingest.sources.curated.schemas import BattleEntry
from ingest.sources.pokeapi.index import PokemonIndex
from ingest.sources.wikidex.fetch import PageCache
from ingest.sources.wikidex.parse import TeamMember, TeamParseError, find_section, team_variants


class WikidexDataError(Exception):
    """A key battle's team could not be read; the curated data or WikiDex must be checked."""


class WikidexSource:
    """Ingest source of the key battles and their teams.

    ``index`` provides the loaded Pokémon by Spanish name; it is called lazily so the
    PokeAPI files are read only once per load.
    """

    name = "wikidex"
    pokeapi_commit = None

    def __init__(
        self, curated: CuratedData, pages: PageCache, index: Callable[[], PokemonIndex]
    ) -> None:
        self._curated = curated
        self._pages = pages
        self._index = index

    def rows(self) -> Iterable[ReferenceModel]:
        index = self._index()
        for battles_file in self._curated.key_battles:
            for order, battle in enumerate(battles_file.battles, start=1):
                page = self._pages.page(battle.wikidex_page)
                try:
                    section = find_section(page.wikitext, battles_file.wikidex_section)
                    variants = team_variants(section, battle.wikidex_team)
                except TeamParseError as error:
                    raise WikidexDataError(
                        f"{battle.id} ({battle.wikidex_page}): {error}"
                    ) from None
                teams = [
                    _without_starter(_resolve(team, battle, index), battle, index)
                    for team in variants
                ]
                read = _ReadBattle(order, battle, _common_members(teams, battle), page.revision)
                for game in battles_file.games:
                    yield from read.rows(game)


type ResolvedTeam = list[tuple[TeamMember, str, int]]  # member, form slug, evolution chain


def _resolve(team: list[TeamMember], battle: BattleEntry, index: PokemonIndex) -> ResolvedTeam:
    resolved = []
    for member in team:
        pokemon = index.find(member.name)
        if pokemon is None:
            raise WikidexDataError(
                f"{battle.id} ({battle.wikidex_page}): «{member.name}» no es un Pokémon cargado"
            )
        resolved.append((member, pokemon.slug, pokemon.evolution_chain))
    return resolved


def _without_starter(team: ResolvedTeam, battle: BattleEntry, index: PokemonIndex) -> ResolvedTeam:
    """Leave out the rival's starter: exactly one member of a starter line (CA-26)."""
    if not battle.rival_starter_lines:
        return team
    unknown = [s for s in battle.rival_starter_lines if s not in index.chain_by_species]
    if unknown:
        raise WikidexDataError(f"{battle.id}: líneas de inicial desconocidas {unknown}")
    chains = {index.chain_by_species[s] for s in battle.rival_starter_lines}
    starters = [entry for entry in team if entry[2] in chains]
    if len(starters) != 1:
        names = [entry[0].name for entry in starters]
        raise WikidexDataError(f"{battle.id}: se esperaba un inicial en el equipo y hay {names}")
    return [entry for entry in team if entry[2] not in chains]


def _common_members(teams: list[ResolvedTeam], battle: BattleEntry) -> ResolvedTeam:
    """Pokémon present in every variant, in the order of the first one (CA-38).

    A team with variants depends on the player's choice (the rival's on the starter), so
    only what the player meets whatever they choose is kept.
    """
    common = list(teams[0])
    for team in teams[1:]:
        remaining = [pokemon for _member, pokemon, _chain in team]
        kept = []
        for entry in common:
            if entry[1] in remaining:
                remaining.remove(entry[1])  # repeated Pokémon count once per variant
                kept.append(entry)
        common = kept
    if not common:
        raise WikidexDataError(f"{battle.id}: sus variantes no tienen ningún Pokémon en común")
    return common


@dataclass(frozen=True)
class _ReadBattle:
    """A curated battle with its team already read from WikiDex."""

    order: int
    battle: BattleEntry
    team: ResolvedTeam
    revision: int

    def rows(self, game: str) -> Iterator[ReferenceModel]:
        slug = f"{game}-{self.battle.id}"
        yield KeyBattle(
            slug=slug,
            game=game,
            category=self.battle.category,
            trainer_name=self.battle.trainer,
            order=self.order,
            origin=Origin.AUTOMATIC,
            fact_key=f"battle:{game}:{self.battle.id}",
            source_page=self.battle.wikidex_page,
            source_revision=self.revision,
        )
        for member, pokemon, _chain in self.team:
            yield KeyBattlePokemon(
                battle=slug, position=member.position, pokemon=pokemon, level=member.level
            )
