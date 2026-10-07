"""The target game, its starters and its key battles (RN-15, RN-17, RN-21)."""

from dataclasses import dataclass

# Mechanics that condition evolutions (docs/02-ddt/datos-curados.md, games.yaml).
DAY_NIGHT_CYCLE = "day_night_cycle"
CONTESTS = "contests"


@dataclass(frozen=True)
class GameInfo:
    """Target game: identifier, generation and the mechanics it has (already confirmed).

    ``name`` is its Spanish name, for the explanations of the rules; without it, they use the
    identifier. ``starters`` are its starters, as the form of their final evolution in the
    game (RN-21, CA-59).
    """

    slug: str
    generation: int
    mechanics: frozenset[str] = frozenset()
    name: str | None = None
    starters: frozenset[str] = frozenset()

    def has(self, mechanic: str) -> bool:
        return mechanic in self.mechanics

    @property
    def label(self) -> str:
        """How the explanations call the game: «Rojo Fuego»."""
        return self.name or self.slug


@dataclass(frozen=True)
class Rival:
    """A Pokémon of a key battle, with its types in the target game's generation."""

    pokemon: str
    types: tuple[str, ...]


@dataclass(frozen=True)
class KeyBattle:
    """A key battle of the target game and its rival Pokémon (RN-17).

    The rival's starter and the Pokémon that depend on it are already left out (CA-26,
    CA-38).
    """

    slug: str
    category: str
    trainer: str
    rivals: tuple[Rival, ...]

    def __post_init__(self) -> None:
        if not self.rivals:
            raise ValueError(f"{self.slug}: un combate clave necesita al menos un rival")
