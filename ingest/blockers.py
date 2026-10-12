"""Blockers of a load: what the application cannot handle without a new version (ADR-0008).

Unlike an error, a blocker does not stop the load: every one is collected, the previous
reference.sqlite is kept and the CLI ends with exit code 2 (RF-16). Each blocker says what
it is, where it appears, which rules it affects, what the architect must decide and, when
possible, a template to complete. The kinds are described in docs/05-operacion/ingesta.md,
section "Carga bloqueada".

Sources report the blockers found while reading (a key battle team not found in WikiDex);
``find_data_blockers`` finds those that need the whole data: evolution triggers and conditions
that are not in the catalog of evolution methods (CA-42), and those whose category depends on
the moves learnt by level, which are not loaded (CA-45).
"""

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from sqlmodel import Session, col, select

from db.reference import EvolutionMethod, EvolutionStep, MethodKind

EVOLUTION_RULES = ("RN-15", "RN-20")


class BlockerKind(StrEnum):
    """What blocks the load; the values are part of the report format."""

    UNKNOWN_EVOLUTION_TRIGGER = "unknown_evolution_trigger"
    UNKNOWN_EVOLUTION_CONDITION = "unknown_evolution_condition"
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
    """Blockers that need the stored rows: the evolution steps whose methods are not in the
    catalog (CA-42) or need the moves learnt by level (CA-45).

    The moves learnt by level (``level_move``) are not loaded, so a step with a condition
    marked ``unless_learnt_by_level`` blocks the load: whether it is tedious depends on them
    (CA-32). One blocker per unknown method, or per required move, with every step.
    """
    catalog = {
        (method.kind, method.name): method for method in session.exec(select(EvolutionMethod))
    }
    unknown_triggers: dict[str, list[str]] = defaultdict(list)
    unknown_conditions: dict[str, list[str]] = defaultdict(list)
    by_move: dict[str, list[str]] = defaultdict(list)
    steps = session.exec(select(EvolutionStep).order_by(col(EvolutionStep.id))).all()
    for step in steps:
        where = f"{step.from_pokemon} → {step.to_pokemon} ({step.version_group})"
        if (MethodKind.TRIGGER, step.trigger) not in catalog:
            unknown_triggers[step.trigger].append(where)
        for name, value in step.conditions.items():
            method = catalog.get((MethodKind.CONDITION, name))
            if method is None:
                unknown_conditions[name].append(where)
            elif method.unless_learnt_by_level:
                by_move[str(value)].append(where)
    return [
        *(
            _unknown_method(BlockerKind.UNKNOWN_EVOLUTION_TRIGGER, "triggers", name, where)
            for name, where in sorted(unknown_triggers.items())
        ),
        *(
            _unknown_method(BlockerKind.UNKNOWN_EVOLUTION_CONDITION, "conditions", name, where)
            for name, where in sorted(unknown_conditions.items())
        ),
        *(
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
        ),
    ]


def _unknown_method(kind: BlockerKind, section: str, name: str, where: list[str]) -> Blocker:
    what = "el disparador" if section == "triggers" else "la condición"
    return Blocker(
        kind=kind,
        subject=name,
        occurrences=tuple(where),
        rules=EVOLUTION_RULES,
        action=(
            f"Catalogar {what} en data/curated/evolution_methods.yaml: no tedioso (easy), "
            "tedioso con su motivo (tedious) o aleatorio (random)"
        ),
        template=f"{section}:\n  {name}: {{category: ???, reason: ???}}",
    )
