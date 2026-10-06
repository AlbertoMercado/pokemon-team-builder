"""Load phase of the ingest: build reference.sqlite safely and replace the previous one.

The new database is built in a temporary file next to the target. Only when every row is
stored, the integrity checks pass, the data checks of the load (``ingest/checks.py``) pass
and the keys that user.sqlite uses still exist (``ingest/user_keys.py``) does it replace the
previous file, in a single atomic rename. If anything fails, the previous database is kept
untouched (RF-11, ADR-0003).

Once the rows are stored, each form gets its sprite (ADR-0010). A missing sprite is only a
warning: the form is loaded without image.
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Connection, Engine, Row, Table, func, select, text
from sqlmodel import Session, col
from sqlmodel import select as select_model

from db.reference import Game, IngestRun, Pokemon, ReferenceModel, create_reference_schema
from db.sqlite import create_sqlite_engine
from ingest.checks import Check
from ingest.report import LoadReport
from ingest.sources import Source
from ingest.sources.pokeapi.sprites import MissingReason, MissingSpriteError, SpriteCache
from ingest.user_keys import check_user_keys

ORIGIN_COLUMN_SUFFIX = "origin"
MAX_DANGLING_VALUES = 5
MAX_FORMS_WITHOUT_IMAGE = 10


class IntegrityCheckError(Exception):
    """The freshly built database is not consistent."""


def build_reference(
    sources: Sequence[Source],
    target: Path,
    checks: Sequence[Check] = (),
    user_database: Path | None = None,
    sprites: SpriteCache | None = None,
) -> LoadReport:
    """Build reference.sqlite at ``target`` from ``sources`` and report the outcome.

    If ``sprites`` is given, every form gets the path of its sprite; forms without one are
    reported as warnings.

    ``checks`` run on the new database; any problem they report rejects the load. Then, if
    ``user_database`` is given, the keys of user.sqlite are checked against the new database:
    missing favourites or Hall of Fame data reject it, missing confirmations are warnings.
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
        if sprites is not None:
            _attach_images(engine, sprites, report)
        problems = _run_checks(engine, checks)
        if problems:
            report.errors.extend(f"Comprobación fallida: {problem}" for problem in problems)
        elif user_database is None or not _rejected_by_user_keys(engine, user_database, report):
            report.checks_passed = len(checks)
            _record_run(engine, sources, started_at, sprites)
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


def _attach_images(engine: Engine, sprites: SpriteCache, report: LoadReport) -> None:
    """Store the sprite of every form and report the forms without one."""
    without_image: dict[MissingReason, list[str]] = defaultdict(list)
    with Session(engine) as session:
        forms = session.exec(select_model(Pokemon).order_by(col(Pokemon.pokeapi_id))).all()
        for form in forms:
            try:
                form.image = sprites.image(form.pokeapi_id)
            except MissingSpriteError as error:
                without_image[error.reason].append(form.slug)
        session.commit()
    missing = sum(len(slugs) for slugs in without_image.values())
    report.images = (len(forms) - missing, len(forms))
    for reason, slugs in without_image.items():
        shown = ", ".join(slugs[:MAX_FORMS_WITHOUT_IMAGE])
        more = (
            f" y {len(slugs) - MAX_FORMS_WITHOUT_IMAGE} más"
            if len(slugs) > MAX_FORMS_WITHOUT_IMAGE
            else ""
        )
        forms_text = "1 forma" if len(slugs) == 1 else f"{len(slugs)} formas"
        report.warnings.append(f"{forms_text} sin imagen, {reason}: {shown}{more}")


def _rejected_by_user_keys(engine: Engine, user_database: Path, report: LoadReport) -> bool:
    """Adds the problems with user.sqlite's keys to ``report``; true if they reject the load."""
    with Session(engine) as session:
        problems = check_user_keys(session, user_database)
    report.errors.extend(f"Datos del usuario: {error}" for error in problems.errors)
    report.warnings.extend(problems.warnings)
    return bool(problems.errors)


def _run_checks(engine: Engine, checks: Sequence[Check]) -> list[str]:
    with Session(engine) as session:
        return [problem for check in checks for problem in check(session)]


def _record_run(
    engine: Engine, sources: Sequence[Source], started_at: datetime, sprites: SpriteCache | None
) -> None:
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
                sprites_commit=sprites.commit if sprites is not None else None,
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
