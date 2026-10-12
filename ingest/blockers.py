"""Blockers of a load: what the application cannot handle without a new version (ADR-0008).

Unlike an error, a blocker does not stop the load: every one is collected, the previous
reference.sqlite is kept and the CLI ends with exit code 2 (RF-16). Each blocker says what
it is, where it appears, which rules it affects, what the architect must decide and, when
possible, a template to complete. The kinds are described in docs/05-operacion/ingesta.md,
section "Carga bloqueada".

Sources report the blockers found while reading (a key battle team not found in WikiDex);
``find_data_blockers`` finds those that need the whole data (an evolution by move).
"""

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from sqlmodel import Session, col, select

from db.reference import EvolutionStep

# Condition of an evolution step that needs the moves learnt by level (CA-32, CA-45).
KNOWN_MOVE_CONDITION = "known_move"


class BlockerKind(StrEnum):
    """What blocks the load; the values are part of the report format."""

    MISSING_LEVEL_MOVES = "missing_level_moves"
    WIKIDEX_TEAM_NOT_FOUND = "wikidex_team_not_found"


@dataclass(frozen=True)
class Blocker:
    """Something the load cannot handle, with what the architect needs to resolve it.

    ``subject`` is what is unknown or missing; ``occurrences``, where it appears. ``action``
    is what has to be decided and ``template``, if any, the text to complete and copy.
    """

    kind: BlockerKind
    subject: str
    occurrences: tuple[str, ...]
    rules: tuple[str, ...]
    action: str
    template: str | None = None


def wikidex_team_not_found(
    battle: str, page: str, section: str, team: str | None, problem: str
) -> Blocker:
    """A curated key battle whose team is not on its WikiDex page (RN-17)."""
    where = f"página «{page}», sección «{section}»"
    if team is not None:
        where += f", combate «{team}»"
    return Blocker(
        kind=BlockerKind.WIKIDEX_TEAM_NOT_FOUND,
        subject=battle,
        occurrences=(f"{where}: {problem}",),
        rules=("RN-17",),
        action=(
            "Corregir la página (wikidex_page), el rótulo del combate (wikidex_team) o la "
            "sección (wikidex_section) en data/curated/key_battles/"
        ),
        template=f"- id: {battle}\n  wikidex_page: {page}\n  wikidex_team: ???",
    )


def find_data_blockers(session: Session) -> list[Blocker]:
    """Blockers that need the stored rows: evolutions by move without level moves (CA-45).

    The moves learnt by level (``level_move``) are not loaded, so any step that needs a
    known move blocks the load: whether it is tedious depends on them (CA-32).
    """
    by_move: dict[str, list[str]] = defaultdict(list)
    steps = session.exec(select(EvolutionStep).order_by(col(EvolutionStep.id))).all()
    for step in steps:
        move = step.conditions.get(KNOWN_MOVE_CONDITION)
        if move is not None:
            by_move[str(move)].append(
                f"{step.from_pokemon} → {step.to_pokemon} ({step.version_group})"
            )
    return [
        Blocker(
            kind=BlockerKind.MISSING_LEVEL_MOVES,
            subject=move,
            occurrences=tuple(occurrences),
            rules=("RN-15",),
            action=(
                "Cargar los movimientos que se aprenden por nivel (tabla level_move, CA-45) "
                "para saber si el paso es tedioso (CA-32)"
            ),
        )
        for move, occurrences in sorted(by_move.items())
    ]
