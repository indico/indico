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

import click
from flask.cli import AppGroup, pass_script_info

# XXX: Do not import any other indico modules here!
# If any import from this module triggers an exception the dev server
# will die while an exception only happening during app creation will
# be handled gracefully.
from indico.cli.util import IndicoFlaskGroup, LazyGroup


click.disable_unicode_literals_warning = True
__all__ = ('cli_command', 'cli_group')


# We never use the group but expose cli_command and cli_group for
# plugins to have access to the flask-enhanced command and group
# decorators that use the app context by default
_cli = AppGroup()
cli_command = _cli.command
cli_group = _cli.group
del _cli


def _get_indico_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    import indico
    message = 'Indico v{}'.format(indico.__version__)
    click.echo(message, ctx.color)
    ctx.exit()


@click.group(cls=IndicoFlaskGroup)
@click.option('--version', '-v', expose_value=False, callback=_get_indico_version, is_flag=True, is_eager=True,
              help='Show the flask version',)
def cli():
    """
    This script lets you control various aspects of Indico from the
    command line.
    """


# All core cli commands (including groups with subcommands) are
# registered in this file and imported lazily - either using a
# LazyGroup or by importing the actual logic of a command inside
# the command's function here.  This allows running the cli even
# if there's no indico config available or importing indico is
# broken for other reasons.

@cli.group(cls=LazyGroup, import_name='indico.cli.setup:cli')
def setup():
    """Setup Indico."""


@cli.group(cls=LazyGroup, import_name='indico.cli.user:cli')
def user():
    """Manage Indico users."""


@cli.group(cls=LazyGroup, import_name='indico.cli.event:cli')
def event():
    """Manage Indico events."""


@cli.group(cls=LazyGroup, import_name='indico.cli.i18n:cli')
def i18n():
    """Perform i18n-related operations."""


@cli.group(cls=LazyGroup, import_name='indico.cli.database:cli')
def db():
    """Perform database operations."""


@cli.command(context_settings={'ignore_unknown_options': True, 'allow_extra_args': True}, add_help_option=False)
@click.pass_context
def celery(ctx):
    """Manage the Celery task daemon."""
    from indico.core.celery.cli import celery_cmd
    celery_cmd(ctx.args)


@cli.command(short_help='Re-send a failed email.')
@click.argument('paths', type=click.Path(exists=True, dir_okay=False), metavar='PATH...', nargs=-1, required=True)
def resend_email(paths):
    """Re-send failed emails.

    If sending emails failed for some reason and you want to retry
    sending them, use this command and specify the path(s) to the
    `failed-email-*` file(s) mentioned in the log.

    If sending an email succeeds, the file is deleted; otherwise it
    is kept and this command terminates with the exception that caused
    the sending to fail.
    """
    from indico.core.emails import resend_failed_emails_cmd
    resend_failed_emails_cmd(paths)


@cli.command(short_help='Delete old temporary files.')
@click.option('--temp', is_flag=True, help='Delete old files in the temp dir')
@click.option('--cache', is_flag=True, help='Delete old files in the cache dir')
@click.option('--assets', is_flag=True, help='Delete old files in the assets dir.')
@click.option('--verbose', '-v', is_flag=True, help="Be verbose and show what's being deleted")
@click.option('--dry-run', '-n', is_flag=True, help="Do not delete anything (implies --verbose)")
@click.option('--min-age', type=click.IntRange(1), default=1, metavar='N',
              help='Delete files at least N days old (default: 1)')
def cleanup(temp, cache, assets, verbose, dry_run, min_age):
    from .cleanup import cleanup_cmd
    if not temp and not cache and not assets:
        raise click.UsageError('You need to specify what to delete')
    cleanup_cmd(temp, cache, assets, min_age=min_age, dry_run=dry_run, verbose=(verbose or dry_run))


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
@click.option('--reloader', 'reloader_type', type=click.Choice(['auto', 'none', 'stat', 'watchdog']), default='auto',
              help='The type of auto-reloader to use.')
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
    run_cmd(info, **kwargs)


@cli.command(short_help='Run a shell in the app context.')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose information on the available objects')
@click.option('-r', '--request-context', is_flag=True, help='Run the shell inside a Flask request context')
def shell(verbose, request_context):
    from .shell import shell_cmd
    shell_cmd(verbose, request_context)
