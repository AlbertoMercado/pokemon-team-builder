"""Extraction of key battle teams from WikiDex wikitext.

Trainer pages list each game's teams in a section titled after the games (e.g. "Pokémon
Rojo Fuego y Pokémon Verde Hoja"). Each team is an ``{{Equipo}}`` template with one
parameter per Pokémon (``P1``, ``P2``…) and its level (``NvP1``…). When a section has
several battles, a definition line (``; En Silph S.A.``) precedes each one; several
templates after the same line (often inside a ``<tabber>`` tag, one tab per starter) are
variants of one battle.
"""

import re
from dataclasses import dataclass

import mwparserfromhell
from mwparserfromhell.nodes import Template

TEAM_TEMPLATE = "equipo"
DISAMBIGUATION_MARK = "puede referirse a"
LABEL_LINE = re.compile(r"^;\s*(?P<label>[^\n:]+?)\s*$", re.MULTILINE)
POKEMON_PARAM = re.compile(r"^P(?P<position>\d+)$")


class TeamParseError(Exception):
    """The expected team is not in the wikitext."""


@dataclass(frozen=True)
class TeamMember:
    position: int
    name: str
    level: int | None


def find_section(wikitext: str, title: str) -> str:
    """Text of the only section whose heading is exactly ``title``."""
    code = mwparserfromhell.parse(wikitext)
    sections = [
        section
        for section in code.get_sections(include_lead=False)
        if str(section.filter_headings()[0].title).strip() == title
    ]
    if len(sections) != 1:
        hint = ""
        if DISAMBIGUATION_MARK in wikitext:
            hint = " (parece una página de desambiguación: usa la página del entrenador)"
        raise TeamParseError(f"hay {len(sections)} secciones «{title}», se esperaba una{hint}")
    return str(sections[0])


def team_variants(section: str, label: str | None) -> list[list[TeamMember]]:
    """Teams of a battle in a section: one, or several variants.

    With ``label``, the templates after the ``; label`` line, up to the next label. Without
    it, every template of the section, which then must not have labels.
    """
    labels = list(LABEL_LINE.finditer(section))
    if label is None:
        if labels:
            found = [match.group("label") for match in labels]
            raise TeamParseError(f"la sección tiene varios combates {found}: falta wikidex_team")
        text = section
    else:
        matches = [i for i, match in enumerate(labels) if match.group("label") == label]
        if len(matches) != 1:
            found = [match.group("label") for match in labels]
            raise TeamParseError(f"no hay un combate «{label}»; hay {found}")
        start = labels[matches[0]].end()
        end = labels[matches[0] + 1].start() if matches[0] + 1 < len(labels) else len(section)
        text = section[start:end]

    templates = [
        template
        # Recursive: variants may be inside a <tabber> tag. {{Equipo}} is never nested in
        # another {{Equipo}}, and other templates (move links…) are filtered out by name.
        for template in mwparserfromhell.parse(text).filter_templates(recursive=True)
        if str(template.name).strip().casefold() == TEAM_TEMPLATE
    ]
    if not templates:
        raise TeamParseError("no hay ninguna plantilla {{Equipo}}")
    return [_members(template) for template in templates]


def _members(template: Template) -> list[TeamMember]:
    values = {
        str(param.name).strip(): param.value.strip_code().strip() for param in template.params
    }
    members = []
    for key, name in values.items():
        match = POKEMON_PARAM.match(key)
        if match is None or not name:
            continue
        position = int(match.group("position"))
        level = values.get(f"NvP{position}", "")
        members.append(
            TeamMember(position=position, name=name, level=int(level) if level.isdigit() else None)
        )
    if not members:
        raise TeamParseError("una plantilla {{Equipo}} no tiene Pokémon")
    return sorted(members, key=lambda member: member.position)
