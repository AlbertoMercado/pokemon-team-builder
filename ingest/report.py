"""Load report: what was loaded, how much is inferred or pending, errors and blockers (RF-11,
RF-16).

``LoadReport.render`` is the text shown in the terminal. ``write_report`` saves a completed or
blocked load as JSON (the source, with a stable format) and as Markdown generated from it,
for the architect (ADR-0008). Both formats are described in docs/05-operacion/ingesta.md,
section "Informe".
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

from ingest.blockers import Blocker

REPORT_FORMAT = 1
FILE_STATUS = {"completed": "completada", "blocked": "bloqueada"}


class LoadStatus(StrEnum):
    """Outcome of a load; the CLI turns it into the exit code (0, 2 or 1)."""

    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class LoadReport:
    """Outcome of an ingest run.

    ``checks_passed`` is the number of data checks of the load that passed. ``warnings`` do
    not reject the load, like confirmations of user.sqlite whose data no longer exists.
    ``blockers`` are what the application cannot handle without a new version: they keep the
    previous database, but unlike ``errors`` they are all collected (ADR-0008).

    ``rows_by_table`` counts the stored rows per table. ``origins_by_table`` counts the
    reviewable values per table and origin (``automatic``, ``inferred``, ``pending``), so
    the administrator knows how much the user will have to confirm (RN-18). ``images`` and
    ``artworks`` are the number of forms with a sprite or an official artwork, and the number of
    forms, if the load includes images; ``covers``, the number of games with a cover and the
    number of games, if it includes covers. ``incomplete_games`` are the games that cannot be
    chosen as target because they lack data, with what they lack (RF-05, CA-67).

    ``started_at``, ``finished_at``, ``pokeapi_commit`` and ``games`` identify the load in the
    report files.
    """

    target: Path
    rows_by_table: dict[str, int] = field(default_factory=dict)
    origins_by_table: dict[str, dict[str, int]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    checks_passed: int = 0
    images: tuple[int, int] | None = None
    artworks: tuple[int, int] | None = None
    covers: tuple[int, int] | None = None
    incomplete_games: dict[str, list[str]] = field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    pokeapi_commit: str | None = None
    games: list[str] = field(default_factory=list)

    @property
    def status(self) -> LoadStatus:
        """An error fails the load even if there are blockers: it must be fixed first."""
        if self.errors:
            return LoadStatus.FAILED
        return LoadStatus.BLOCKED if self.blockers else LoadStatus.COMPLETED

    @property
    def succeeded(self) -> bool:
        return self.status is LoadStatus.COMPLETED

    def render(self) -> str:
        """Human-readable report for the terminal, in Spanish like the rest of the UI."""
        lines = [f"Carga de {self.target}"]
        if self.status is LoadStatus.FAILED:
            lines.append("ERROR: la carga ha fallado; se conserva la base de datos anterior.")
            lines.extend(f"  - {error}" for error in self.errors)
            lines.extend(self._warnings())
            return "\n".join(lines)
        if self.status is LoadStatus.BLOCKED:
            lines.append(
                f"BLOQUEADA ({_count(len(self.blockers), 'bloqueo', 'bloqueos')}): hace falta "
                "una nueva versión; se conserva la base de datos anterior."
            )
            lines.extend(
                f"  - {blocker.kind}: {blocker.subject}"
                f" ({_count(len(blocker.occurrences), 'caso', 'casos')})"
                for blocker in self.blockers
            )
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


class BlockerJson(TypedDict):
    kind: str
    subject: str
    occurrences: list[str]
    rules: list[str]
    action: str
    template: str | None


class SummaryJson(TypedDict):
    rows: dict[str, int]
    origins: dict[str, dict[str, int]]
    checks_passed: int


class ReportJson(TypedDict):
    format: int
    status: str
    started_at: str | None
    finished_at: str | None
    pokeapi_commit: str | None
    games: list[str]
    blockers: list[BlockerJson]
    warnings: list[str]
    summary: SummaryJson


def report_json(report: LoadReport) -> ReportJson:
    """The report file's content. It has no local paths: it may be registered in git."""
    return {
        "format": REPORT_FORMAT,
        "status": report.status.value,
        "started_at": _iso(report.started_at),
        "finished_at": _iso(report.finished_at),
        "pokeapi_commit": report.pokeapi_commit,
        "games": report.games,
        "blockers": [
            {
                "kind": blocker.kind.value,
                "subject": blocker.subject,
                "occurrences": list(blocker.occurrences),
                "rules": list(blocker.rules),
                "action": blocker.action,
                "template": blocker.template,
            }
            for blocker in report.blockers
        ],
        "warnings": report.warnings,
        "summary": {
            "rows": report.rows_by_table,
            "origins": report.origins_by_table,
            "checks_passed": report.checks_passed,
        },
    }


