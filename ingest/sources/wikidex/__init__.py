"""WikiDex source: teams of the key battles listed in the curated data (RN-17).

For each curated battle, reads its trainer page (cached, rate limited), finds the team in
the games' section, translates the Spanish names to loaded forms and leaves out the rival's
starter (CA-26). See docs/02-ddt/plan-carga-datos.md and docs/02-ddt/datos-curados.md.
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
                read = _ReadBattle(order, battle, teams, page.revision)
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


@dataclass(frozen=True)
class _ReadBattle:
    """A curated battle with its team (or variants) already read from WikiDex."""

    order: int
    battle: BattleEntry
    teams: list[ResolvedTeam]
    revision: int

    def rows(self, game: str) -> Iterator[ReferenceModel]:
        slug = f"{game}-{self.battle.id}"
        yield KeyBattle(
            slug=slug,
            game=game,
            category=self.battle.category,
            trainer_name=self.battle.trainer,
            order=self.order,
            # Variants depend on the player's choice: the user confirms them (RN-18).
            origin=Origin.AUTOMATIC if len(self.teams) == 1 else Origin.INFERRED,
            fact_key=f"battle:{game}:{self.battle.id}",
            source_page=self.battle.wikidex_page,
            source_revision=self.revision,
        )
        for variant, team in enumerate(self.teams, start=1):
            for member, pokemon, _chain in team:
                yield KeyBattlePokemon(
                    battle=slug,
                    variant=variant,
                    position=member.position,
                    pokemon=pokemon,
                    level=member.level,
                )
