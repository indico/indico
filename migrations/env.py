import logging.config

from alembic import context
from flask import current_app
from sqlalchemy import engine_from_config, pool

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import update_session_options
from indico.core.db.sqlalchemy.util.models import import_all_models


# Ensure all our models are imported
import_all_models()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
logging.config.fileConfig(config.config_file_name)

config.set_main_option('sqlalchemy.url', current_app.config.get('SQLALCHEMY_DATABASE_URI'))
target_metadata = current_app.extensions['migrate'].db.metadata

# Get rid of the ZODB transaction manager
update_session_options(db)


def _include_symbol(tablename, schema):
    # We ignore plugin tables in migrations
    if schema and schema.startswith('plugin_'):
        return False
    return not tablename.startswith('alembic_version_')


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(url=url, include_schemas=True, version_table_schema='public', include_symbol=_include_symbol)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = engine_from_config(config.get_section(config.config_ini_section),
                                prefix='sqlalchemy.',
                                poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(connection=connection, target_metadata=target_metadata, include_schemas=True,
                      version_table_schema='public', include_symbol=_include_symbol)

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
