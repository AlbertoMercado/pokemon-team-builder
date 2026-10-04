"""Load phase of the ingest: build reference.sqlite safely and replace the previous one.

The new database is built in a temporary file next to the target. Only when every row is
stored and the integrity checks pass does it replace the previous file, in a single atomic
rename. If anything fails, the previous database is kept untouched (RF-11).
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, Table, func, select, text
from sqlmodel import Session, col
from sqlmodel import select as select_model

from db.reference import Game, IngestRun, ReferenceModel, create_reference_schema
from db.sqlite import create_sqlite_engine
from ingest.report import LoadReport
from ingest.sources import Source

ORIGIN_COLUMN_SUFFIX = "origin"


class IntegrityCheckError(Exception):
    """The freshly built database is not consistent."""


def build_reference(sources: Sequence[Source], target: Path) -> LoadReport:
    """Build reference.sqlite at ``target`` from ``sources`` and report the outcome."""
    report = LoadReport(target=target)
    temporary = target.with_name(f"{target.name}.tmp")
    temporary.unlink(missing_ok=True)
    started_at = datetime.now(UTC)
    engine = create_sqlite_engine(temporary)
    try:
        create_reference_schema(engine)
        _store_rows(engine, sources)
        _check_integrity(engine)
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
    """Store every row in one transaction, checking foreign keys only at commit.

    Deferring the checks lets sources yield rows in any order, even within a table (an
    evolution before its pre-evolution), while still rejecting dangling references.
    """
    with Session(engine) as session:
        session.execute(text("PRAGMA defer_foreign_keys = ON"))
        for source in sources:
            session.add_all(source.rows())
        session.commit()


def _check_integrity(engine: Engine) -> None:
    with engine.connect() as connection:
        integrity = connection.execute(text("PRAGMA integrity_check")).scalar_one()
        if integrity != "ok":
            raise IntegrityCheckError(f"integrity_check: {integrity}")
        dangling = connection.execute(text("PRAGMA foreign_key_check")).all()
        if dangling:
            raise IntegrityCheckError(f"claves foráneas rotas: {dangling}")


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
