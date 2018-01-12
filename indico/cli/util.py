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

import traceback
from importlib import import_module

import click
from flask.cli import AppGroup, FlaskGroup, ScriptInfo
from flask_pluginengine import wrap_in_plugin_context
from werkzeug.utils import cached_property


# XXX: Do not import any indico modules in here!
# See the comment in indico.cli.core for details.
# If there is ever the need to add more utils to be used in commands,
# consider renaming this file to `coreutil.py` and adding a new
# `util.py` for whatever you are going to add.


def _create_app(info):
    from indico.web.flask.app import make_app
    return make_app(set_path=True)


class IndicoFlaskGroup(FlaskGroup):
    """
    A flask-enhanced click Group that includes commands provided
    by Indico plugins.
    """

    def __init__(self, **extra):
        super(IndicoFlaskGroup, self).__init__(create_app=_create_app, add_default_commands=False,
                                               add_version_option=False, **extra)
        self._indico_plugin_commands = None

    def _load_plugin_commands(self):
        # We don't care about `flask.commands` but indico plugin commands instead
        # This actually shouldn't be called sinde we override all the methods
        # calling it...
        assert False

    def _wrap_in_plugin_context(self, plugin, cmd):
        cmd.callback = wrap_in_plugin_context(plugin, cmd.callback)
        for subcmd in getattr(cmd, 'commands', {}).viewvalues():
            self._wrap_in_plugin_context(plugin, subcmd)

    def _get_indico_plugin_commands(self, ctx):
        if self._indico_plugin_commands is not None:
            return self._indico_plugin_commands
        try:
            from indico.core import signals
            from indico.util.signals import named_objects_from_signal
            ctx.ensure_object(ScriptInfo).load_app()
            cmds = named_objects_from_signal(signals.plugin.cli.send(), plugin_attr='_indico_plugin')
            rv = {}
            for name, cmd in cmds.viewitems():
                if cmd._indico_plugin:
                    self._wrap_in_plugin_context(cmd._indico_plugin, cmd)
                rv[name] = cmd
        except Exception as exc:
            if 'No indico config found' not in unicode(exc):
                click.echo(click.style('Loading plugin commands failed:', fg='red', bold=True))
                click.echo(click.style(traceback.format_exc(), fg='red'))
            rv = {}
        self._indico_plugin_commands = rv
        return rv

    def get_command(self, ctx, name):
        rv = AppGroup.get_command(self, ctx, name)
        if rv is not None:
            return rv
        return self._get_indico_plugin_commands(ctx).get(name)

    def list_commands(self, ctx):
        rv = set(click.Group.list_commands(self, ctx))
        rv.update(self._get_indico_plugin_commands(ctx))
        return sorted(rv)


class LazyGroup(click.Group):
    """
    A click Group that imports the actual implementation only when
    needed.  This allows for more resilient CLIs where the top-level
    command does not fail when a subcommand is broken enough to fail
    at import time.
    """

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

    def invoke(self, ctx):
        return self._impl.invoke(ctx)

    def get_usage(self, ctx):
        return self._impl.get_usage(ctx)

    def get_params(self, ctx):
        return self._impl.get_params(ctx)
