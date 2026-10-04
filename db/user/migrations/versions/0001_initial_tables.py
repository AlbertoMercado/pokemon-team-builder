"""Initial tables of user.sqlite: favourites, rule settings, Hall of Fame and confirmations.

Revision ID: 0001
Revises:
Create Date: 2026-10-04 19:37:26.062097
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fact_confirmation",
        sa.Column("fact_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("game", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("confirmed_value", sa.JSON(), nullable=False),
        sa.Column("proposed_value_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("confirmed_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("fact_key", name=op.f("pk_fact_confirmation")),
    )
    op.create_table(
        "favorite",
        sa.Column("pokemon", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("added_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("pokemon", name=op.f("pk_favorite")),
    )
    op.create_table(
        "hall_of_fame_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("completed_on", sa.Date(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hall_of_fame_entry")),
        sa.UniqueConstraint("sequence", name=op.f("uq_hall_of_fame_entry_sequence")),
    )
    op.create_table(
        "rule_setting",
        sa.Column("rule_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "weight IS NULL OR weight BETWEEN 0 AND 10", name=op.f("ck_rule_setting_weight")
        ),
        sa.PrimaryKeyConstraint("rule_id", name=op.f("pk_rule_setting")),
    )
    op.create_table(
        "hall_of_fame_member",
        sa.Column("entry", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("pokemon", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("types", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "position BETWEEN 1 AND 6", name=op.f("ck_hall_of_fame_member_position")
        ),
        sa.ForeignKeyConstraint(
            ["entry"],
            ["hall_of_fame_entry.id"],
            name=op.f("fk_hall_of_fame_member_entry_hall_of_fame_entry"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("entry", "position", name=op.f("pk_hall_of_fame_member")),
    )


def downgrade() -> None:
    op.drop_table("hall_of_fame_member")
    op.drop_table("rule_setting")
    op.drop_table("hall_of_fame_entry")
    op.drop_table("favorite")
    op.drop_table("fact_confirmation")
