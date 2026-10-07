"""Requests and responses of the rule settings (RF-06, RF-07)."""

from pydantic import BaseModel, Field, model_validator

from core.rules.catalog import MAX_WEIGHT, MIN_WEIGHT, RuleKind


class RuleOut(BaseModel):
    rule_id: str = Field(description="Identificador del DDF, p. ej. `RN-17`.")
    name: str = Field(description="Nombre en español.")
    description: str = Field(description="Qué hace la regla, en una frase.")
    kind: RuleKind = Field(
        description="`hard` (filtro), `presence` (obliga a incluir un tipo de miembro), "
        "`soft` (puntúa) o `mechanism` (cómo funciona el motor)."
    )
    configurable: bool = Field(description="Si el usuario la puede activar y desactivar.")
    enabled: bool = Field(description="Si está activa.")
    weight: int | None = Field(description="Peso actual, solo en las reglas blandas.")
    default_weight: int | None = Field(description="Peso por defecto, solo en las blandas.")


class RulePatch(BaseModel):
    """What to change; at least one of the two."""

    enabled: bool | None = Field(
        default=None,
        description="Activarla (`true`) o desactivarla (`false`); solo en las configurables.",
    )
    weight: int | None = Field(
        default=None,
        ge=MIN_WEIGHT,
        le=MAX_WEIGHT,
        description="Peso nuevo, de 0 a 10; solo en las blandas.",
    )

    @model_validator(mode="after")
    def _something(self) -> "RulePatch":
        if self.enabled is None and self.weight is None:
            raise ValueError("indica enabled, weight o los dos")
        return self
