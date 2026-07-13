import os

from alembic import context
from sqlalchemy import create_engine

# Single source of connection truth: the DATABASE_URL environment variable
# (twelve-factor, DESIGN.md Section 11). The default targets the local
# compose stack from the host. The canonical form is plain postgresql://
# (what psycopg consumes); SQLAlchemy needs the +psycopg driver marker.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://scriptorium:scriptorium-dev@localhost:5432/scriptorium",
).replace("postgresql://", "postgresql+psycopg://", 1)

config = context.config


def run_migrations_offline() -> None:
    context.configure(url=DATABASE_URL, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
