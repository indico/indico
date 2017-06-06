# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
import sys
from functools import partial

import alembic.command
import click
from flask import current_app
from flask.cli import with_appcontext
from flask_migrate.cli import db as flask_migrate_cli

from indico.cli.core import cli_group
from indico.core.db import db
from indico.core.db.sqlalchemy.migration import PluginScriptDirectory, migrate, prepare_db
from indico.core.plugins import plugin_engine
from indico.util.console import cformat


@cli_group()
@click.option('--plugin', metavar='PLUGIN', help='Execute the command for the given plugin')
@click.option('--all-plugins', is_flag=True, help='Execute the command for all plugins')
@click.pass_context
@with_appcontext
def cli(ctx, plugin=None, all_plugins=False):
    if plugin and all_plugins:
        raise click.BadParameter('cannot combine --plugin and --all-plugins')
    if all_plugins and ctx.invoked_subcommand in ('migrate', 'revision', 'downgrade', 'stamp', 'edit'):
        raise click.UsageError('this command requires an explicit plugin')
    if (all_plugins or plugin) and ctx.invoked_subcommand == 'prepare':
        raise click.UsageError('this command is not available for plugins (use `upgrade` instead)')
    if plugin and not plugin_engine.get_plugin(plugin):
        raise click.BadParameter('plugin does not exist or is not loaded', param_hint='plugin')
    migrate.init_app(current_app, db, os.path.join(current_app.root_path, 'migrations'))


@cli.command()
@click.option('--empty', is_flag=True, help='Do not create the root category or system user. Use this only if you '
                                            'intend to import data from ZODB.')
def prepare(empty):
    """Initializes an empty database (creates tables, sets alembic rev to HEAD)"""
    return prepare_db(empty=empty)


def _safe_downgrade(*args, **kwargs):
    func = kwargs.pop('_func')
    print cformat('%{yellow!}*** DANGER')
    print cformat('%{yellow!}***%{reset} '
                  '%{red!}This operation may %{yellow!}PERMANENTLY ERASE %{red!}some data!%{reset}')
    if current_app.debug:
        skip_confirm = os.environ.get('INDICO_ALWAYS_DOWNGRADE', '').lower() in ('1', 'yes')
        print cformat('%{yellow!}***%{reset} '
                      "%{green!}Debug mode is active, so you probably won't destroy valuable data")
    else:
        skip_confirm = False
        print cformat('%{yellow!}***%{reset} '
                      "%{red!}Debug mode is NOT ACTIVE, so make sure you are on the right machine!")
    if not skip_confirm and raw_input(cformat('%{yellow!}***%{reset} '
                                              'To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
        print cformat('%{green}Aborted%{reset}')
        sys.exit(1)
    else:
        return func(*args, **kwargs)


def _call_with_plugins(*args, **kwargs):
    func = kwargs.pop('_func')
    ctx = click.get_current_context()
    all_plugins = ctx.parent.params['all_plugins']
    plugin = ctx.parent.params['plugin']
    if plugin:
        plugins = {plugin_engine.get_plugin(plugin)}
    elif all_plugins:
        plugins = set(plugin_engine.get_active_plugins().viewvalues())
    else:
        plugins = None

    if plugins is None:
        func(*args, **kwargs)
    else:
        PluginScriptDirectory.dir = os.path.join(current_app.root_path, 'core', 'plugins', 'alembic')
        alembic.command.ScriptDirectory = PluginScriptDirectory
        for plugin in plugins:
            if not os.path.exists(plugin.alembic_versions_path):
                print cformat("%{cyan}skipping plugin '{}' (no migrations folder)").format(plugin.name)
                continue
            print cformat("%{cyan!}executing command for plugin '{}'").format(plugin.name)
            with plugin.plugin_context():
                func(*args, **kwargs)


def _setup_cli():
    for command in flask_migrate_cli.commands.itervalues():
        if command.name == 'init':
            continue
        command.callback = partial(with_appcontext(_call_with_plugins), _func=command.callback)
        if command.name == 'downgrade':
            command.callback = partial(with_appcontext(_safe_downgrade), _func=command.callback)
        cli.add_command(command)

_setup_cli()
del _setup_cli
