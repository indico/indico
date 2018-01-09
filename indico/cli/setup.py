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
import re
import shutil
import socket
import sys
from operator import attrgetter
from smtplib import SMTP

import click
from click import wrap_text
from flask.helpers import get_root_path
from pkg_resources import iter_entry_points
from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import PathCompleter, WordCompleter
from prompt_toolkit.layout.lexers import SimpleLexer
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from pytz import all_timezones, common_timezones
from redis import RedisError, StrictRedis
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool
from terminaltables import AsciiTable
from werkzeug.urls import url_parse

from indico.util.console import cformat
from indico.util.string import is_valid_mail


click.disable_unicode_literals_warning = True


def _echo(msg=''):
    click.echo(msg, err=True)


def _warn(msg):
    msg = wrap_text(msg)
    click.echo(click.style(msg, fg='yellow'), err=True)


def _error(msg):
    msg = wrap_text(msg)
    click.echo(click.style(msg, fg='red', bold=True), err=True)


def _prompt_abort():
    _confirm('Continue anyway?', abort=True)


def _copy(src, dst, force=False):
    if not force and os.path.exists(dst):
        _echo(cformat('%{yellow!}{}%{reset}%{yellow} already exists; not copying %{yellow!}{}')
              .format(dst, src))
        return
    _echo(cformat('%{green}Copying %{green!}{}%{reset}%{green} -> %{green!}{}').format(src, dst))
    shutil.copy(src, dst)


def _link(src, dst):
    _echo(cformat('%{cyan}Linking %{cyan!}{}%{reset}%{cyan} -> %{cyan!}{}').format(dst, src))
    if os.path.exists(dst) or os.path.islink(dst):
        os.unlink(dst)
    os.symlink(src, dst)


def _get_dirs(target_dir):
    if not os.path.isdir(target_dir):
        _echo(cformat('%{red}Directory not found:%{red!} {}').format(target_dir))
        sys.exit(1)
    return get_root_path('indico'), os.path.abspath(target_dir)


PROMPT_TOOLKIT_STYLE = style_from_dict({
    Token.HELP: '#aaaaaa',
    Token.PROMPT: '#5f87ff',
    Token.DEFAULT: '#dfafff',
    Token.BRACKET: '#ffffff',
    Token.COLON: '#ffffff',
    Token.INPUT: '#aaffaa',
})


def _prompt(message, default='', path=False, list_=None, required=True, validate=None, allow_invalid=False,
            password=False, help=None):
    def _get_prompt_tokens(cli):
        rv = [
            (Token.PROMPT, message),
            (Token.COLON, ': '),
        ]
        if first and help:
            rv.insert(0, (Token.HELP, wrap_text(help) + '\n'))
        return rv

    completer = None
    if path:
        completer = PathCompleter(only_directories=True, expanduser=True)
    elif list_:
        completer = WordCompleter(sorted(list_), ignore_case=True, sentence=True,
                                  meta_dict=(list_ if isinstance(list_, dict) else None))
        if validate is None:
            validate = list_.__contains__

    first = True
    while True:
        try:
            rv = prompt(get_prompt_tokens=_get_prompt_tokens, default=default, is_password=password,
                        completer=completer, lexer=SimpleLexer(Token.INPUT), style=PROMPT_TOOLKIT_STYLE)
        except (EOFError, KeyboardInterrupt):
            sys.exit(1)
        # pasting a multiline string works even with multiline disabled :(
        rv = rv.replace('\n', ' ').strip()
        if not rv:
            if not required:
                break
        else:
            if path:
                rv = os.path.abspath(os.path.expanduser(rv))
            if validate is None or validate(rv):
                break
            if allow_invalid and _confirm('Keep this value anyway?'):
                break
            default = rv
        first = False
    return rv


