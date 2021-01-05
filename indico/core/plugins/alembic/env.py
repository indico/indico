# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import logging.config

from alembic import context
from flask import current_app
from flask_pluginengine import current_plugin
from sqlalchemy import engine_from_config, pool

from indico.core.db.sqlalchemy.util.models import import_all_models


if not current_plugin:
    raise Exception('Cannot run plugin db migration outside plugin context')


# Ensure all our models are imported - XXX is this necessary? if we call configure_db it's not!
import_all_models()
import_all_models(current_plugin.package_name)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
logging.config.fileConfig(config.config_file_name)

config.set_main_option('sqlalchemy.url', current_app.config.get('SQLALCHEMY_DATABASE_URI'))
target_metadata = current_app.extensions['migrate'].db.metadata

plugin_schema = 'plugin_{}'.format(current_plugin.name)
version_table = 'alembic_version_plugin_{}'.format(current_plugin.name)


def _include_symbol(tablename, schema):
    # We only include tables in this plugin's schema in migrations
    return schema == plugin_schema


def _render_item(type_, obj, autogen_context):
    if hasattr(obj, 'info') and obj.info.get('alembic_dont_render'):
        return None
    func = getattr(obj, 'alembic_render_' + type_, None)
    if func is None:
        return False
    return func(autogen_context, autogen_context.opts['template_args']['toplevel_code'])


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
    context.configure(url=url, target_metadata=target_metadata, include_schemas=True,
                      include_symbol=_include_symbol, render_item=_render_item, version_table=version_table,
                      version_table_schema='public', template_args={'toplevel_code': set()})

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
                      include_symbol=_include_symbol, render_item=_render_item, version_table=version_table,
                      version_table_schema='public', template_args={'toplevel_code': set()})

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
