"""Requests and responses of the game catalogue (RF-25): its games, what the user chose and why a
game cannot be a target game (RF-05, CA-90 to CA-93)."""

from pydantic import BaseModel, Field, model_validator


class ReasonOut(BaseModel):
    code: str = Field(description="Código estable, p. ej. `not_playable` o `key_battles`.")
    text: str = Field(description="El motivo en español, para mostrarlo.")


class CatalogGameOut(BaseModel):
    game: str = Field(description="Identificador del juego, el de PokeAPI, p. ej. `firered`.")
    name: str = Field(description="Nombre en español.")
    generation: int = Field(description="Generación del juego.")
    platform: str = Field(
        description="Plataforma: `game_boy`, `game_boy_color`, `game_boy_advance`, `ds`, `3ds` o "
        "`switch`."
    )
    receives_bred: bool = Field(
        description="Si puede recibir un Pokémon criado, en el propio juego o por transferencia "
        "(CA-29, CA-91)."
    )
    known_playable: bool = Field(
        description="Si se sabe que es jugable en un sistema actual de Nintendo (los de Switch). "
        "Si no, se pregunta al usuario (CA-92)."
    )
    playable: bool | None = Field(
        description="Si es jugable en un sistema actual: verdadero si se sabe; si no, la "
        "respuesta del usuario, o nulo si no ha respondido (CA-92)."
    )
    selected: bool = Field(description="Si el usuario lo ha seleccionado como juego objetivo.")
    target: bool = Field(
        description="Si es juego objetivo: seleccionado, sin ningún motivo en `obstacles` y no "
        "registrado en el *Hall of Fame* (RF-05, CA-93)."
    )
    completed: bool = Field(
        description="Si ya está registrado en el *Hall of Fame* (CA-68): seleccionado o no, no "
        "es juego objetivo mientras lo esté."
    )
    obstacles: list[ReasonOut] = Field(
        description="Por qué no se puede seleccionar, en el orden en que se comprueba (RF-25): "
        "`cannot_receive_bred`, `missing_data` (el detalle, en `missing`), "
        "`playability_unknown` (hay que preguntar al usuario) y `not_playable`. Vacío si se "
        "puede."
    )
    missing: list[ReasonOut] = Field(
        description="Lo que le falta para estar completo (RF-05): `generation_not_loaded`, "
        "`pokemon`, `mechanics`, `key_battles` o `starters`. Vacío si está completo."
    )
    cover_url: str | None = Field(
        description="URL de su portada en esta API; nula si el juego no está cargado o no tiene "
        "portada (RF-18)."
    )


class GameChoiceIn(BaseModel):
    selected: bool | None = Field(
        default=None,
        description="Seleccionarlo como juego objetivo (`true`) o quitarlo (`false`); si falta, "
        "no cambia.",
    )
    playable: bool | None = Field(
        default=None,
        description="Respuesta del usuario: si puede jugarlo en un sistema actual de Nintendo; "
        "si falta, no cambia (CA-92).",
    )

    @model_validator(mode="after")
    def _something(self) -> "GameChoiceIn":
        if self.selected is None and self.playable is None:
            raise ValueError("indica selected, playable o los dos")
        return self
