"""Types, type chart, species and forms, resolved per generation (RN-05, RN-10, RN-11)."""

from sqlalchemy import CheckConstraint
from sqlmodel import Field

from db.reference.base import ReferenceModel


class Type(ReferenceModel, table=True):
    """A Pokémon type and the generation in which it appeared (Steel and Dark in the 2nd)."""

    __tablename__ = "type"

    slug: str = Field(primary_key=True)
    name_es: str
    generation: int = Field(foreign_key="generation.number")


class TypeEfficacy(ReferenceModel, table=True):
    """Damage factor of an attacking type against a defending type in a generation.

    Already resolved with PokeAPI's past efficacies. ``factor`` is in hundredths: 0, 50, 100
    or 200.
    """

    __tablename__ = "type_efficacy"
    __table_args__ = (CheckConstraint("factor IN (0, 50, 100, 200)", name="factor_values"),)

    generation: int = Field(primary_key=True, foreign_key="generation.number")
    attacking: str = Field(primary_key=True, foreign_key="type.slug")
    defending: str = Field(primary_key=True, foreign_key="type.slug")
    factor: int


class Species(ReferenceModel, table=True):
    """A species of the National Pokédex.

    ``requires_incense`` marks baby species that only hatch when a parent holds an incense,
    such as Azurill; for them the egg stage is the next one (CA-36).
    """

    __tablename__ = "species"

    slug: str = Field(primary_key=True)
    dex_number: int = Field(unique=True)
    name_es: str
    generation: int = Field(foreign_key="generation.number")
    evolves_from: str | None = Field(default=None, foreign_key="species.slug")
    evolution_chain: int = Field(index=True)
    is_baby: bool
    requires_incense: bool = False
    is_legendary: bool
    is_mythical: bool


class SpeciesEggGroup(ReferenceModel, table=True):
    """Egg group of a species, used to decide whether its line can be bred (RN-11)."""

    __tablename__ = "species_egg_group"

    species: str = Field(primary_key=True, foreign_key="species.slug")
    egg_group: str = Field(primary_key=True)


class Pokemon(ReferenceModel, table=True):
    """A form with its own data: the default form or a regional one (RN-05).

    Mega evolutions, Gigamax and battle-only forms are not loaded. ``region`` is set only for
    regional forms (``alola``, ``galar``…).
    """

    __tablename__ = "pokemon"

    slug: str = Field(primary_key=True)
    species: str = Field(foreign_key="species.slug", index=True)
    name_es: str
    is_default: bool
    region: str | None = None


class PokemonType(ReferenceModel, table=True):
    """Type of a form in a generation; slot 1 is the primary type (RN-10, RN-13)."""

    __tablename__ = "pokemon_type"
    __table_args__ = (CheckConstraint("slot IN (1, 2)", name="slot_values"),)

    pokemon: str = Field(primary_key=True, foreign_key="pokemon.slug")
    generation: int = Field(primary_key=True, foreign_key="generation.number")
    slot: int = Field(primary_key=True)
    type: str = Field(foreign_key="type.slug")