def _confirm(message, default=False, abort=False, help=None):
    def _get_prompt_tokens(cli):
        rv = [
            (Token.PROMPT, message),
            (Token.BRACKET, ' ['),
            (Token.DEFAULT, 'Y/n' if default else 'y/N'),
            (Token.BRACKET, ']'),
            (Token.COLON, ': '),
        ]
        if first and help:
            rv.insert(0, (Token.HELP, wrap_text(help) + '\n'))
        return rv

    first = True
    while True:
        try:
            rv = prompt(get_prompt_tokens=_get_prompt_tokens, lexer=SimpleLexer(Token.INPUT),
                        completer=WordCompleter(['yes', 'no'], ignore_case=True, sentence=True),
                        style=PROMPT_TOOLKIT_STYLE)
        except (EOFError, KeyboardInterrupt):
            sys.exit(1)
        first = False
        rv = rv.replace('\n', ' ').strip().lower()
        if rv in ('y', 'yes', '1', 'true'):
            rv = True
        elif rv in ('n', 'no', '0', 'false'):
            rv = False
        elif not rv:
            rv = default
        else:
            _warn('Invalid input, enter Y or N')
            continue
        break
    if abort and not rv:
        raise click.Abort
    return rv


@click.group()
def cli():
    """This script helps with the initial steps of installing Indico"""


@cli.command()
def list_plugins():
    """Lists the available indico plugins."""
    table_data = [['Name', 'Title']]
    for ep in sorted(iter_entry_points('indico.plugins'), key=attrgetter('name')):
        plugin = ep.load()
        table_data.append([ep.name, plugin.title])
    table = AsciiTable(table_data, cformat('%{white!}Available Plugins%{reset}'))
    click.echo(table.table)


@cli.command()
@click.argument('target_dir')
def create_symlinks(target_dir):
    """Creates useful symlinks to run Indico from a webserver.

    This lets you use static paths for the WSGI file and the htdocs
    folder so you do not need to update your webserver config when
    updating Indico.
    """
    root_dir, target_dir = _get_dirs(target_dir)
    _link(os.path.join(root_dir, 'htdocs'), os.path.join(target_dir, 'htdocs'))
    _copy(os.path.join(root_dir, 'web', 'indico.wsgi'), os.path.join(target_dir, 'indico.wsgi'), force=True)


@cli.command()
@click.argument('target_dir')
def create_logging_config(target_dir):
    """Creates the default logging config file for Indico.

    If a file already exists it is left untouched. This command is
    usually only used when doing a fresh indico installation when
    not using the setup wizard.
    """
    root_dir, target_dir = _get_dirs(target_dir)
    _copy(os.path.normpath(os.path.join(root_dir, 'logging.yaml.sample')), os.path.join(target_dir, 'logging.yaml'))


@cli.command()
@click.option('--dev', is_flag=True)
def wizard(dev):
    """Runs a setup wizard to configure Indico from scratch."""
    SetupWizard().run(dev=dev)


