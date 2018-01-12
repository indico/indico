# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os

import alembic.command
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
        super(PluginScriptDirectory, self).__init__(*args, **kwargs)
        self.dir = PluginScriptDirectory.dir
        # use __dict__ since it's a memoized property
        self.__dict__['_version_locations'] = [current_plugin.alembic_versions_path]

    @classmethod
    def from_config(cls, config):
        instance = super(PluginScriptDirectory, cls).from_config(config)
        instance.dir = PluginScriptDirectory.dir
        instance.__dict__['_version_locations'] = [current_plugin.alembic_versions_path]
        return instance


def _require_extensions(*names):
    missing = sorted(name for name in names if not has_extension(db.engine, name))
    if not missing:
        return True
    print cformat('%{red}Required Postgres extensions missing: {}').format(', '.join(missing))
    print cformat('%{yellow}Create them using these SQL commands (as a Postgres superuser):')
    for name in missing:
        print cformat('%{white!}  CREATE EXTENSION {};').format(name)
    return False


def _require_pg_version(version):
    # convert version string such as '9.4.10' to `90410` which is the
    # format used by server_version_num
    req_version = sum(segment * 10**(4 - 2*i) for i, segment in enumerate(map(int, version.split('.'))))
    cur_version = db.engine.execute("SELECT current_setting('server_version_num')::int").scalar()
    if cur_version >= req_version:
        return True
    print cformat('%{red}Postgres version too old; you need at least {} (or newer)').format(version)
    return False


def _require_encoding(encoding):
    cur_encoding = db.engine.execute("SELECT current_setting('server_encoding')").scalar()
    if cur_encoding >= encoding:
        return True
    print cformat('%{red}Database encoding must be {}; got {}').format(encoding, cur_encoding)
    print cformat('%{yellow}Recreate your database using `createdb -E {} -T template0 ...`').format(encoding)
    return False


def prepare_db(empty=False, root_path=None, verbose=True):
    """Initialize an empty database (create tables, set alembic rev to HEAD)."""
    if not _require_pg_version('9.6'):
        return
    if not _require_encoding('UTF8'):
        return
    if not _require_extensions('unaccent', 'pg_trgm'):
        return
    root_path = root_path or current_app.root_path
    tables = get_all_tables(db)
    if 'alembic_version' not in tables['public']:
        if verbose:
            print cformat('%{green}Setting the alembic version to HEAD')
        stamp(directory=os.path.join(root_path, 'migrations'), revision='heads')
        PluginScriptDirectory.dir = os.path.join(root_path, 'core', 'plugins', 'alembic')
        alembic.command.ScriptDirectory = PluginScriptDirectory
        plugin_msg = cformat("%{cyan}Setting the alembic version of the %{cyan!}{}%{reset}%{cyan} "
                             "plugin to HEAD%{reset}")
        for plugin in plugin_engine.get_active_plugins().itervalues():
            if not os.path.exists(plugin.alembic_versions_path):
                continue
            if verbose:
                print plugin_msg.format(plugin.name)
            with plugin.plugin_context():
                stamp(revision='heads')
        # Retrieve the table list again, just in case we created unexpected tables
        tables = get_all_tables(db)

    tables['public'] = [t for t in tables['public'] if not t.startswith('alembic_version')]
    if any(tables.viewvalues()):
        if verbose:
            print cformat('%{red}Your database is not empty!')
            print cformat('%{yellow}If you just added a new table/model, create an alembic revision instead!')
            print
            print 'Tables in your database:'
            for schema, schema_tables in sorted(tables.items()):
                for t in schema_tables:
                    print cformat('  * %{cyan}{}%{reset}.%{cyan!}{}%{reset}').format(schema, t)
        return
    create_all_tables(db, verbose=verbose, add_initial_data=(not empty))
