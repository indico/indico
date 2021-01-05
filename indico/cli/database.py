# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import print_function, unicode_literals

import os
import sys
from functools import partial

import alembic.command
import click
from flask import current_app
from flask.cli import with_appcontext
from flask_migrate.cli import db as flask_migrate_cli

import indico
from indico.cli.core import cli_group
from indico.core.db import db
from indico.core.db.sqlalchemy.migration import PluginScriptDirectory, migrate, prepare_db
from indico.core.db.sqlalchemy.util.management import get_all_tables
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
def prepare():
    """Initialize a new database (creates tables, sets alembic rev to HEAD)."""
    return prepare_db()


def _stamp(plugin=None, revision=None):
    table = 'alembic_version' if not plugin else 'alembic_version_plugin_{}'.format(plugin)
    db.session.execute('DELETE FROM {}'.format(table))
    if revision:
        db.session.execute('INSERT INTO {} VALUES (:revision)'.format(table), {'revision': revision})


@cli.command()
def reset_alembic():
    """Reset the alembic state carried over from 1.9.x.

    Only run this command right after upgrading from a 1.9.x version
    so the references to old alembic revisions (which were removed in
    2.0) are reset.
    """
    tables = get_all_tables(db)['public']
    if 'alembic_version' not in tables:
        print('No alembic_version table found')
        sys.exit(1)
    current_revs = [rev for rev, in db.session.execute('SELECT version_num FROM alembic_version').fetchall()]
    if current_revs != ['65c079b091bf']:
        print('Your database is not at the latest 1.9.11 revision (got [{}], expected [65c079b091bf]).'
              .format(', '.join(current_revs)))
        print('This can have multiple reasons:')
        print('1) You did not upgrade from 1.9.x, so you do not need this command')
        print('2) You have already executed the script')
        print('3) You did not fully upgrade to the latest 1.9.11 revision before upgrading to 2.x')
        print('In case of (3), you need to install v1.9.11 and then upgrade the database before updating Indico back '
              'to {}'.format(indico.__version__))
        sys.exit(1)
    plugins = sorted(x[23:] for x in tables if x.startswith('alembic_version_plugin_'))
    print('Resetting core alembic state...')
    _stamp()
    print('Plugins found: {}'.format(', '.join(plugins)))
    no_revision_plugins = {'audiovisual', 'payment_cern'}
    for plugin in no_revision_plugins:
        # All revisions were just data migrations -> get rid of them
        if plugin not in plugins:
            continue
        print('[{}] Deleting revision table'.format(plugin))
        db.session.execute('DROP TABLE alembic_version_plugin_{}'.format(plugin))
    plugin_revisions = {'chat': '3888761f35f7',
                        'livesync': 'aa0dbc6c14aa',
                        'outlook': '6093a83228a7',
                        'vc_vidyo': '6019621fea50'}
    for plugin, revision in plugin_revisions.iteritems():
        if plugin not in plugins:
            continue
        print('[{}] Stamping to new revision'.format(plugin))
        _stamp(plugin, revision)
    db.session.commit()


def _safe_downgrade(*args, **kwargs):
    func = kwargs.pop('_func')
    print(cformat('%{yellow!}*** DANGER'))
    print(cformat('%{yellow!}***%{reset} '
                  '%{red!}This operation may %{yellow!}PERMANENTLY ERASE %{red!}some data!%{reset}'))
    if current_app.debug:
        skip_confirm = os.environ.get('INDICO_ALWAYS_DOWNGRADE', '').lower() in ('1', 'yes')
        print(cformat('%{yellow!}***%{reset} '
                      "%{green!}Debug mode is active, so you probably won't destroy valuable data"))
    else:
        skip_confirm = False
        print(cformat('%{yellow!}***%{reset} '
                      "%{red!}Debug mode is NOT ACTIVE, so make sure you are on the right machine!"))
    if not skip_confirm and raw_input(cformat('%{yellow!}***%{reset} '
                                              'To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
        print(cformat('%{green}Aborted%{reset}'))
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
                print(cformat("%{cyan}skipping plugin '{}' (no migrations folder)").format(plugin.name))
                continue
            print(cformat("%{cyan!}executing command for plugin '{}'").format(plugin.name))
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
