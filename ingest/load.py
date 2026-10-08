"""Load phase of the ingest: build reference.sqlite safely and replace the previous one.

The new database is built in a temporary file next to the target. Only when every row is
stored, the integrity checks pass, the data checks of the load (``ingest/checks.py``) pass
and the keys that user.sqlite uses still exist (``ingest/user_keys.py``) does it replace the
previous file, in a single atomic rename. If anything fails, the previous database is kept
untouched (RF-11, ADR-0003).

Once the rows are stored, only the complete games stay as target games (``ingest/targets.py``,
RF-05); the others are reported with what they lack. Locations without a Spanish name are
reported as a warning, since the English one is shown (ADR-0013). Each form gets its images,
the trimmed sprite and the official artwork (ADR-0010), and each game its cover (ADR-0011). A
missing image is only a warning: the form or the game is loaded without it.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Connection, Engine, Row, Table, func, select, text
from sqlmodel import Session, col
from sqlmodel import select as select_model

from db.reference import (
    Game,
    IngestRun,
    Location,
    Pokemon,
    ReferenceModel,
    create_reference_schema,
)
from db.sqlite import create_sqlite_engine
from ingest.checks import Check
from ingest.report import LoadReport
from ingest.sources import Source
from ingest.sources.pokeapi.sprites import MissingReason, MissingSpriteError, SpriteCache
from ingest.sources.wikidex.covers import CoverCache, CoverMissing, MissingCoverError
from ingest.targets import mark_incomplete_games
from ingest.user_keys import check_user_keys

ORIGIN_COLUMN_SUFFIX = "origin"
MAX_DANGLING_VALUES = 5
MAX_FORMS_WITHOUT_IMAGE = 10
MAX_UNNAMED_LOCATIONS = 10


@dataclass(frozen=True)
class Images:
    """Where the images of a load come from: the forms' (ADR-0010) and the games' covers
    (ADR-0011). ``None`` leaves them out."""

    sprites: SpriteCache | None = None
    covers: CoverCache | None = None


class IntegrityCheckError(Exception):
    """The freshly built database is not consistent."""


def build_reference(
    sources: Sequence[Source],
    target: Path,
    checks: Sequence[Check] = (),
    user_database: Path | None = None,
    images: Images | None = None,
) -> LoadReport:
    """Build reference.sqlite at ``target`` from ``sources`` and report the outcome.

    With ``images``, every form gets the paths of its images and every game its cover; those
    without them are reported as warnings.

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
        _mark_target_games(engine, report)
        _report_unnamed_locations(engine, report)
        if images is not None and images.sprites is not None:
            _attach_images(engine, images.sprites, report)
        if images is not None and images.covers is not None:
            _attach_covers(engine, images.covers, report)
        problems = _run_checks(engine, checks)
        if problems:
            report.errors.extend(f"Comprobación fallida: {problem}" for problem in problems)
        elif user_database is None or not _rejected_by_user_keys(engine, user_database, report):
            report.checks_passed = len(checks)
            _record_run(engine, sources, started_at, images.sprites if images else None)
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


def _mark_target_games(engine: Engine, report: LoadReport) -> None:
    """Only the complete games stay as target; the report lists the others (CA-67)."""
    with Session(engine) as session:
        report.incomplete_games = mark_incomplete_games(session)
        session.commit()


def _report_unnamed_locations(engine: Engine, report: LoadReport) -> None:
    """Warn about the locations without a Spanish name, which show the English one."""
    with Session(engine) as session:
        query = select_model(Location.slug).where(col(Location.name_es).is_(None))
        slugs = list(session.exec(query.order_by(col(Location.slug))).all())
    if not slugs:
        return
    shown = ", ".join(slugs[:MAX_UNNAMED_LOCATIONS])
    more = (
        f" y {len(slugs) - MAX_UNNAMED_LOCATIONS} más" if len(slugs) > MAX_UNNAMED_LOCATIONS else ""
    )
    places = "1 lugar" if len(slugs) == 1 else f"{len(slugs)} lugares"
    report.warnings.append(
        f"{places} sin nombre en español, se muestra el inglés "
        f"(añádelo a data/curated/locations.yaml): {shown}{more}"
    )


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
    """Store the images of every form (trimmed sprite and artwork) and report those without."""
    without_image: dict[MissingReason, list[str]] = defaultdict(list)
    without_artwork: dict[MissingReason, list[str]] = defaultdict(list)
    with Session(engine) as session:
        forms = session.exec(select_model(Pokemon).order_by(col(Pokemon.pokeapi_id))).all()
        for form in forms:
            try:
                form.image = sprites.image(form.pokeapi_id)
            except MissingSpriteError as error:
                without_image[error.reason].append(form.slug)
            try:
                form.artwork = sprites.artwork(form.pokeapi_id)
            except MissingSpriteError as error:
                without_artwork[error.reason].append(form.slug)
        session.commit()
    report.images = _found(len(forms), without_image)
    report.artworks = _found(len(forms), without_artwork)
    report.warnings.extend(_missing_warnings("imagen", without_image))
    report.warnings.extend(_missing_warnings("ilustración", without_artwork))


def _attach_covers(engine: Engine, covers: CoverCache, report: LoadReport) -> None:
    """Store the cover of every game and report the games without one."""
    without_cover: dict[CoverMissing, list[str]] = defaultdict(list)
    with Session(engine) as session:
        games = session.exec(select_model(Game).order_by(col(Game.release_order))).all()
        for game in games:
            try:
                game.cover, game.cover_source = covers.cover(game.slug)
            except MissingCoverError as error:
                without_cover[error.reason].append(game.slug)
        session.commit()
    missing = sum(len(slugs) for slugs in without_cover.values())
    report.covers = (len(games) - missing, len(games))
    for reason, slugs in without_cover.items():
        games_text = "1 juego" if len(slugs) == 1 else f"{len(slugs)} juegos"
        report.warnings.append(f"{games_text} sin portada, {reason}: {', '.join(slugs)}")


def _found(forms: int, missing: dict[MissingReason, list[str]]) -> tuple[int, int]:
    return forms - sum(len(slugs) for slugs in missing.values()), forms


def _missing_warnings(what: str, missing: dict[MissingReason, list[str]]) -> list[str]:
    """One warning per reason: «2 formas sin imagen, <reason>: bulbasaur, ivysaur»."""
    warnings = []
    for reason, slugs in missing.items():
        shown = ", ".join(slugs[:MAX_FORMS_WITHOUT_IMAGE])
        more = (
            f" y {len(slugs) - MAX_FORMS_WITHOUT_IMAGE} más"
            if len(slugs) > MAX_FORMS_WITHOUT_IMAGE
            else ""
        )
        forms_text = "1 forma" if len(slugs) == 1 else f"{len(slugs)} formas"
        warnings.append(f"{forms_text} sin {what}, {reason}: {shown}{more}")
    return warnings


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
