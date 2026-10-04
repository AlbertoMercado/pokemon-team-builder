"""Static catalogue of business rules (CA-10) and the user's settings (RF-06, RF-07).

Every rule of the DDF (docs/01-ddf/reglas-negocio.md) is listed here with its kind, whether
the user can switch it on and off, and its default weight if it is soft (CA-05, CA-37). By
default every configurable rule is active (CA-41).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

MIN_WEIGHT = 0
MAX_WEIGHT = 10


class RuleKind(StrEnum):
    HARD = "hard"  # filter: a candidate or team that breaks it is discarded
    PRESENCE = "presence"  # hard rule that forces a kind of member into the team
    SOFT = "soft"  # weighted score between 0 and 1
    MECHANISM = "mechanism"  # how the engine works, not a filter or a score


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    name: str
    kind: RuleKind
    configurable: bool
    default_weight: int | None = None


def _rule(
    rule_id: str,
    name: str,
    kind: RuleKind,
    *,
    configurable: bool = False,
    default_weight: int | None = None,
) -> RuleDefinition:
    return RuleDefinition(rule_id, name, kind, configurable, default_weight)


_HARD, _PRESENCE, _SOFT, _MECHANISM = (
    RuleKind.HARD,
    RuleKind.PRESENCE,
    RuleKind.SOFT,
    RuleKind.MECHANISM,
)

CATALOG: Mapping[str, RuleDefinition] = MappingProxyType(
    {
        rule.rule_id: rule
        for rule in (
            _rule("RN-01", "El equipo tiene 6 Pokémon", _HARD),
            _rule("RN-02", "Solo se eligen Pokémon favoritos", _HARD),
            _rule("RN-03", "Solo Pokémon de la generación y del juego objetivo", _HARD),
            _rule("RN-04", "Equipos con mayor puntuación ponderada", _MECHANISM),
            _rule("RN-05", "Cada forma regional es un Pokémon distinto", _HARD),
            _rule(
                "RN-06",
                "Penalizar varias formas de la misma especie",
                _SOFT,
                configurable=True,
                default_weight=1,
            ),
            _rule("RN-07", "Sin líneas evolutivas repetidas", _HARD, configurable=True),
            _rule("RN-08", "Equipo incompleto y sugerencias", _MECHANISM),
            _rule("RN-09", "Cada favorito marca la evolución a la que llegar", _HARD),
            _rule("RN-10", "Datos tal como son en el juego objetivo", _MECHANISM),
            _rule("RN-11", "Solo Pokémon que se pueden criar", _HARD, configurable=True),
            _rule("RN-12", "Sin tipos repetidos en el equipo", _HARD, configurable=True),
            _rule(
                "RN-13",
                "Dragonite o un Pokémon de tipo primario Dragón",
                _PRESENCE,
                configurable=True,
            ),
            _rule("RN-14", "Una evolución de Eevee, y solo una", _PRESENCE, configurable=True),
            _rule(
                "RN-15",
                "Penalizar evoluciones tediosas",
                _SOFT,
                configurable=True,
                default_weight=3,
            ),
            _rule("RN-16", "Excluir Pokémon ya usados en el recorrido", _HARD, configurable=True),
            _rule(
                "RN-17",
                "Tipos eficaces frente a los combates clave",
                _SOFT,
                configurable=True,
                default_weight=10,
            ),
            _rule("RN-18", "Los datos sin verificar los confirma el usuario", _MECHANISM),
            _rule("RN-19", "A igual puntuación, Pokémon con dos tipos", _MECHANISM),
            _rule(
                "RN-20",
                "Penalizar las evoluciones aleatorias",
                _SOFT,
                configurable=True,
                default_weight=5,
            ),
        )
    }
)


class SettingsError(ValueError):
    """A settings change is not allowed (unknown rule, not configurable, invalid weight)."""


def _definition(rule_id: str) -> RuleDefinition:
    try:
        return CATALOG[rule_id]
    except KeyError:
        raise SettingsError(f"la regla {rule_id} no existe en el catálogo") from None


@dataclass(frozen=True)
class RuleSettings:
    """Which configurable rules are active and the weight of each soft rule (RN-04).

    Build it with ``defaults()`` and change it with ``with_changes``. Rules that are not
    configurable are always active. Not hashable: ``weights`` is a read-only mapping.
    """

    disabled: frozenset[str]
    weights: Mapping[str, int]

    @classmethod
    def defaults(cls) -> "RuleSettings":
        weights = {
            rule.rule_id: rule.default_weight
            for rule in CATALOG.values()
            if rule.default_weight is not None
        }
        return cls(disabled=frozenset(), weights=MappingProxyType(weights))

    def with_changes(
        self,
        *,
        enabled: Mapping[str, bool] | None = None,
        weights: Mapping[str, int] | None = None,
    ) -> "RuleSettings":
        """A copy with some rules switched on or off and some weights changed."""
        disabled = set(self.disabled)
        for rule_id, active in (enabled or {}).items():
            if not _definition(rule_id).configurable:
                raise SettingsError(f"la regla {rule_id} no se puede desactivar")
            if active:
                disabled.discard(rule_id)
            else:
                disabled.add(rule_id)
        new_weights = dict(self.weights)
        for rule_id, weight in (weights or {}).items():
            if _definition(rule_id).kind is not RuleKind.SOFT:
                raise SettingsError(f"la regla {rule_id} no es blanda: no tiene peso")
            if not MIN_WEIGHT <= weight <= MAX_WEIGHT:
                raise SettingsError(
                    f"el peso de {rule_id} es {weight}; "
                    f"debe estar entre {MIN_WEIGHT} y {MAX_WEIGHT}"
                )
            new_weights[rule_id] = weight
        return RuleSettings(disabled=frozenset(disabled), weights=MappingProxyType(new_weights))

    def is_enabled(self, rule_id: str) -> bool:
        return rule_id not in self.disabled or not _definition(rule_id).configurable

    def weight(self, rule_id: str) -> int:
        if _definition(rule_id).kind is not RuleKind.SOFT:
            raise SettingsError(f"la regla {rule_id} no es blanda: no tiene peso")
        return self.weights[rule_id]

    def active_soft_rules(self) -> tuple[str, ...]:
        """Active soft rules, in catalogue order."""
        return tuple(
            rule.rule_id
            for rule in CATALOG.values()
            if rule.kind is RuleKind.SOFT and self.is_enabled(rule.rule_id)
        )