class SetupWizard(object):
    def __init__(self):
        self._missing_dirs = set()
        self.root_path = None
        self.data_root_path = None
        self.config_dir_path = None
        self.config_path = None
        self.indico_url = None
        self.db_uri = None
        self.redis_uri_celery = None
        self.redis_uri_cache = None
        self.contact_email = None
        self.admin_email = None
        self.noreply_email = None
        self.smtp_host = None
        self.smtp_port = None
        self.smtp_user = None
        self.smtp_password = None
        self.default_locale = None
        self.default_timezone = None
        self.rb_active = None
        self.old_archive_dir = None

    def run(self, dev):
        self._check_root()
        self._check_venv()
        self._prompt_root_path(dev=dev)
        self.config_dir_path = (get_root_path('indico') if dev else os.path.join(self.root_path, 'etc'))
        self.config_path = os.path.join(self.config_dir_path, 'indico.conf')
        self._check_configured()
        self._check_directories(dev=dev)
        self._prompt_indico_url(dev=dev)
        self._prompt_db_uri()
        self._prompt_redis_uris()
        self._prompt_emails()
        self._prompt_smtp_data(dev=dev)
        self._prompt_defaults()
        self._prompt_misc()
        if not dev:
            self._prompt_migration()
        self._setup(dev=dev)

    def _check_root(self):
        if os.getuid() == 0 or os.geteuid() == 0:
            _error('Indico must not be installed as root.')
            _error('Please create a user (e.g. `indico`) and run this script again using that user.')
            sys.exit(1)

    def _check_venv(self):
        if not hasattr(sys, 'real_prefix'):
            _warn('It looks like you are not using a virtualenv. This is unsupported and strongly discouraged.')
            _prompt_abort()

    def _prompt_root_path(self, dev=False):
        if dev:
            default_root = os.getcwd()
            if os.path.exists(os.path.join(default_root, '.git')):
                # based on the setup guide the most likely location to run
                # this commanad from is `~/dev/indico/src`, in which case
                # we want to go up a level since the data dir should not be
                # created inside the source directory
                default_root = os.path.dirname(default_root)
            default_root = default_root.decode(sys.getfilesystemencoding())
        else:
            default_root = '/opt/indico'
        self.root_path = _prompt('Indico root path', default=default_root, path=True,
                                 help='Enter the base directory where Indico will be installed.')
        # The root needs to exist (ideally created during `useradd`)
        if not os.path.isdir(self.root_path):
            _error('The specified self.root_path path does not exist.')
            raise click.Abort
        # There is no harm in having the virtualenv somewhere else but it
        # is cleaner to keep everything within the root path
        if not sys.prefix.startswith(self.root_path + '/'):
            _warn('It is recommended to have the virtualenv inside the root directory, e.g. {}/.venv'
                  .format(self.root_path))
            _warn('The virtualenv is currently located in {}'.format(sys.prefix))
            _prompt_abort()
        self.data_root_path = os.path.join(self.root_path, 'data') if dev else self.root_path

    def _check_configured(self):
        # Bail out early if indico is already configured
        if os.path.exists(self.config_path):
            _error('Config file already exists. If you really want to run this wizard again, delete {}'.format(
                self.config_path))
            raise click.Abort

    def _check_directories(self, dev=False):
        dirs = ['archive', 'assets', 'cache', 'log', 'tmp']
        if not dev:
            dirs += ['etc', 'web']

        _echo('Indico will use the following directories')
        has_existing = False
        for name in dirs:
            path = os.path.join(self.data_root_path, name)
            exists_suffix = ''
            if os.path.exists(path):
                has_existing = True
                exists_suffix = cformat(' %{yellow!}*%{reset}')
            else:
                self._missing_dirs.add(path)
            _echo(cformat('  %{blue!}{}%{reset}').format(path) + exists_suffix)
        if has_existing:
            _warn('The directories marked with a * already exist.  We strongly recommend installing Indico in a new '
                  'directory that contains nothing but the Python virtualenv.  If you are upgrading from Indico v1.2, '
                  'please move its data to a different location.')
            _prompt_abort()

    def _prompt_indico_url(self, dev=False):
        def _check_url(url):
            data = url_parse(url)
            if not data.scheme or not data.host:
                _warn('Invalid URL: scheme/host missing')
                return False
            elif data.fragment or data.query or data.auth:
                _warn('Invalid URL: must not contain fragment, query string or username/password')
                return False
            elif not dev and data.scheme != 'https':
                _warn('Unless this is a test instance it is HIGHLY RECOMMENDED to use an https:// URL')
                return False
            elif data.path not in ('', '/'):
                _warn('It is recommended to run Indico on a subdomain instead of a subdirectory')
                return False
            return True

        default_url = ('http://127.0.0.1:8000' if dev else 'https://{}'.format(socket.getfqdn()))
        url = _prompt('Indico URL', validate=_check_url, allow_invalid=True,
                      default=default_url,
                      help='Indico needs to know the URL through which it is accessible. '
                           'We strongly recommend using an https:// URL and a subdomain, e.g. '
                           'https://indico.yourdomain.com')
        self.indico_url = url.rstrip('/')

    def _prompt_db_uri(self):
        def _check_postgres(uri, silent=False):
            try:
                engine = create_engine(uri, connect_args={'connect_timeout': 3}, poolclass=NullPool)
                engine.connect().close()
            except OperationalError as exc:
                if not silent:
                    _warn('Invalid database URI: ' + unicode(exc.orig).strip())
                return False
            else:
                return True

        # Local postgres instance running and accessible?
        if _check_postgres('postgresql:///template1', silent=True):
            default = 'postgresql:///indico'
        else:
            default = 'postgresql://user:pass@host/indico'
        self.db_uri = _prompt('PostgreSQL database URI', default=default,
                              validate=_check_postgres, allow_invalid=True,
                              help='Enter the SQLAlchemy connection string to connect to your PostgreSQL database. '
                                   'For a remote database, use postgresql://user:pass@host/dbname')

    def _prompt_redis_uris(self):
        def _check_redis(uri):
            client = StrictRedis.from_url(uri)
            client.connection_pool.connection_kwargs['socket_timeout'] = 3
            try:
                client.ping()
            except RedisError as exc:
                _warn('Invalid redis URI: ' + unicode(exc))
                return False
            else:
                return True

        def _increase_redis_dbnum(uri):
            return re.sub(r'(?<=/)(\d+)$', lambda m: str(int(m.group(1)) + 1), uri)

        self.redis_uri_celery = _prompt('Redis URI (celery)', default='redis://127.0.0.1:6379/0',
                                        validate=_check_redis, allow_invalid=True,
                                        help='Indico uses Redis to manage scheduled/background tasks. '
                                             'Enter the URL to your Redis server. '
                                             'Running one locally is usually the easiest option.')
        self.redis_uri_cache = _prompt('Redis URI (cache)', default=_increase_redis_dbnum(self.redis_uri_celery),
                                       validate=_check_redis, allow_invalid=True,
                                       help='Redis is also used for caching. We recommend using a separate redis '
                                            'database, which allows you to clear the cache without affecting celery')

    def _prompt_emails(self):
        def _check_email(email):
            if is_valid_mail(email, False):
                return True
            _warn('Invalid email address')
            return False

        def _get_noreply_email(email):
            return 'noreply@' + email.split('@', 1)[1]

        self.contact_email = _prompt('Contact email', validate=_check_email, required=False,
                                     help='The Contact page displays this email address to users. '
                                          'If empty, the Contact page will be hidden.')
        self.admin_email = _prompt('Admin email', default=self.contact_email, validate=_check_email,
                                   help='If an error occurs Indico sends an email to the admin address. '
                                        'This should be the address of whoever is the technical manager of this '
                                        'Indico instance, i.e. most likely you.')
        self.noreply_email = _prompt('No-reply email',
                                     default=_get_noreply_email(self.contact_email or self.admin_email),
                                     validate=_check_email,
                                     help='When Indico sends email notifications they are usually sent from the '
                                          'noreply email.')

    def _prompt_smtp_data(self, dev=False):
        def _get_default_smtp(custom_host=None):
            if custom_host:
                candidates = [(custom_host, 25), (custom_host, 587)]
            else:
                candidates = [('127.0.0.1', 25), ('127.0.0.1', 587)]
            if dev:
                candidates.insert(0, (custom_host or '127.0.0.1', 1025))
            for host, port in candidates:
                try:
                    SMTP(host, port, timeout=3).close()
                except Exception:
                    continue
                return host, port
            return '', ''

        first = True
        default_smtp_host, default_smtp_port = _get_default_smtp()
        smtp_user = ''
        while True:
            smtp_host = _prompt('SMTP host', default=default_smtp_host,
                                help=('Indico needs an SMTP server to send emails.' if first else None))
            if smtp_host != default_smtp_host:
                default_smtp_port = _get_default_smtp(smtp_host)[1]
            smtp_port = int(_prompt('SMTP port', default=unicode(default_smtp_port or 25)))
            smtp_user = _prompt('SMTP username', default=smtp_user, required=False,
                                help=('If your SMTP server requires authentication, '
                                      'enter the username now.' if first else None))
            smtp_password = _prompt('SMTP password', password=True) if smtp_user else ''
            first = False
            # Test whether we can connect
            try:
                smtp = SMTP(smtp_host, smtp_port, timeout=10)
                smtp.ehlo_or_helo_if_needed()
                if smtp_user and smtp_password:
                    smtp.starttls()
                    smtp.login(smtp_user, smtp_password)
                smtp.quit()
            except Exception as exc:
                _warn('SMTP connection failed: ' + unicode(exc))
                if not click.confirm('Keep these settings anyway?'):
                    default_smtp_host = smtp_host
                    default_smtp_port = smtp_port
                    continue
            self.smtp_host = smtp_host
            self.smtp_port = smtp_port
            self.smtp_user = smtp_user
            self.smtp_password = smtp_password
            break

    def _prompt_defaults(self):
        def _get_all_locales():
            # get all directories in indico/translations
            return os.walk(os.path.join(get_root_path('indico'), 'translations')).next()[1]

        def _get_system_timezone():
            candidates = []
            # Get a timezone name directly
            if os.path.isfile('/etc/timezone'):
                with open('/etc/timezone') as f:
                    candidates.append(f.read().strip())
            # Get the timezone from the symlink
            if os.path.islink('/etc/localtime'):
                candidates.append(re.sub(r'.*/usr/share/zoneinfo/', '', os.readlink('/etc/localtime')))
            # We do not try to find a matching zoneinfo based on a checksum
            # as e.g. https://stackoverflow.com/a/12523283/298479 suggests
            # since this is ambiguous and we rather have the user type their
            # timezone if we don't have a very likely match.
            return next((unicode(tz) for tz in candidates if tz in common_timezones), '')

        self.default_locale = _prompt('Default locale', default='en_GB', list_=_get_all_locales(),
                                      help='Specify the default language/locale used by Indico.')

        self.default_timezone = _prompt('Default timezone', default=_get_system_timezone(), list_=common_timezones,
                                        validate=all_timezones.__contains__,
                                        help='Specify the default timezone used by Indico.')

    def _prompt_misc(self):
        self.rb_active = _confirm('Enable room booking?',
                                  help='Indico contains a room booking system. If you do not plan to maintain a list '
                                       'of rooms available in your organization in Indico and use it to book them, it '
                                       'is recommended to leave the room booking system disabled.')

    def _prompt_migration(self):
        def _check_path(path):
            if os.path.exists(path):
                return True
            _warn('Directory does not exist')
            return False

        self.old_archive_dir = _prompt('Old archive dir', path=True, required=False, validate=_check_path,
                                       allow_invalid=True,
                                       help='If you are upgrading from Indico 1.2, please specify the path to the '
                                            'ArchiveDir of the old indico version.  Leave this empty if you are not '
                                            'upgrading.')

    def _setup(self, dev=False):
        storage_backends = {'default': 'fs:' + os.path.join(self.data_root_path, 'archive')}
        if self.old_archive_dir:
            storage_backends['legacy'] = 'fs-readonly:' + self.old_archive_dir

        config_link_path = os.path.expanduser('~/.indico.conf')
        if not dev:
            create_config_link = _confirm('Create symlink?', default=True,
                                          help='By creating a symlink to indico.conf in {}, you can run '
                                               'indico without having to set the INDICO_CONFIG '
                                               'environment variable'.format(config_link_path))
        else:
            create_config_link = False

        config_data = [
            b'# General settings',
            b'SQLALCHEMY_DATABASE_URI = {!r}'.format(self.db_uri.encode('utf-8')),
            b'SECRET_KEY = {!r}'.format(os.urandom(32)),
            b'BASE_URL = {!r}'.format(self.indico_url.encode('utf-8')),
            b'CELERY_BROKER = {!r}'.format(self.redis_uri_celery.encode('utf-8')),
            b'REDIS_CACHE_URL = {!r}'.format(self.redis_uri_cache.encode('utf-8')),
            b"CACHE_BACKEND = 'redis'",
            b'DEFAULT_TIMEZONE = {!r}'.format(self.default_timezone.encode('utf-8')),
            b'DEFAULT_LOCALE = {!r}'.format(self.default_locale.encode('utf-8')),
            b'ENABLE_ROOMBOOKING = {!r}'.format(self.rb_active),
            b'CACHE_DIR = {!r}'.format(os.path.join(self.data_root_path, 'cache').encode('utf-8')),
            b'TEMP_DIR = {!r}'.format(os.path.join(self.data_root_path, 'tmp').encode('utf-8')),
            b'LOG_DIR = {!r}'.format(os.path.join(self.data_root_path, 'log').encode('utf-8')),
            b'ASSETS_DIR = {!r}'.format(os.path.join(self.data_root_path, 'assets').encode('utf-8')),
            b'STORAGE_BACKENDS = {!r}'.format({k.encode('utf-8'): v.encode('utf-8')
                                              for k, v in storage_backends.iteritems()}),
            b"ATTACHMENT_STORAGE = 'default'",
            b'ROUTE_OLD_URLS = True' if self.old_archive_dir else None,
            b'',
            b'# Email settings',
            b'SMTP_SERVER = {!r}'.format((self.smtp_host.encode('utf-8'), self.smtp_port)),
            b'SMTP_USE_TLS = {!r}'.format(bool(self.smtp_user and self.smtp_password)),
            b'SMTP_LOGIN = {!r}'.format(self.smtp_user.encode('utf-8')),
            b'SMTP_PASSWORD = {!r}'.format(self.smtp_password.encode('utf-8')),
            b'SUPPORT_EMAIL = {!r}'.format(self.admin_email.encode('utf-8')),
            b'PUBLIC_SUPPORT_EMAIL = {!r}'.format(self.contact_email.encode('utf-8')),
            b'NO_REPLY_EMAIL = {!r}'.format(self.noreply_email.encode('utf-8'))
        ]

        if dev:
            config_data += [
                b'',
                b'# Development options',
                b'DB_LOG = True',
                b'DEBUG = True',
                b'SMTP_USE_CELERY = False'
            ]

        config = b'\n'.join(x for x in config_data if x is not None)

        if dev:
            if not os.path.exists(self.data_root_path):
                os.mkdir(self.data_root_path)

        _echo()
        for path in self._missing_dirs:
            _echo(cformat('%{magenta}Creating %{magenta!}{}%{reset}%{magenta}').format(path))
            os.mkdir(path)

        _echo(cformat('%{magenta}Creating %{magenta!}{}%{reset}%{magenta}').format(self.config_path))
        with open(self.config_path, 'wb') as f:
            f.write(config + b'\n')

        package_root = get_root_path('indico')
        _copy(os.path.normpath(os.path.join(package_root, 'logging.yaml.sample')),
              os.path.join(self.config_dir_path, 'logging.yaml'))

        if not dev:
            _link(os.path.join(package_root, 'htdocs'), os.path.join(self.data_root_path, 'web', 'htdocs'))
            _copy(os.path.join(package_root, 'web', 'indico.wsgi'),
                  os.path.join(self.data_root_path, 'web', 'indico.wsgi'),
                  force=True)

        if create_config_link:
            _link(self.config_path, config_link_path)

        _echo()
        _echo(cformat('%{green}Indico has been configured successfully!'))
        if not dev and not create_config_link:
            _echo(cformat('Run %{green!}export INDICO_CONFIG={}%{reset} to use your config file')
                  .format(self.config_path))

        if self.old_archive_dir:
            _echo(cformat('Check %{green!}https://git.io/vHP6o%{reset} for a guide on how to '
                          'import data from Indico v1.2'))
        else:
            _echo(cformat('You can now run %{green!}indico db prepare%{reset} to initialize your Indico database'))
