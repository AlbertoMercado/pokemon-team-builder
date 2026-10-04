"""Reads the record of the load that built reference.sqlite."""

from sqlmodel import Session, select

from db.reference import IngestRun


def ingest_run(reference: Session) -> IngestRun | None:
    return reference.exec(select(IngestRun)).first()
