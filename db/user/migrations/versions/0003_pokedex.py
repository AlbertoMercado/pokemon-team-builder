"""The Pokédex of each completed game: its initial list and the user's marks (RF-20 to RF-24).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-10 20:00:00

Both tables hang from the Hall of Fame entry: removing it removes its Pokédex (CA-68).
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pokedex",
        sa.Column("entry", sa.Integer(), nullable=False),
        sa.Column("started_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["entry"],
            ["hall_of_fame_entry.id"],
            name=op.f("fk_pokedex_entry_hall_of_fame_entry"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("entry", name=op.f("pk_pokedex")),
    )
    op.create_table(
        "pokedex_entry",
        sa.Column("pokedex", sa.Integer(), nullable=False),
        sa.Column("species", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("registered", "impossible", name="dexstatus", native_enum=False, length=10),
            nullable=True,
        ),
        sa.Column("chosen_method", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.CheckConstraint(
            "status IS NULL OR status IN ('registered', 'impossible')",
            name=op.f("ck_pokedex_entry_status"),
        ),
        sa.CheckConstraint(
            "status IS NOT NULL OR chosen_method IS NOT NULL",
            name=op.f("ck_pokedex_entry_not_empty"),
        ),
        sa.ForeignKeyConstraint(
            ["pokedex"],
            ["pokedex.entry"],
            name=op.f("fk_pokedex_entry_pokedex_pokedex"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("pokedex", "species", name=op.f("pk_pokedex_entry")),
    )


def downgrade() -> None:
    op.drop_table("pokedex_entry")
    op.drop_table("pokedex")
