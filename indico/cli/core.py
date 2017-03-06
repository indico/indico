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

from importlib import import_module

import click
from flask.cli import FlaskGroup, with_appcontext
from werkzeug.utils import cached_property

click.disable_unicode_literals_warning = True


def _create_app(info):
    # XXX: Keep this import local - importing this file should not
    # import any other indico code as having the import of this file
    # fail would break the reloader.
    from indico.web.flask.app import make_app
    return make_app(set_path=True)


class LazyGroup(click.Group):
    def __init__(self, import_name, **kwargs):
        self._import_name = import_name
        super(LazyGroup, self).__init__(**kwargs)

    @cached_property
    def _impl(self):
        module, name = self._import_name.split(':', 1)
        return getattr(import_module(module), name)

    def get_command(self, ctx, cmd_name):
        return self._impl.get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        return self._impl.list_commands(ctx)


@click.group(cls=FlaskGroup, create_app=_create_app, add_default_commands=False)
def cli(**kwargs):
    """
    This script lets you control various aspects of Indico from the
    command line.
    """


@cli.group(cls=LazyGroup, import_name='indico.cli.setup:cli')
def setup():
    """Setup Indico."""


@cli.group(cls=LazyGroup, import_name='indico.cli.admin:cli')
def admin():
    """Manage Indico users."""


@cli.command(short_help='Runs a shell in the app context.')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose information on the available objects')
@with_appcontext
def shell(verbose):
    from .shell import shell_cmd
    shell_cmd(verbose)
