"""Report files of the ingest: JSON with a stable format and Markdown generated from it, for
the completed and the blocked loads (ADR-0008, docs/05-operacion/ingesta.md#informe)."""

import json
from datetime import UTC, datetime
from pathlib import Path

from ingest.blockers import wikidex_team_not_found
from ingest.report import LoadReport, report_json, report_markdown, write_report

STARTED = datetime(2026, 11, 2, 10, 15, tzinfo=UTC)
BLOCKER = wikidex_team_not_found(
    "brock", "Brock", "Pokémon Rojo Fuego y Pokémon Verde Hoja", "Revancha", "no hay un combate"
)


def _blocked(target: Path) -> LoadReport:
    return LoadReport(
        target=target,
        blockers=[BLOCKER],
        started_at=STARTED,
        finished_at=STARTED,
        pokeapi_commit="bc92d3b",
        games=["firered", "leafgreen"],
    )


def test_the_json_report_has_the_documented_format(tmp_path: Path) -> None:
    data = report_json(_blocked(tmp_path / "reference.sqlite"))

    assert list(data) == [
        "format",
        "status",
        "started_at",
        "finished_at",
        "pokeapi_commit",
        "games",
        "blockers",
        "warnings",
        "summary",
    ]
    assert (data["format"], data["status"], data["pokeapi_commit"]) == (1, "blocked", "bc92d3b")
    assert data["blockers"][0] == {
        "kind": "wikidex_team_not_found",
        "subject": "brock",
        "occurrences": [
            "página «Brock», sección «Pokémon Rojo Fuego y Pokémon Verde Hoja», "
            "combate «Revancha»: no hay un combate"
        ],
        "rules": ["RN-17"],
        "action": BLOCKER.action,
        "template": "- id: brock\n  wikidex_page: Brock\n  wikidex_team: ???",
    }
    assert data["summary"] == {"rows": {}, "origins": {}, "checks_passed": 0}
    # It may be registered in git: no local path of the administrator's computer.
    assert str(tmp_path) not in json.dumps(data)


def test_the_markdown_lists_each_blocker_with_its_template() -> None:
    markdown = report_markdown(report_json(_blocked(Path("reference.sqlite"))))

    assert markdown.startswith("# Informe de carga: bloqueada\n")
    assert "- **Commit de PokeAPI**: bc92d3b" in markdown
    assert "| `wikidex_team_not_found` | 1 |" in markdown
    assert "### `wikidex_team_not_found`: brock" in markdown
    assert "```yaml\n- id: brock\n  wikidex_page: Brock\n  wikidex_team: ???\n```" in markdown


def test_a_completed_report_has_the_usual_summary() -> None:
    report = LoadReport(
        target=Path("reference.sqlite"),
        rows_by_table={"species": 386},
        origins_by_table={"game_pokemon": {"automatic": 1930}},
        checks_passed=13,
        warnings=["1 juego sin portada"],
        started_at=STARTED,
    )

    markdown = report_markdown(report_json(report))

    assert markdown.startswith("# Informe de carga: completada\n")
    assert "## Bloqueos" not in markdown
    assert "| `species` | 386 |" in markdown
    assert "- `game_pokemon`: automatic 1930" in markdown
    assert "Comprobaciones superadas: 13." in markdown
    assert "- 1 juego sin portada" in markdown


def test_both_files_are_named_after_the_start_and_the_status(tmp_path: Path) -> None:
    written = write_report(_blocked(Path("reference.sqlite")), tmp_path / "reports")

    stem = STARTED.astimezone().strftime("%Y-%m-%dT%H%M%S")
    assert written == tmp_path / "reports" / f"{stem}-bloqueada.md"
    json_file = written.with_suffix(".json")
    assert json.loads(json_file.read_text(encoding="utf-8"))["status"] == "blocked"


def test_a_failed_load_has_no_report_file(tmp_path: Path) -> None:
    report = LoadReport(target=Path("reference.sqlite"), errors=["fallo"], started_at=STARTED)

    assert write_report(report, tmp_path / "reports") is None
    assert not (tmp_path / "reports").exists()
