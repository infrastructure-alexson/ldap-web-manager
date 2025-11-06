"""
Alembic environment configuration
Handles database migrations for LDAP Web Manager
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add backend directory to path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_config
from app.db.base import Base
from app.db.models import *  # noqa: Import all models for Alembic to detect them

# this is the Alembic Config object, which provides
# the values of the [alembic] section of the .ini file as well as other
# options containing the values from the env variable
config_obj = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config_obj.config_file_name is not None:
    fileConfig(config_obj.config_file_name)

# Get database URL from app config
app_config = get_config()
if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = app_config.database_url

# Set sqlalchemy.url for Alembic
config_obj.set_main_option('sqlalchemy.url', os.environ['DATABASE_URL'])

# set the target for 'autogenerate' support
# this will be the Base object for models defined for the application
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config_obj.get_section(config_obj.config_ini_section)["sqlalchemy.url"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config_obj.get_section(config_obj.config_ini_section)
    configuration["sqlalchemy.url"] = os.environ.get('DATABASE_URL')
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

