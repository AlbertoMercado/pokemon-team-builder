"""Requests and responses of the Pokédex of the completed games (RF-20 to RF-24)."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from core.pokedex import EncounterKind, MethodKind, PokedexStatus
from db.user import DexStatus


class PokedexProgressOut(BaseModel):
    registered: int = Field(description="Pokémon registrados (capturados u obtenidos, CA-69).")
    total: int = Field(description="Pokémon de la Pokédex del juego (RN-22).")
    impossible: int = Field(
        description="Pokémon sin registrar imposibles de obtener: los marcados por el usuario y "
        "los que solo se obtienen en spin-offs (RN-25). Cuentan en el total (CA-71)."
    )
    percent: int = Field(
        description="Porcentaje de registrados sobre el total, redondeado hacia abajo: 100 solo "
        "con la Pokédex completa (RN-22)."
    )
    status: PokedexStatus = Field(
        description="`not_started` hasta confirmar la lista inicial (RF-21), `in_progress` o "
        "`completed` con todos registrados."
    )


class PokedexGameOut(BaseModel):
    game: str = Field(description="Identificador del juego superado.")
    game_name: str = Field(description="Nombre en español del juego.")
    cover_url: str | None = Field(
        description="URL de su portada en esta API; nula si no tiene (RF-18)."
    )
    hall_of_fame_entry: int = Field(description="El registro del *Hall of Fame* del juego.")
    progress: PokedexProgressOut = Field(description="Progreso de su Pokédex (RN-22).")


class PokedexSpeciesOut(BaseModel):
    species: str = Field(description="Identificador de la especie: la Pokédex registra especies.")
    number: int = Field(description="Número en la Pokédex del juego, que da su orden (RN-23).")
    name: str = Field(description="Nombre en español.")
    pokemon: str = Field(description="Su forma base, la de su imagen y sus tipos.")
    types: list[str] = Field(description="Tipos en la generación del juego (RN-10).")
    image_url: str | None = Field(
        description="URL de su imagen en esta API; nula si no tiene (RF-17)."
    )
    status: DexStatus | None = Field(
        description="`registered`, `impossible` (marcado por el usuario) o nulo si no está "
        "marcado (RF-21, RF-22)."
    )
    automatically_impossible: bool = Field(
        description="Si solo se obtiene en spin-offs, sin ninguna otra forma (RN-25)."
    )


class PokedexOut(BaseModel):
    game: str = Field(description="Identificador del juego superado.")
    game_name: str = Field(description="Nombre en español del juego.")
    hall_of_fame_entry: int = Field(description="El registro del *Hall of Fame* del juego.")
    progress: PokedexProgressOut = Field(description="Progreso de la Pokédex (RN-22).")
    species: list[PokedexSpeciesOut] = Field(
        description="Todos los Pokémon de la Pokédex, en su orden (RF-21, RF-24)."
    )


class InitialListIn(BaseModel):
    registered: list[str] = Field(
        description="Las especies que el usuario ya tiene registradas; puede estar vacía (RF-21)."
    )


class SpeciesRefOut(BaseModel):
    species: str = Field(description="Identificador de la especie.")
    name: str = Field(description="Nombre en español.")


class WayOut(BaseModel):
    """A way of obtaining it from the encounters of a game (RN-26)."""

    kind: EncounterKind = Field(
        description="`gift`, `npc_trade`, `fossil`, `static`, `wild`, `swarm` (salvaje en "
        "enjambre), `roaming`, `starter_gift` (depende del inicial) o `event` (RN-26, CA-82 a "
        "CA-87)."
    )
    location: str = Field(description="Identificador del lugar.")
    location_name: str = Field(
        description="Nombre del lugar en español; en inglés si no se conoce."
    )
    area: str | None = Field(description="Zona del lugar (`b1f`); nula si solo tiene una.")
    method: str = Field(description="Método de PokeAPI (`walk`, `surf`, `gift`…).")
    rarity: int = Field(
        description="Probabilidad, en %, de encontrarlo en esa zona con ese método; con "
        "`times`, la mayor de esos momentos (CA-81)."
    )
    times: list[str] = Field(
        description="Momentos del día (`morning`, `day`, `night`) en que tiene esa "
        "probabilidad; vacío si no depende de la hora (CA-81)."
    )
    choice: str | None = Field(
        description="La elección de la que depende: `starter-<especie>` (el inicial elegido, "
        "CA-80, CA-87) o `tv-option-<color>` (la televisión de Esmeralda, CA-85)."
    )
    item: str | None = Field(
        description="El fósil que se revive o el objeto de evento con el que se llega al lugar "
        "(CA-82)."
    )
    conditions: list[str] = Field(
        description="El resto de condiciones de PokeAPI, para mostrarlas con la forma "
        "(`coins-9999`, `trade-abra`, `weekday-friday`…; CA-83, CA-85)."
    )
    alternatives: list[SpeciesRefOut] = Field(
        description="Los demás Pokémon de un regalo en el que se elige uno (CA-87)."
    )


class DexEvolutionOut(BaseModel):
    trigger: str = Field(description="Disparador de PokeAPI (`level-up`, `use-item`, `trade`…).")
    conditions: dict[str, str | int | bool] = Field(
        description="Condiciones de PokeAPI (`minimum_level`, `trigger_item`…)."
    )


class ObtentionMethodOut(BaseModel):
    key: str = Field(description="Identificador estable de la forma, para elegirla (RF-23).")
    kind: MethodKind = Field(
        description="`evolve`, `breed_registered` (1), `transfer_registered` (2), `in_game` (3), "
        "`breed` (4), `transfer` (5), `starter_gift` (6) o `event` (7), en el orden de RN-24."
    )
    recommended: bool = Field(description="Si es la más sencilla (RN-24).")
    chosen: bool = Field(description="Si es la que eligió el usuario (RF-23, CA-75).")
    way: WayOut | None = Field(
        description="Dónde se obtiene: en el juego, en un regalo que depende del inicial, en un "
        "evento con lugar o, al transferirlo de un juego no superado, allí."
    )
    game: str | None = Field(description="Juego desde el que se transfiere (RN-25).")
    game_name: str | None = Field(description="Nombre en español de ese juego.")
    pokemon: str | None = Field(description="Especie que se evoluciona o se cría.")
    pokemon_name: str | None = Field(description="Nombre en español de esa especie.")
    pokemon_registered: bool = Field(
        description="Si esa especie está registrada; si no, la ficha enlaza a la suya (CA-76)."
    )
    evolution: DexEvolutionOut | None = Field(description="El paso de evolución, al evolucionarlo.")
    incense: bool = Field(description="Si criarlo exige que el progenitor lleve un incienso.")


class PokedexPokemonOut(PokedexSpeciesOut):
    artwork_url: str | None = Field(
        description="URL de su ilustración oficial en esta API; nula si no tiene."
    )
    chosen_method: str | None = Field(
        description="Clave de la forma elegida por el usuario; nula si sigue la recomendada."
    )
    methods: list[ObtentionMethodOut] = Field(
        description="Todas las formas de obtenerlo, de la más sencilla a la menos (RN-24); "
        "vacía si no se conoce ninguna."
    )


class ObjectiveOut(BaseModel):
    pokemon: PokedexPokemonOut | None = Field(
        description="La ficha del Pokémon objetivo; nula si no queda ninguno por registrar "
        "(RN-23, RF-22)."
    )


class PokedexMarkIn(BaseModel):
    """What to change; at least one field."""

    status: Literal["registered", "impossible"] | None = Field(
        default=None,
        description="`registered`, `impossible` o `null` para desmarcarlo (RF-22, RF-24).",
    )
    chosen_method: str | None = Field(
        default=None,
        description="Clave de una de sus formas (`key`), o `null` para volver a la recomendada "
        "(RF-23).",
    )

    @model_validator(mode="after")
    def _something(self) -> "PokedexMarkIn":
        if not self.model_fields_set:
            raise ValueError("indica al menos un campo")
        return self
