# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
import shutil
import socket
import subprocess
import sys
from operator import attrgetter
from pathlib import Path
from smtplib import SMTP

import click
from click import wrap_text
from flask.helpers import get_root_path
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pkg_resources import iter_entry_points
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter, WordCompleter
from prompt_toolkit.styles import Style
from pytz import all_timezones, common_timezones
from redis import RedisError, StrictRedis
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool
from terminaltables import AsciiTable
from werkzeug.urls import url_parse

import indico
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.util.console import cformat
from indico.util.string import validate_email


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


PROMPT_TOOLKIT_STYLE = Style.from_dict({
    'help': '#aaaaaa',
    'prompt': '#5f87ff',
    'default': '#dfafff',
    'bracket': '#ffffff',
    'colon': '#ffffff',
    '': '#aaffaa',  # user input
})


def _prompt(message, default='', path=False, list_=None, required=True, validate=None, allow_invalid=False,
            password=False, help=None):
    def _get_prompt_tokens():
        rv = [
            ('class:prompt', message),
            ('class:colon', ': '),
        ]
        if first and help:
            rv.insert(0, ('class:help', wrap_text(help) + '\n'))
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
            rv = prompt(_get_prompt_tokens(), default=default, is_password=password,
                        completer=completer, style=PROMPT_TOOLKIT_STYLE)
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
    def _get_prompt_tokens():
        rv = [
            ('class:prompt', message),
            ('class:bracket', ' ['),
            ('class:default', 'Y/n' if default else 'y/N'),
            ('class:bracket', ']'),
            ('class:colon', ': '),
        ]
        if first and help:
            rv.insert(0, ('class:help', wrap_text(help) + '\n'))
        return rv

    first = True
    while True:
        try:
            rv = prompt(_get_prompt_tokens(),
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
    """This script helps with the initial steps of installing Indico."""


@cli.command()
def list_plugins():
    """List the available Indico plugins."""
    import_all_models()
    table_data = [['Name', 'Title']]
    for ep in sorted(iter_entry_points('indico.plugins'), key=attrgetter('name')):
        plugin = ep.load()
        table_data.append([ep.name, plugin.title])
    table = AsciiTable(table_data, cformat('%{white!}Available Plugins%{reset}'))
    click.echo(table.table)


@cli.command()
@click.argument('target_dir')
def create_symlinks(target_dir):
    """Create useful symlinks to run Indico from a webserver.

    This lets you use static paths for the WSGI file and the htdocs
    folder so you do not need to update your webserver config when
    updating Indico.
    """
    root_dir, target_dir = _get_dirs(target_dir)
    _link(os.path.join(root_dir, 'web', 'static'), os.path.join(target_dir, 'static'))
    _copy(os.path.join(root_dir, 'web', 'indico.wsgi'), os.path.join(target_dir, 'indico.wsgi'), force=True)


@cli.command()
@click.argument('target_dir')
def create_logging_config(target_dir):
    """Create the default logging config file for Indico.

    If a file already exists it is left untouched. This command is
    usually only used when doing a fresh indico installation when
    not using the setup wizard.
    """
    root_dir, target_dir = _get_dirs(target_dir)
    _copy(os.path.normpath(os.path.join(root_dir, 'logging.yaml.sample')), os.path.join(target_dir, 'logging.yaml'))


@cli.command()
@click.option('--check', is_flag=True, help='Only check for updates but do not actually update.')
@click.option('--no-pyenv-update', is_flag=True, help='Do not update pyenv')
@click.option('--local', is_flag=True,
              help='Set the local pyenv version instead of the global one. Do not use this in a standard Indico '
                   'deployment; it is only meant for development where you do not have a dedicated indico user.')
@click.option('--force-version',
              help='Force using a custom python version, regardless of the preferred version this Indico version has. '
                   'Only use this when explicitly asked to, either by a developer or in the upgrade instructions.')
@click.option('--venv', required=True, metavar='PATH', envvar='VIRTUAL_ENV',
              type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
              help='The path of the Python venv; defaults to the active one.')
def upgrade_python(check, no_pyenv_update, local, force_version, venv):
    """Upgrade the Python version used in the Indico virtualenv.

    When using `--check`, only Python versions currently available in pyenv will
    be used; make sure to `pyenv update` first (this is done automatically when
    you run this command without `--check`).

    Be careful when using `--force-version` with a custom version; you may end up
    using an unsupported version where this command will no longer work.
    """

    if not check and not no_pyenv_update:
        click.echo('updating pyenv')
        proc = subprocess.run(['pyenv', 'update'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode:
            click.echo(proc.stdout)
            click.confirm('pyenv update failed - continue anyway?', abort=True)

    pyenv_mode = 'local' if local else 'global'
    pyenv_version_list = subprocess.run(['pyenv', 'install', '--list'], capture_output=True,
                                        encoding='utf-8').stdout.splitlines()
    pyenv_versions = [Version(x) for line in pyenv_version_list
                      if (x := line.strip()) and re.match(r'^\d+\.\d+\.\d+$', x)]
    preferred_version_spec = SpecifierSet(indico.PREFERRED_PYTHON_VERSION_SPEC)
    current_version = Version('.'.join(map(str, sys.version_info[:3])))

    if force_version:
        preferred_version = Version(force_version)
        if preferred_version not in preferred_version_spec:
            click.echo(f'Warning: {preferred_version} is not within {preferred_version_spec} spec')
            click.confirm('Continue anyway?', abort=True)
    else:
        if not (available_versions := preferred_version_spec.filter(pyenv_versions)):
            click.echo(f'Found no qualifying versions for {preferred_version_spec}')
            sys.exit(1)
        preferred_version = max(available_versions)

    if current_version == preferred_version:
        click.echo(f'Already running on preferred version ({preferred_version})')
        sys.exit(0)

    if (preferred_version.major, preferred_version.minor) != (current_version.major, current_version.minor):
        old = f'{current_version.major}.{current_version.minor}'
        new = f'{preferred_version.major}.{preferred_version.minor}'
        click.echo(f'WARNING: You are upgrading from {old} to {new}. This upgrade CANNOT be done in-place.')
        click.echo('You will need to `pip install indico` (and any other packages such as plugins)\n'
                   'again after this upgrade! Do not perform this update, unless you are updating to\n'
                   'a new major Indico release which is documented to require this Python version!')
        click.confirm('Continue?', abort=True)

    pyenv_local_version = Version(subprocess.run(['pyenv', 'version-name'], capture_output=True,
                                                 encoding='utf-8').stdout.strip())
    if pyenv_local_version != preferred_version:
        click.echo(f'Currently selected version {pyenv_local_version} does not match '
                   f'preferred version {preferred_version}')
        if not check:
            click.echo(f'Installing python {preferred_version} (may take some time)')
            proc = subprocess.run(['pyenv', 'install', '--skip-existing', '--verbose', str(preferred_version)],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if proc.returncode:
                click.echo(proc.stdout)
                click.echo(f'Installing python {preferred_version} update failed')
                sys.exit(1)
            click.echo(f'Setting {pyenv_mode} pyenv version to {preferred_version}')
            subprocess.run(['pyenv', pyenv_mode, str(preferred_version)], check=True)
        else:
            click.echo(f'Would set {pyenv_mode} pyenv version to {preferred_version} (skipping due to --check)')

    # Upgrade the virtualenv in-place
    from . import python_upgrader
    args = [venv]
    if check:
        args.append('--check')
    # we need to run the upgrade script in an isolated environment to avoid any
    # of the currently-installed packages or PYTHONPATH info leaking into the
    # environment in case the venv builder needs to upgrade pip
    subprocess.run([sys.executable, '-I', python_upgrader.__file__, *args], check=True)


@cli.command()
@click.option('--dev', is_flag=True)
def wizard(dev):
    """Run a setup wizard to configure Indico from scratch."""
    SetupWizard().run(dev=dev)


class SetupWizard:
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
        self.system_notices = True

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
        self._setup(dev=dev)

    def _check_root(self):
        if os.getuid() == 0 or os.geteuid() == 0:
            _error('Indico must not be installed as root.')
            _error('Please create a user (e.g. `indico`) and run this script again using that user.')
            sys.exit(1)

    def _check_venv(self):
        if sys.prefix == sys.base_prefix:
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
        else:
            default_root = '/opt/indico'
        self.root_path = _prompt('Indico root path', default=default_root, path=True,
                                 help='Enter the base directory where Indico will be installed.')
        # The root needs to exist (ideally created during `useradd`)
        if not os.path.isdir(self.root_path):
            _error('The specified root path path does not exist.')
            raise click.Abort
        # There is no harm in having the virtualenv somewhere else but it
        # is cleaner to keep everything within the root path
        if not sys.prefix.startswith(self.root_path + '/'):
            _warn('It is recommended to have the virtualenv inside the root directory, e.g. {}/.venv'
                  .format(self.root_path))
            _warn(f'The virtualenv is currently located in {sys.prefix}')
            _prompt_abort()
        self.data_root_path = os.path.join(self.root_path, 'data') if dev else self.root_path

    def _check_configured(self):
        # Bail out early if indico is already configured
        if os.path.exists(self.config_path):
            _error('Config file already exists. If you really want to run this wizard again, delete {}'.format(
                self.config_path))
            raise click.Abort

    def _check_directories(self, dev=False):
        dirs = ['archive', 'cache', 'log', 'tmp']
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
                _warn('Unless you built your own indico package for the specified path, '
                      'Indico will not work correctly!')
                return False
            return True

        default_url = ('http://127.0.0.1:8000' if dev else f'https://{socket.getfqdn()}')
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
                    _warn('Invalid database URI: ' + str(exc.orig).strip())
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
                _warn('Invalid redis URI: ' + str(exc))
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
            if validate_email(email):
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
            smtp_port = int(_prompt('SMTP port', default=str(default_smtp_port or 25)))
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
                _warn('SMTP connection failed: ' + str(exc))
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
            root = Path(get_root_path('indico')) / 'translations'
            return [ent.name for ent in root.iterdir() if ent.is_dir()]

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
            return next((str(tz) for tz in candidates if tz in common_timezones), '')

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
        self.system_notices = _confirm('Enable system notices?', default=True,
                                       help='Indico can show important system notices (e.g. about security issues) to '
                                            'administrators. They are retrieved once a day without sending any data '
                                            'related to your Indico instance. It is strongly recommended to enable '
                                            'them.')

    def _setup(self, dev=False):
        storage_backends = {'default': 'fs:' + os.path.join(self.data_root_path, 'archive')}

        config_link_path = os.path.expanduser('~/.indico.conf')
        if not dev:
            create_config_link = _confirm('Create symlink?', default=True,
                                          help='By creating a symlink to indico.conf in {}, you can run '
                                               'indico without having to set the INDICO_CONFIG '
                                               'environment variable'.format(config_link_path))
        else:
            create_config_link = False

        config_data = [
            '# General settings',
            f'SQLALCHEMY_DATABASE_URI = {self.db_uri!r}',
            f'SECRET_KEY = {os.urandom(32)!r}',
            f'BASE_URL = {self.indico_url!r}',
            f'CELERY_BROKER = {self.redis_uri_celery!r}',
            f'REDIS_CACHE_URL = {self.redis_uri_cache!r}',
            f'DEFAULT_TIMEZONE = {self.default_timezone!r}',
            f'DEFAULT_LOCALE = {self.default_locale!r}',
            f'ENABLE_ROOMBOOKING = {self.rb_active!r}',
            'CACHE_DIR = {!r}'.format(os.path.join(self.data_root_path, 'cache')),
            'TEMP_DIR = {!r}'.format(os.path.join(self.data_root_path, 'tmp')),
            'LOG_DIR = {!r}'.format(os.path.join(self.data_root_path, 'log')),
            'STORAGE_BACKENDS = {!r}'.format({k: v
                                              for k, v in storage_backends.items()}),
            "ATTACHMENT_STORAGE = 'default'",
            '',
            '# Email settings',
            f'SMTP_SERVER = {(self.smtp_host, self.smtp_port)!r}',
            f'SMTP_USE_TLS = {bool(self.smtp_user and self.smtp_password)!r}',
            f'SMTP_LOGIN = {self.smtp_user!r}',
            f'SMTP_PASSWORD = {self.smtp_password!r}',
            f'SUPPORT_EMAIL = {self.admin_email!r}',
            f'PUBLIC_SUPPORT_EMAIL = {self.contact_email!r}',
            f'NO_REPLY_EMAIL = {self.noreply_email!r}'
        ]

        if dev:
            config_data += [
                '',
                '# Development options',
                'DB_LOG = True',
                'DEBUG = True',
                'SMTP_USE_CELERY = False'
            ]

        if not self.system_notices:
            config_data += [
                '',
                '# Disable system notices',
                'SYSTEM_NOTICES_URL = None'
            ]

        config = '\n'.join(x for x in config_data if x is not None)

        if dev:
            if not os.path.exists(self.data_root_path):
                os.mkdir(self.data_root_path)

        _echo()
        for path in self._missing_dirs:
            _echo(cformat('%{magenta}Creating %{magenta!}{}%{reset}%{magenta}').format(path))
            os.mkdir(path)

        _echo(cformat('%{magenta}Creating %{magenta!}{}%{reset}%{magenta}').format(self.config_path))
        with open(self.config_path, 'w') as f:
            f.write(config + '\n')

        package_root = get_root_path('indico')
        _copy(os.path.normpath(os.path.join(package_root, 'logging.yaml.sample')),
              os.path.join(self.config_dir_path, 'logging.yaml'))

        if not dev:
            _link(os.path.join(package_root, 'web', 'static'), os.path.join(self.data_root_path, 'web', 'static'))
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

        _echo(cformat('You can now run %{green!}indico db prepare%{reset} to initialize your Indico database'))
