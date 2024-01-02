# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

import alembic.command
import click
from alembic.script import ScriptDirectory
from flask import current_app
from flask_migrate import Migrate, stamp
from flask_pluginengine import current_plugin

from indico.core.db import db
from indico.core.db.sqlalchemy.util.management import create_all_tables, get_all_tables
from indico.core.db.sqlalchemy.util.queries import has_extension
from indico.core.plugins import plugin_engine
from indico.util.console import cformat


migrate = Migrate(db=db)


class PluginScriptDirectory(ScriptDirectory):
    """Like `ScriptDirectory` but lets you override the paths from outside.

    This is a pretty ugly hack but alembic doesn't give us a nice way to do it...
    """

    dir = None
    versions = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dir = PluginScriptDirectory.dir
        # use __dict__ since it's a memoized property
        self.__dict__['_version_locations'] = [current_plugin.alembic_versions_path]

    @classmethod
    def from_config(cls, config):
        instance = super().from_config(config)
        instance.dir = PluginScriptDirectory.dir
        instance.__dict__['_version_locations'] = [current_plugin.alembic_versions_path]
        return instance


def _require_extensions(*names):
    missing = sorted(name for name in names if not has_extension(db.engine, name))
    if not missing:
        return True
    click.secho(f"Required Postgres extensions missing: {', '.join(missing)}", fg='red')
    click.secho('Create them using these SQL commands (as a Postgres superuser):', fg='yellow')
    for name in missing:
        click.secho(f'  CREATE EXTENSION {name};', bold=True)
    return False


def _require_pg_version(req_version, *, force=False):
    cur_version = db.engine.execute("SELECT current_setting('server_version_num')::int / 10000").scalar()
    if cur_version >= req_version:
        return True
    click.secho(f'Postgres version {cur_version} too old; you need at least {req_version} (or newer)', fg='red')
    if force:
        click.secho('Continuing anyway, you have been warned.', fg='yellow')
        return True
    return False


def _require_encoding(encoding):
    cur_encoding = db.engine.execute("SELECT current_setting('server_encoding')").scalar()
    if cur_encoding == encoding:
        return True
    click.secho(f'Database encoding must be {encoding}; got {cur_encoding}', fg='red')
    click.secho(f'Recreate your database using `createdb -E {encoding} -T template0 ...`', fg='yellow')
    return False


def prepare_db(empty=False, root_path=None, verbose=True, force=False):
    """Initialize an empty database (create tables, set alembic rev to HEAD)."""
    if not _require_pg_version(13, force=force):
        return False
    if not _require_encoding('UTF8'):
        return False
    if not _require_extensions('unaccent', 'pg_trgm'):
        return False
    root_path = root_path or current_app.root_path
    tables = get_all_tables(db)
    if 'alembic_version' not in tables['public']:
        if verbose:
            click.secho('Setting the alembic version to HEAD', fg='green')
        stamp(directory=os.path.join(root_path, 'migrations'), revision='heads')
        PluginScriptDirectory.dir = os.path.join(root_path, 'core', 'plugins', 'alembic')
        alembic.command.ScriptDirectory = PluginScriptDirectory
        plugin_msg = cformat('%{cyan}Setting the alembic version of the %{cyan!}{}%{reset}%{cyan} '
                             'plugin to HEAD%{reset}')
        for plugin in plugin_engine.get_active_plugins().values():
            if not os.path.exists(plugin.alembic_versions_path):
                continue
            if verbose:
                print(plugin_msg.format(plugin.name))
            with plugin.plugin_context():
                stamp(revision='heads')
        # Retrieve the table list again, just in case we created unexpected tables
        tables = get_all_tables(db)

    tables['public'] = [t for t in tables['public'] if not t.startswith('alembic_version')]
    if any(tables.values()):
        if verbose:
            click.secho('Your database is not empty!', fg='red')
            click.secho('If you just added a new table/model, create an alembic revision instead!', fg='yellow')
            print()
            print('Tables in your database:')
            for schema, schema_tables in sorted(tables.items()):
                for t in schema_tables:
                    print(cformat('  * %{cyan}{}%{reset}.%{cyan!}{}%{reset}').format(schema, t))
        return False
    create_all_tables(db, verbose=verbose, add_initial_data=(not empty))
    return True
