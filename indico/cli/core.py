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
from flask.cli import FlaskGroup, pass_script_info
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

    def invoke(self, ctx):
        return self._impl.invoke(ctx)


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


@cli.group(cls=LazyGroup, import_name='indico.cli.i18n:cli')
def i18n():
    """Perform i18n-related operations."""


@cli.command(context_settings={'ignore_unknown_options': True, 'allow_extra_args': True}, add_help_option=False)
@click.pass_context
def celery(ctx):
    """Manage the Celery task daemon."""
    from indico.core.celery.cli import celery_cmd
    celery_cmd(ctx.args)


@cli.command(with_appcontext=False)
@click.option('--host', '-h', default='127.0.0.1', metavar='HOST', help='The ip/host to bind to.')
@click.option('--port', '-p', default=None, type=int, metavar='PORT', help='The port to bind to.')
@click.option('--url', '-u', default=None, metavar='URL',
              help='The URL used to access indico. Defaults to `http(s)://host:port`')
@click.option('--ssl', '-s', is_flag=True, help='Use SSL.')
@click.option('--ssl-key', '-K', type=click.Path(exists=True, dir_okay=False), help='The SSL private key to use.')
@click.option('--ssl-cert', '-C', type=click.Path(exists=True, dir_okay=False), help='The SSL cert key to use.')
@click.option('--quiet', '-q', is_flag=True, help='Disable logging of requests for most static files.')
@click.option('--enable-evalex', is_flag=True,
              help="Enable the werkzeug debugger's python shell in tracebacks and via /console")
@click.option('--evalex-from', multiple=True,
              help='Restrict the debugger shell to the given ips (can be used multiple times)')
@click.option('--proxy', is_flag=True, help='Use the ip and protocol provided by the proxy.')
@pass_script_info
def run(info, **kwargs):
    """Run the development webserver.

    If no port is set, 8000 or 8443 will be used (depending on whether
    SSL is enabled or not).

    Enabling SSL without specifying key and certificate will use a
    self-signed one.

    Specifying a custom URL allows you to run the dev server e.g. behind
    nginx to access it on the standard ports and serve static files
    much faster. Note that you MUST use `--proxy` when running behind
    another server; otherwise all requests will be considered to
    originate from that server's IP which is especially dangerous
    when using the evalex whitelist with `127.0.0.1` in it.

    Note that even behind nginx the dev server is NOT SUITABLE for a
    production setup.
    """
    from indico.cli.devserver import run_cmd
    if bool(kwargs['ssl_key']) != bool(kwargs['ssl_cert']):
        raise click.BadParameter('ssl-key and ssl-cert must be used together')
    if kwargs['url']:
        proto = 'https://' if kwargs['ssl'] else 'http://'
        if not kwargs['url'].startswith(proto):
            raise click.BadParameter('must start with {}'.format(proto), param_hint='url')
    run_cmd(info, **kwargs)


@cli.command(short_help='Run a shell in the app context.')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose information on the available objects')
def shell(verbose):
    from .shell import shell_cmd
    shell_cmd(verbose)
