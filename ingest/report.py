"""Load report: what was loaded, how much is inferred or pending, and errors (RF-11)."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoadReport:
    """Outcome of an ingest run.

    ``rows_by_table`` counts the stored rows per table. ``origins_by_table`` counts the
    reviewable values per table and origin (``automatic``, ``inferred``, ``pending``), so
    the administrator knows how much the user will have to confirm (RN-18).
    """

    target: Path
    rows_by_table: dict[str, int] = field(default_factory=dict)
    origins_by_table: dict[str, dict[str, int]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return not self.errors

    def render(self) -> str:
        """Human-readable report for the terminal, in Spanish like the rest of the UI."""
        lines = [f"Carga de {self.target}"]
        if not self.succeeded:
            lines.append("ERROR: la carga ha fallado; se conserva la base de datos anterior.")
            lines.extend(f"  - {error}" for error in self.errors)
            return "\n".join(lines)

        lines.append("Filas cargadas por tabla:")
        lines.extend(f"  {table:<20} {count:>6}" for table, count in self.rows_by_table.items())
        if self.origins_by_table:
            lines.append("Datos revisables por origen:")
            for table, origins in self.origins_by_table.items():
                detail = ", ".join(f"{origin} {count}" for origin, count in origins.items())
                lines.append(f"  {table:<20} {detail}")
        lines.append("Carga completada.")
        return "\n".join(lines)
