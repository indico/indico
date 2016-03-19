# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import os
import sys
from copy import deepcopy

import alembic.command
from alembic.script import ScriptDirectory
from flask import current_app
from flask_migrate import MigrateCommand as DatabaseManager
from flask_migrate import stamp
from flask_pluginengine import current_plugin
from flask_script import Command

from indico.core.db import db
from indico.core.db.sqlalchemy.util.management import get_all_tables
from indico.core.plugins import plugin_engine
from indico.util.console import colored, cformat


@DatabaseManager.command
def prepare():
    """Initializes an empty database (creates tables, sets alembic rev to HEAD)"""
    tables = get_all_tables(db)
    if 'alembic_version' not in tables['public']:
        print colored('Setting the alembic version to HEAD', 'green')
        stamp()
        PluginScriptDirectory.dir = os.path.join(current_app.root_path, 'core', 'plugins', 'alembic')
        alembic.command.ScriptDirectory = PluginScriptDirectory
        plugin_msg = cformat("%{cyan}Setting the alembic version of the %{cyan!}{}%{reset}%{cyan} "
                             "plugin to HEAD%{reset}")
        for plugin in plugin_engine.get_active_plugins().itervalues():
            if not os.path.exists(plugin.alembic_versions_path):
                continue
            print plugin_msg.format(plugin.name)
            with plugin.plugin_context():
                stamp()
        # Retrieve the table list again, just in case we created unexpected hables
        tables = get_all_tables(db)

    tables['public'] = [t for t in tables['public'] if not t.startswith('alembic_version')]
    if any(tables.viewvalues()):
        print colored('Your database is not empty!', 'red')
        print colored('If you just added a new table/model, create an alembic revision instead!', 'yellow')
        print
        print 'Tables in your database:'
        for schema, schema_tables in sorted(tables.items()):
            for t in schema_tables:
                print cformat('  * %{cyan}{}%{reset}.%{cyan!}{}%{reset}').format(schema, t)
        return
    print colored('Creating tables', 'green')
    db.create_all()


del DatabaseManager._commands['init']  # not useful since we already have a migration environment
run_downgrade = DatabaseManager._commands['downgrade'].run


def _safe_downgrade(*args, **kwargs):
    print cformat('%{yellow!}*** DANGER')
    print cformat('%{yellow!}***%{reset} '
                  '%{red!}This operation may %{yellow!}PERMANENTLY ERASE %{red!}some data!%{reset}')
    if current_app.debug:
        print cformat('%{yellow!}***%{reset} '
                      "%{green!}Debug mode is active, so you probably won't destroy valuable data")
    else:
        print cformat('%{yellow!}***%{reset} '
                      "%{red!}Debug mode is NOT ACTIVE, so make sure you are on the right machine!")
    if raw_input(cformat('%{yellow!}***%{reset} '
                         'To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
        print cformat('%{green}Aborted%{reset}')
        sys.exit(1)
    else:
        return run_downgrade(*args, **kwargs)


DatabaseManager._commands['downgrade'].run = _safe_downgrade


class PluginScriptDirectory(ScriptDirectory):
    """Like `ScriptDirectory` but lets you override the paths from outside.

    This is a pretty ugly hack but alembic doesn't give us a nice way to do it...
    """
    dir = None
    versions = None

    def __init__(self, *args, **kwargs):
        super(PluginScriptDirectory, self).__init__(*args, **kwargs)
        self.dir = PluginScriptDirectory.dir
        self.versions = current_plugin.alembic_versions_path

    @classmethod
    def from_config(cls, config):
        instance = super(PluginScriptDirectory, cls).from_config(config)
        instance.dir = PluginScriptDirectory.dir
        instance.versions = current_plugin.alembic_versions_path
        return instance


class PluginDBCommand(Command):
    """Like `Command`, but specific to plugin DB migrations.

    Executes its underlying function for all plugins and makes
    flask-migrate use the plugin's migrations.
    """
    @classmethod
    def from_command(cls, command, require_plugin_arg):
        """Clones an existing command.

        :param command: A Flask-Script `Command`
        """
        new_command = cls()
        new_command.run = command.run
        new_command.__doc__ = command.__doc__
        new_command.help_args = command.help_args
        new_command.option_list = tuple(command.option_list)
        new_command.require_plugin_arg = require_plugin_arg
        return new_command

    def __call__(self, app=None, *args, **kwargs):
        PluginScriptDirectory.dir = os.path.join(app.root_path, 'core', 'plugins', 'alembic')
        alembic.command.ScriptDirectory = PluginScriptDirectory

        with app.app_context():
            active_plugins = plugin_engine.get_active_plugins()
            plugins = set(kwargs.pop('plugins'))
            if plugins:
                invalid_plugins = plugins - active_plugins.viewkeys()
                if invalid_plugins:
                    print cformat('%{red!}Invalid plugin(s) specified: {}').format(', '.join(invalid_plugins))
                    sys.exit(1)
            for plugin in active_plugins.itervalues():
                if plugins and plugin.name not in plugins:
                    continue
                if not os.path.exists(plugin.alembic_versions_path):
                    print cformat("%{cyan}skipping plugin '{}' (no migrations folder)").format(plugin.name)
                    continue
                print cformat("%{cyan!}executing command for plugin '{}'").format(plugin.name)
                with plugin.plugin_context():
                    super(PluginDBCommand, self).__call__(app, *args, **kwargs)

    def create_parser(self, *args, **kwargs):
        parser = super(PluginDBCommand, self).create_parser(*args, **kwargs)
        parser.add_argument('--plugin', dest='plugins', action='append', default=[], metavar='PLUGIN',
                            required=self.require_plugin_arg,
                            help='Plugin name to work on - can be used multiple times')
        return parser


def _make_plugin_database_manager():
    """Clones DatabaseManager and adapts its commands to plugin database migrations"""
    manager = deepcopy(DatabaseManager)
    manager.description += ' for plugins'
    manager.help += ' for plugins'
    del manager._commands['prepare']  # not needed for plugins
    single_plugin_commands = {'migrate', 'revision', 'downgrade', 'stamp'}
    for name, command in manager._commands.iteritems():
        manager._commands[name] = PluginDBCommand.from_command(command, name in single_plugin_commands)
    return manager


PluginDatabaseManager = _make_plugin_database_manager()
