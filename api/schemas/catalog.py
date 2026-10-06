"""Responses of the Pokémon catalogue (RF-01, RF-02)."""

from pydantic import BaseModel, Field

from db.reference.evolution import ConditionValue


class CatalogPokemonOut(BaseModel):
    pokemon: str = Field(description="Identificador de la forma, p. ej. `vulpix-alola`.")
    name: str = Field(description="Nombre en español; el de una forma regional la identifica.")
    dex_number: int = Field(description="Número de la Pokédex Nacional.")
    types: list[str] = Field(description="Tipos actuales (de la última generación cargada).")
    region: str | None = Field(description="Región de una forma regional (`alola`, `galar`…).")
    favorite: bool = Field(description="Si está en favoritos.")
    image_url: str | None = Field(
        description="URL de su imagen en esta API (`/api/pokemon/{pokemon}/image`); nula si la "
        "forma no tiene imagen."
    )


class CatalogOut(BaseModel):
    total: int = Field(description="Pokémon que cumplen los filtros.")
    pokemon: list[CatalogPokemonOut] = Field(description="En orden de la Pokédex Nacional.")


class LineMemberOut(CatalogPokemonOut):
    stage: int = Field(description="Etapa en la línea: 1 para la primera.")


class EvolutionMethodOut(BaseModel):
    trigger: str = Field(
        description="Disparador de PokeAPI: `level-up`, `use-item`, `trade`, `shed`…"
    )
    conditions: dict[str, ConditionValue] = Field(
        description='Condiciones de PokeAPI, p. ej. `{"minimum_level": 16}` o '
        '`{"trigger_item": "thunder-stone"}`.'
    )


class EvolutionOut(BaseModel):
    from_pokemon: str
    to_pokemon: str
    version_group: str = Field(
        description="Grupo de versiones más reciente con datos de esta evolución."
    )
    methods: list[EvolutionMethodOut] = Field(
        description="Formas de evolucionar; varias si hay métodos alternativos."
    )


class PokemonDetailOut(CatalogPokemonOut):
    artwork_url: str | None = Field(
        description="URL de su ilustración oficial, más grande, para la ficha "
        "(`/api/pokemon/{pokemon}/artwork`); nula si la forma no tiene."
    )
    generation: int = Field(description="Generación en que apareció la especie.")
    species: str
    is_legendary: bool
    is_mythical: bool
    line: list[LineMemberOut] = Field(
        description="La línea evolutiva completa, con todas sus formas, por etapa y número."
    )
    evolutions: list[EvolutionOut] = Field(description="Cada evolución de la línea y su mecanismo.")
