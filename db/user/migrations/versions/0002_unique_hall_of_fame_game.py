"""Each game is recorded once in the Hall of Fame (CA-68).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-07 21:00:00

If some game is already recorded more than once, the upgrade stops and says which, without
deleting anything: the user decides which entry to keep.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class RepeatedGamesError(RuntimeError):
    """Some games are recorded more than once: the constraint cannot be added."""


def upgrade() -> None:
    repeated = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT game FROM hall_of_fame_entry GROUP BY game HAVING COUNT(*) > 1 "
                "ORDER BY game"
            )
        )
        .scalars()
        .all()
    )
    if repeated:
        raise RepeatedGamesError(
            "Cada juego solo puede estar una vez en el Hall of Fame (CA-68), y estos están "
            f"repetidos: {', '.join(repeated)}. Elimina los registros que sobren con la versión "
            "anterior y vuelve a arrancar."
        )
    with op.batch_alter_table("hall_of_fame_entry") as batch:
        batch.create_unique_constraint(op.f("uq_hall_of_fame_entry_game"), ["game"])


def downgrade() -> None:
    with op.batch_alter_table("hall_of_fame_entry") as batch:
        batch.drop_constraint(op.f("uq_hall_of_fame_entry_game"), type_="unique")
