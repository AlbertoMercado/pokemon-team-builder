"""Load report: what was loaded, how much is inferred or pending, and errors (RF-11)."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoadReport:
    """Outcome of an ingest run.

    ``checks_passed`` is the number of data checks of the load that passed. ``warnings`` do
    not reject the load, like confirmations of user.sqlite whose data no longer exists.

    ``rows_by_table`` counts the stored rows per table. ``origins_by_table`` counts the
    reviewable values per table and origin (``automatic``, ``inferred``, ``pending``), so
    the administrator knows how much the user will have to confirm (RN-18). ``images`` and
    ``artworks`` are the number of forms with a sprite or an official artwork, and the number of
    forms, if the load includes images; ``covers``, the number of games with a cover and the
    number of games, if it includes covers. ``incomplete_games`` are the games that cannot be
    chosen as target because they lack data, with what they lack (RF-05, CA-67).
    """

    target: Path
    rows_by_table: dict[str, int] = field(default_factory=dict)
    origins_by_table: dict[str, dict[str, int]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks_passed: int = 0
    images: tuple[int, int] | None = None
    artworks: tuple[int, int] | None = None
    covers: tuple[int, int] | None = None
    incomplete_games: dict[str, list[str]] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return not self.errors

    def render(self) -> str:
        """Human-readable report for the terminal, in Spanish like the rest of the UI."""
        lines = [f"Carga de {self.target}"]
        if not self.succeeded:
            lines.append("ERROR: la carga ha fallado; se conserva la base de datos anterior.")
            lines.extend(f"  - {error}" for error in self.errors)
            lines.extend(self._warnings())
            return "\n".join(lines)

        lines.append("Filas cargadas por tabla:")
        lines.extend(f"  {table:<20} {count:>6}" for table, count in self.rows_by_table.items())
        if self.origins_by_table:
            lines.append("Datos revisables por origen:")
            for table, origins in self.origins_by_table.items():
                detail = ", ".join(f"{origin} {count}" for origin, count in origins.items())
                lines.append(f"  {table:<20} {detail}")
        if self.images is not None:
            with_image, forms = self.images
            lines.append(f"Imágenes: {with_image} de {forms} formas")
        if self.artworks is not None:
            with_artwork, forms = self.artworks
            lines.append(f"Ilustraciones: {with_artwork} de {forms} formas")
        if self.covers is not None:
            with_cover, games = self.covers
            lines.append(f"Portadas: {with_cover} de {games} juegos")
        if self.incomplete_games:
            lines.append("Juegos que no se pueden elegir como objetivo (datos incompletos):")
            lines.extend(
                f"  {game}: faltan {_listed(missing)}"
                for game, missing in self.incomplete_games.items()
            )
        if self.checks_passed:
            lines.append(f"Comprobaciones superadas: {self.checks_passed}")
        lines.extend(self._warnings())
        lines.append("Carga completada.")
        return "\n".join(lines)

    def _warnings(self) -> list[str]:
        if not self.warnings:
            return []
        return ["Avisos:", *(f"  - {warning}" for warning in self.warnings)]


def _listed(items: list[str]) -> str:
    """«a, b y c»."""
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} y {items[-1]}"