def report_markdown(data: ReportJson) -> str:
    """The Markdown report, generated from the JSON one, to read or paste in a PR."""
    status = FILE_STATUS.get(data["status"], data["status"])
    lines = [
        f"# Informe de carga: {status}",
        "",
        f"- **Inicio**: {data['started_at'] or '—'}",
        f"- **Fin**: {data['finished_at'] or '—'}",
        f"- **Commit de PokeAPI**: {data['pokeapi_commit'] or '—'}",
        f"- **Juegos**: {', '.join(data['games']) or '—'}",
    ]
    blockers = data["blockers"]
    if blockers:
        lines += ["", "## Resumen", "", "| Bloqueo | Cuántos |", "|---------|---------|"]
        by_kind = Counter(blocker["kind"] for blocker in blockers)
        lines += [f"| `{kind}` | {count} |" for kind, count in by_kind.items()]
        lines += ["", "## Bloqueos"]
        for blocker in blockers:
            lines += [
                "",
                f"### `{blocker['kind']}`: {blocker['subject']}",
                "",
                f"- **Reglas**: {', '.join(blocker['rules'])}",
                f"- **Qué hay que decidir**: {blocker['action']}",
                "- **Dónde aparece**:",
                *(f"    - {occurrence}" for occurrence in blocker["occurrences"]),
            ]
            if blocker["template"] is not None:
                lines += ["", "```yaml", blocker["template"], "```"]
    summary = data["summary"]
    if summary["rows"]:
        lines += ["", "## Filas cargadas", "", "| Tabla | Filas |", "|-------|------:|"]
        lines += [f"| `{table}` | {count} |" for table, count in summary["rows"].items()]
    if summary["origins"]:
        lines += ["", "## Datos revisables por origen", ""]
        for table, origins in summary["origins"].items():
            detail = ", ".join(f"{origin} {count}" for origin, count in origins.items())
            lines.append(f"- `{table}`: {detail}")
    if summary["checks_passed"]:
        lines += ["", f"Comprobaciones superadas: {summary['checks_passed']}."]
    if data["warnings"]:
        lines += ["", "## Avisos", "", *(f"- {warning}" for warning in data["warnings"])]
    return "\n".join(lines) + "\n"


def write_report(report: LoadReport, directory: Path) -> Path | None:
    """Save a completed or blocked load as ``<started>-<status>.json`` and ``.md``, named
    after its local start time.

    Returns the Markdown path, or ``None`` for a failed load, which has no report file.
    """
    status = FILE_STATUS.get(report.status.value)
    if status is None or report.started_at is None:
        return None
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{report.started_at.astimezone().strftime('%Y-%m-%dT%H%M%S')}-{status}"
    data = report_json(report)
    (directory / f"{stem}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = directory / f"{stem}.md"
    markdown.write_text(report_markdown(data), encoding="utf-8")
    return markdown


def _iso(moment: datetime | None) -> str | None:
    """In the local time of the administrator, with its offset."""
    return None if moment is None else moment.astimezone().isoformat(timespec="seconds")


def _count(number: int, singular: str, plural: str) -> str:
    return f"{number} {singular if number == 1 else plural}"


def _listed(items: list[str]) -> str:
    """«a, b y c»."""
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} y {items[-1]}"
