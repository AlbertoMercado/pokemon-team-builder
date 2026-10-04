"""Alembic environment of user.sqlite.

The connection comes from ``db.user.upgrade`` (``config.attributes["connection"]``) when the
API starts, or from the ``sqlalchemy.url`` of ``db/user/alembic.ini`` when a developer runs
Alembic by hand (docs/05-operacion/api.md). SQLite cannot alter most constraints in place, so
migrations run in batch mode.
"""

from alembic import context
from sqlalchemy import Connection, engine_from_config, pool

from db.user.models import UserModel

config = context.config
target_metadata = UserModel.metadata


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if isinstance(connection, Connection):
        _run(connection)
        return
    engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with engine.connect() as connection:
        _run(connection)


run_migrations_online()
