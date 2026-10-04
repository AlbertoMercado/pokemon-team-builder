"""The engine's only input: everything needed to generate teams for one target game."""

from dataclasses import dataclass

from core.domain.game import GameInfo, KeyBattle
from core.domain.journey import HallOfFameEntry
from core.domain.pokemon import Candidate, PokemonData, PoolEntry
from core.domain.types import TypeChart
from core.rules.catalog import RuleSettings


class GameContextError(ValueError):
    """The context is not consistent."""


@dataclass(frozen=True)
class GameContext:
    """Data of one target game, the user's favourites and settings, already resolved.

    Built by ``api/services/`` from both databases. Every value is already confirmed (RN-18):
    the engine does not know where data comes from. ``journey`` are the user's Hall of Fame
    entries; ``core.journey`` decides which forms they exclude (RN-16).
    """

    game: GameInfo
    type_chart: TypeChart
    favorites: tuple[Candidate, ...]
    pool: tuple[PoolEntry, ...]
    key_battles: tuple[KeyBattle, ...]
    settings: RuleSettings
    journey: tuple[HallOfFameEntry, ...] = ()

    def __post_init__(self) -> None:
        if self.type_chart.generation != self.game.generation:
            raise GameContextError(
                f"la tabla de tipos es de la generación {self.type_chart.generation} y el "
                f"juego, de la {self.game.generation}"
            )
        favorites = [candidate.pokemon.slug for candidate in self.favorites]
        repeated = sorted({slug for slug in favorites if favorites.count(slug) > 1})
        if repeated:
            raise GameContextError(f"favoritos repetidos: {repeated}")
        in_both = sorted(set(favorites) & {entry.pokemon.slug for entry in self.pool})
        if in_both:
            raise GameContextError(f"Pokémon a la vez en favoritos y en el pool: {in_both}")
        sequences = [entry.sequence for entry in self.journey]
        if len(set(sequences)) != len(sequences):
            raise GameContextError(f"registros del Hall of Fame con el mismo orden: {sequences}")
        self._check_types()

    def _check_types(self) -> None:
        """Every type must exist in the game's generation (RN-10).

        Forms of a later generation are left out: they have no types in the game's generation
        (they keep the ones they appeared with) and RN-03 discards them before using them.
        """
        pokemon: list[PokemonData] = [c.pokemon for c in self.favorites]
        pokemon += [entry.pokemon for entry in self.pool]
        named = [(p.slug, p.types) for p in pokemon if p.generation <= self.game.generation]
        named += [(r.pokemon, r.types) for b in self.key_battles for r in b.rivals]
        unknown = sorted(
            {
                f"{slug}: {type_name}"
                for slug, types in named
                for type_name in types
                if not self.type_chart.has_type(type_name)
            }
        )
        if unknown:
            raise GameContextError(
                f"tipos que no existen en la generación {self.game.generation}: {unknown}"
            )
