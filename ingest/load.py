"""Load phase of the ingest: build reference.sqlite safely and replace the previous one.

The new database is built in a temporary file next to the target. Only when every row is
stored, the integrity checks pass and the data checks of the load (``ingest/checks.py``)
pass does it replace the previous file, in a single atomic rename. If anything fails, the
previous database is kept untouched (RF-11).
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Connection, Engine, Row, Table, func, select, text
from sqlmodel import Session, col
from sqlmodel import select as select_model

from db.reference import Game, IngestRun, ReferenceModel, create_reference_schema
from db.sqlite import create_sqlite_engine
from ingest.checks import Check
from ingest.report import LoadReport
from ingest.sources import Source

ORIGIN_COLUMN_SUFFIX = "origin"
MAX_DANGLING_VALUES = 5


class IntegrityCheckError(Exception):
    """The freshly built database is not consistent."""


def build_reference(
    sources: Sequence[Source], target: Path, checks: Sequence[Check] = ()
) -> LoadReport:
    """Build reference.sqlite at ``target`` from ``sources`` and report the outcome.

    ``checks`` run on the new database; any problem they report rejects the load.
    """
    report = LoadReport(target=target)
    temporary = target.with_name(f"{target.name}.tmp")
    temporary.unlink(missing_ok=True)
    started_at = datetime.now(UTC)
    engine = create_sqlite_engine(temporary)
    try:
        create_reference_schema(engine)
        _store_rows(engine, sources)
        _check_integrity(engine)
        problems = _run_checks(engine, checks)
        if problems:
            report.errors.extend(f"Comprobación fallida: {problem}" for problem in problems)
        else:
            report.checks_passed = len(checks)
            _record_run(engine, sources, started_at)
            report.rows_by_table = _count_rows(engine)
            report.origins_by_table = _count_origins(engine)
    except Exception as error:  # any failure must keep the previous database
        report.errors.append(f"{type(error).__name__}: {error}")
    finally:
        engine.dispose()

    if report.succeeded:
        temporary.replace(target)
    else:
        temporary.unlink(missing_ok=True)
    return report


def _store_rows(engine: Engine, sources: Sequence[Source]) -> None:
    """Store every row in one transaction, with foreign keys checked afterwards.

    Foreign keys are switched off while inserting, so sources can yield rows in any order,
    even within a table (an evolution before its pre-evolution). ``_check_integrity`` then
    lists every dangling reference with its table, column and value.
    """
    with Session(engine) as session:
        # Must run before the transaction starts: SQLite ignores it inside one.
        session.execute(text("PRAGMA foreign_keys = OFF"))
        try:
            for source in sources:
                session.add_all(source.rows())
            session.commit()
        finally:
            session.execute(text("PRAGMA foreign_keys = ON"))


def _check_integrity(engine: Engine) -> None:
    with engine.connect() as connection:
        integrity = connection.execute(text("PRAGMA integrity_check")).scalar_one()
        if integrity != "ok":
            raise IntegrityCheckError(f"integrity_check: {integrity}")
        dangling = connection.execute(text("PRAGMA foreign_key_check")).all()
        if dangling:
            raise IntegrityCheckError(_describe_dangling(connection, dangling))


def _describe_dangling(
    connection: Connection, dangling: Sequence[Row[tuple[str, int, str, int]]]
) -> str:
    """Summarise dangling references as ``table.column → parent: values``."""
    # Rows of PRAGMA foreign_key_check: (table, rowid, parent table, foreign key id).
    missing: dict[str, set[str]] = defaultdict(set)
    for table, rowid, parent, key_id in dangling:
        keys = connection.execute(text(f"PRAGMA foreign_key_list({table})")).all()
        column = next(key[3] for key in keys if key[0] == key_id)
        value = connection.execute(
            text(f'SELECT "{column}" FROM {table} WHERE rowid = :rowid'), {"rowid": rowid}
        ).scalar_one()
        missing[f"{table}.{column} → {parent}"].add(str(value))
    details = "; ".join(
        f"{reference}: {', '.join(sorted(values)[:MAX_DANGLING_VALUES])}"
        + (" …" if len(values) > MAX_DANGLING_VALUES else "")
        for reference, values in sorted(missing.items())
    )
    return f"{len(dangling)} referencias a filas que no existen ({details})"


def _run_checks(engine: Engine, checks: Sequence[Check]) -> list[str]:
    with Session(engine) as session:
        return [problem for check in checks for problem in check(session)]


def _record_run(engine: Engine, sources: Sequence[Source], started_at: datetime) -> None:
    commits = {source.pokeapi_commit for source in sources} - {None}
    if len(commits) > 1:
        raise IntegrityCheckError(f"varios commits de PokeAPI: {sorted(map(str, commits))}")
    with Session(engine) as session:
        games = list(session.exec(select_model(Game.slug).order_by(col(Game.release_order))).all())
        summary = _count_rows(engine)
        session.add(
            IngestRun(
                started_at=started_at,
                finished_at=datetime.now(UTC),
                pokeapi_commit=next(iter(commits), None),
                games=games,
                summary=summary,
            )
        )
        session.commit()


def _data_tables() -> list[Table]:
    """Reference tables in dependency order, without ``ingest_run`` (metadata of the load)."""
    return [
        table
        for table in ReferenceModel.metadata.sorted_tables
        if table.name != IngestRun.__tablename__
    ]


def _count_rows(engine: Engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {
            table.name: connection.execute(select(func.count()).select_from(table)).scalar_one()
            for table in _data_tables()
        }


def _count_origins(engine: Engine) -> dict[str, dict[str, int]]:
    """Count reviewable values by origin in every ``origin`` / ``*_origin`` column."""
    counts: dict[str, dict[str, int]] = {}
    with engine.connect() as connection:
        for table in _data_tables():
            for column in table.columns:
                if not column.name.endswith(ORIGIN_COLUMN_SUFFIX):
                    continue
                rows = connection.execute(
                    select(column, func.count()).group_by(column).order_by(column)
                )
                for origin, count in rows:
                    by_origin = counts.setdefault(table.name, {})
                    by_origin[origin] = by_origin.get(origin, 0) + count
    return counts
