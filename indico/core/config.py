# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

import ast
import codecs
import os
import re
import socket
import warnings
from datetime import timedelta

import pytz
from celery.schedules import crontab
from flask import current_app, g
from flask.helpers import get_root_path
from werkzeug.datastructures import ImmutableDict
from werkzeug.urls import url_parse

from indico.util.caching import make_hashable
from indico.util.fs import resolve_link
from indico.util.packaging import package_is_editable
from indico.util.string import crc32, snakify


DEFAULTS = {
    'ATTACHMENT_STORAGE': 'default',
    'AUTH_PROVIDERS': {},
    'BASE_URL': None,
    'CACHE_BACKEND': 'files',
    'CACHE_DIR': '/opt/indico/cache',
    'CATEGORY_CLEANUP': {},
    'CELERY_BROKER': None,
    'CELERY_CONFIG': {},
    'CELERY_RESULT_BACKEND': None,
    'COMMUNITY_HUB_URL': 'https://hub.getindico.io',
    'CUSTOMIZATION_DEBUG': False,
    'CUSTOMIZATION_DIR': None,
    'CUSTOM_COUNTRIES': {},
    'CUSTOM_LANGUAGES': {},
    'DB_LOG': False,
    'DEBUG': False,
    'DEFAULT_LOCALE': 'en_GB',
    'DEFAULT_TIMEZONE': 'UTC',
    'DISABLE_CELERY_CHECK': None,
    'ENABLE_ROOMBOOKING': False,
    'EXPERIMENTAL_EDITING_SERVICE': False,
    'EXTERNAL_REGISTRATION_URL': None,
    'FLOWER_URL': None,
    'HELP_URL': 'https://learn.getindico.io',
    'IDENTITY_PROVIDERS': {},
    'LOCAL_IDENTITIES': True,
    'LOCAL_MODERATION': False,
    'LOCAL_REGISTRATION': True,
    'LOCAL_GROUPS': True,
    'LOGGING_CONFIG_FILE': 'logging.yaml',
    'LOGO_URL': None,
    'LOG_DIR': '/opt/indico/log',
    'MAX_UPLOAD_FILES_TOTAL_SIZE': 0,
    'MAX_UPLOAD_FILE_SIZE': 0,
    'MEMCACHED_SERVERS': [],
    'NO_REPLY_EMAIL': None,
    'PLUGINS': set(),
    'PROFILE': False,
    'PROVIDER_MAP': {},
    'PUBLIC_SUPPORT_EMAIL': None,
    'REDIS_CACHE_URL': None,
    'ROUTE_OLD_URLS': False,
    'SCHEDULED_TASK_OVERRIDE': {},
    'SECRET_KEY': None,
    'SENTRY_DSN': None,
    'SENTRY_LOGGING_LEVEL': 'WARNING',
    'SESSION_LIFETIME': 86400 * 31,
    'SMTP_LOGIN': None,
    'SMTP_PASSWORD': None,
    'SMTP_SERVER': ('localhost', 25),
    'SMTP_TIMEOUT': 30,
    'SMTP_USE_CELERY': True,
    'SMTP_USE_TLS': False,
    'SQLALCHEMY_DATABASE_URI': None,
    'SQLALCHEMY_MAX_OVERFLOW': 3,
    'SQLALCHEMY_POOL_RECYCLE': 120,
    'SQLALCHEMY_POOL_SIZE': 5,
    'SQLALCHEMY_POOL_TIMEOUT': 10,
    'STATIC_FILE_METHOD': None,
    'STATIC_SITE_STORAGE': None,
    'STORAGE_BACKENDS': {'default': 'fs:/opt/indico/archive'},
    'STRICT_LATEX': False,
    'SUPPORT_EMAIL': None,
    'TEMP_DIR': '/opt/indico/tmp',
    'USE_PROXY': False,
    'WORKER_NAME': socket.getfqdn(),
    'XELATEX_PATH': None,
}

# Default values for settings that cannot be set in the config file
INTERNAL_DEFAULTS = {
    'CONFIG_PATH': os.devnull,
    'CONFIG_PATH_RESOLVED': None,
    'LOGGING_CONFIG_PATH': None,
    'TESTING': False
}


def get_config_path():
    """Get the path of the indico config file.

    This may return the location of a symlink.  Resolving a link is up
    to the caller if needed.
    """
    # In certain environments (debian+uwsgi+no-systemd) Indico may run
    # with an incorrect $HOME (such as /root), resulting in the config
    # files being searched in the wrong place. By clearing $HOME, Python
    # will get the home dir from passwd which has the correct path.
    old_home = os.environ.pop('HOME', None)
    # env var has priority
    try:
        return os.path.expanduser(os.environ['INDICO_CONFIG'])
    except KeyError:
        pass
    # try finding the config in various common paths
    paths = [os.path.expanduser('~/.indico.conf'), '/etc/indico.conf']
    # Keeping HOME unset wouldn't be too bad but let's not have weird side-effects
    if old_home is not None:
        os.environ['HOME'] = old_home
    # If it's an editable setup (ie usually a dev instance) allow having
    # the config in the package's root path
    if package_is_editable('indico'):
        paths.insert(0, os.path.normpath(os.path.join(get_root_path('indico'), 'indico.conf')))
    for path in paths:
        if os.path.exists(path):
            return path
    raise Exception('No indico config found. Point the INDICO_CONFIG env var to your config file or '
                    'move/symlink the config in one of the following locations: {}'.format(', '.join(paths)))


