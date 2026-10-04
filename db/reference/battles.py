"""Key battles of each game and their opposing Pokémon (RN-17)."""

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from db.reference.base import BattleCategory, Origin, ReferenceModel, enum_column


class KeyBattle(ReferenceModel, table=True):
    """A key battle: gym leader or equivalent, Elite Four, champion, villain boss or rival.

    The list of battles is curated; the teams come from WikiDex. A battle with a single
    team is ``automatic``; one whose team depends on the player's choice (variants) is
    ``inferred`` and the user confirms it (RN-18). ``source_page`` and ``source_revision``
    say which WikiDex page and revision the team comes from, for traceability and for the
    attribution its CC BY-NC-SA licence requires.
    """

    __tablename__ = "key_battle"
    __table_args__ = (UniqueConstraint("game", "order"),)

    slug: str = Field(primary_key=True)
    game: str = Field(foreign_key="game.slug", index=True)
    category: BattleCategory = Field(sa_type=enum_column(BattleCategory))
    trainer_name: str
    order: int
    origin: Origin = Field(sa_type=enum_column(Origin))
    fact_key: str = Field(unique=True)
    source_page: str | None = None
    source_revision: int | None = None


class KeyBattlePokemon(ReferenceModel, table=True):
    """A Pokémon of a key battle. The rival's starter is already left out (CA-26).

    ``variant`` numbers the possible teams of a battle from 1: there are several when the
    team depends on the player's choice, like the rival's, which depends on the starter.
    ``position`` is the Pokémon's position in WikiDex's team.
    """

    __tablename__ = "key_battle_pokemon"

    battle: str = Field(primary_key=True, foreign_key="key_battle.slug")
    variant: int = Field(primary_key=True)
    position: int = Field(primary_key=True)
    pokemon: str = Field(foreign_key="pokemon.slug")
    level: int | None = None
