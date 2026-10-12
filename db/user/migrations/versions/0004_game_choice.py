"""The user's choices in the game catalogue: selected games and whether they are playable (RF-25).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-12 20:00:00

Starts empty: after the update no game is selected, and the user chooses them (CA-93).
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "game_choice",
        sa.Column("game", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("playable", sa.Boolean(), nullable=True),
        sa.Column("updated_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("game", name=op.f("pk_game_choice")),
    )


def downgrade() -> None:
    op.drop_table("game_choice")