def _parse_config(path):
    globals_ = {'timedelta': timedelta, 'crontab': crontab}
    locals_ = {}
    with codecs.open(path, encoding='utf-8') as config_file:
        # XXX: unicode_literals is inherited from this file
        exec compile(config_file.read(), path, 'exec') in globals_, locals_
    return {unicode(k if k.isupper() else _convert_key(k)): v
            for k, v in locals_.iteritems()
            if k[0] != '_'}


def _convert_key(name):
    # camelCase to BIG_SNAKE while preserving acronyms, i.e.
    # FooBARs -> FOO_BARS (and not FOO_BA_RS)
    name = re.sub(r'([A-Z])([A-Z]+)', lambda m: m.group(1) + m.group(2).lower(), name)
    name = snakify(name).upper()
    special_cases = {'PDFLATEX_PROGRAM': 'XELATEX_PATH',
                     'IS_ROOM_BOOKING_ACTIVE': 'ENABLE_ROOMBOOKING'}
    return special_cases.get(name, name)


def _postprocess_config(data):
    if data['DEFAULT_TIMEZONE'] not in pytz.all_timezones_set:
        raise ValueError('Invalid default timezone: {}'.format(data['DEFAULT_TIMEZONE']))
    data['BASE_URL'] = data['BASE_URL'].rstrip('/')
    data['STATIC_SITE_STORAGE'] = data['STATIC_SITE_STORAGE'] or data['ATTACHMENT_STORAGE']
    if data['DISABLE_CELERY_CHECK'] is None:
        data['DISABLE_CELERY_CHECK'] = data['DEBUG']


def _sanitize_data(data, allow_internal=False):
    allowed = set(DEFAULTS)
    if allow_internal:
        allowed |= set(INTERNAL_DEFAULTS)
    for key in set(data) - allowed:
        warnings.warn('Ignoring unknown config key {}'.format(key))
    return {k: v for k, v in data.iteritems() if k in allowed}


def load_config(only_defaults=False, override=None):
    """Load the configuration data.

    :param only_defaults: Whether to load only the default options,
                          ignoring any user-specified config file
                          or environment-based overrides.
    :param override: An optional dict with extra values to add to
                     the configuration.  Any values provided here
                     will override values from the config file.
    """
    data = dict(DEFAULTS, **INTERNAL_DEFAULTS)
    if not only_defaults:
        path = get_config_path()
        config = _sanitize_data(_parse_config(path))
        data.update(config)
        env_override = os.environ.get('INDICO_CONF_OVERRIDE')
        if env_override:
            data.update(_sanitize_data(ast.literal_eval(env_override)))
        resolved_path = resolve_link(path) if os.path.islink(path) else path
        resolved_path = None if resolved_path == os.devnull else resolved_path
        data['CONFIG_PATH'] = path
        data['CONFIG_PATH_RESOLVED'] = resolved_path
        if resolved_path is not None:
            data['LOGGING_CONFIG_PATH'] = os.path.join(os.path.dirname(resolved_path), data['LOGGING_CONFIG_FILE'])

    if override:
        data.update(_sanitize_data(override, allow_internal=True))
    _postprocess_config(data)
    return ImmutableDict(data)


class IndicoConfig(object):
    """Wrapper for the Indico configuration.

    It exposes all config keys as read-only attributes.

    Dynamic configuration attributes whose value may change depending
    on other factors may be added as properties, but this should be
    kept to a minimum and is mostly there for legacy reasons.

    :param config: The dict containing the configuration data.
                   If omitted, it is taken from the active flask
                   application.  An explicit configuration dict should
                   not be specified except in special cases such as
                   the initial app configuration where no app context
                   is available yet.
    :param exc: The exception to raise when accessing an invalid
                config key.  This allows using the expected kind of
                exception in most cases but overriding it when
                exposing settings to Jinja where the default
                :exc:`AttributeError` would silently be turned into
                an empty string.
    """

    __slots__ = ('_config', '_exc')

    def __init__(self, config=None, exc=AttributeError):
        # yuck, but we don't allow writing to attributes directly
        object.__setattr__(self, '_config', config)
        object.__setattr__(self, '_exc', exc)

    @property
    def data(self):
        try:
            return self._config or current_app.config['INDICO']
        except KeyError:
            raise RuntimeError('config not loaded')

    @property
    def hash(self):
        return crc32(repr(make_hashable(sorted(self.data.items()))))

    @property
    def CONFERENCE_CSS_TEMPLATES_BASE_URL(self):
        return self.BASE_URL + '/css/confTemplates'

    @property
    def IMAGES_BASE_URL(self):
        return 'static/images' if g.get('static_site') else url_parse('{}/images'.format(self.BASE_URL)).path

    @property
    def LATEX_ENABLED(self):
        return bool(self.XELATEX_PATH)

    def __getattr__(self, name):
        try:
            return self.data[name]
        except KeyError:
            raise self._exc('no such setting: ' + name)

    def __setattr__(self, key, value):
        raise AttributeError('cannot change config at runtime')

    def __delattr__(self, key):
        raise AttributeError('cannot change config at runtime')


#: The global Indico configuration
config = IndicoConfig()
