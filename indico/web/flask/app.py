# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

import os
import uuid

from babel.numbers import format_currency, get_currency_name
from flask import _app_ctx_stack, request
from flask.helpers import get_root_path
from flask_pluginengine import current_plugin, plugins_loaded
from markupsafe import Markup
from packaging.version import Version
from pywebpack import WebpackBundleProject
from sqlalchemy.orm import configure_mappers
from werkzeug.exceptions import BadRequest
from werkzeug.local import LocalProxy
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.urls import url_parse
from wtforms.widgets import html_params

import indico
from indico.core import signals
from indico.core.auth import multipass
from indico.core.cache import cache
from indico.core.celery import celery
from indico.core.config import IndicoConfig, config, load_config
from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.logging import apply_db_loggers
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.core.logger import Logger
from indico.core.marshmallow import mm
from indico.core.plugins import plugin_engine, url_for_plugin
from indico.core.webpack import IndicoManifestLoader, webpack
from indico.modules.auth.providers import IndicoAuthProvider, IndicoIdentityProvider
from indico.modules.auth.util import url_for_login, url_for_logout
from indico.modules.oauth import oauth
from indico.util import date_time as date_time_util
from indico.util.i18n import _, babel, get_current_locale, gettext_context, ngettext_context
from indico.util.mimetypes import icon_from_mimetype
from indico.util.signals import values_from_signal
from indico.util.string import RichMarkup, alpha_enum, crc32, html_to_plaintext, sanitize_html, slugify
from indico.web.flask.errors import errors_bp
from indico.web.flask.stats import get_request_stats, setup_request_stats
from indico.web.flask.templating import (EnsureUnicodeExtension, call_template_hook, decodeprincipal, dedent, groupby,
                                         instanceof, markdown, natsort, plusdelta, subclassof, underline)
from indico.web.flask.util import ListConverter, XAccelMiddleware, discover_blueprints, url_for, url_rule_to_js
from indico.web.flask.wrappers import IndicoFlask
from indico.web.forms.jinja_helpers import is_single_line_field, iter_form_fields, render_field
from indico.web.menu import render_sidemenu
from indico.web.util import url_for_index
from indico.web.views import render_session_bar


def configure_app(app, set_path=False):
    config = IndicoConfig(app.config['INDICO'])  # needed since we don't have an app ctx yet
    app.config['DEBUG'] = config.DEBUG
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['LOGGER_NAME'] = 'flask.app'
    app.config['LOGGER_HANDLER_POLICY'] = 'never'
    if config.SENTRY_DSN:
        app.config['SENTRY_CONFIG'] = {
            'dsn': config.SENTRY_DSN,
            'release': indico.__version__
        }
    if not app.config['SECRET_KEY'] or len(app.config['SECRET_KEY']) < 16:
        raise ValueError('SECRET_KEY must be set to a random secret of at least 16 characters. '
                         'You can generate one using os.urandom(32) in Python shell.')
    if config.MAX_UPLOAD_FILES_TOTAL_SIZE > 0:
        app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_FILES_TOTAL_SIZE * 1024 * 1024
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['TRAP_HTTP_EXCEPTIONS'] = False
    app.config['TRAP_BAD_REQUEST_ERRORS'] = config.DEBUG
    app.config['SESSION_COOKIE_NAME'] = 'indico_session'
    app.config['PERMANENT_SESSION_LIFETIME'] = config.SESSION_LIFETIME
    configure_cache(app, config)
    configure_multipass(app, config)
    app.config['PLUGINENGINE_NAMESPACE'] = 'indico.plugins'
    app.config['PLUGINENGINE_PLUGINS'] = config.PLUGINS
    if set_path:
        base = url_parse(config.BASE_URL)
        app.config['PREFERRED_URL_SCHEME'] = base.scheme
        app.config['SERVER_NAME'] = base.netloc
        if base.path:
            app.config['APPLICATION_ROOT'] = base.path
    configure_xsendfile(app, config.STATIC_FILE_METHOD)
    if config.USE_PROXY:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    configure_webpack(app)


def configure_cache(app, config):
    # TODO: remove anything but redis in 3.0; nobody is using it and it
    # has not been tested recently.
    app.config['CACHE_DEFAULT_TIMEOUT'] = -1
    if app.config['TESTING']:
        app.config['CACHE_TYPE'] = 'simple'
    elif config.CACHE_BACKEND == 'redis':
        app.config['CACHE_TYPE'] = 'redis'
        app.config['CACHE_REDIS_URL'] = config.REDIS_CACHE_URL
    elif config.CACHE_BACKEND == 'memcached':
        app.config['CACHE_TYPE'] = 'memcached'
        app.config['CACHE_MEMCACHED_SERVERS'] = config.MEMCACHED_SERVERS
    elif config.CACHE_BACKEND == 'files':
        app.config['CACHE_TYPE'] = 'filesystem'
        app.config['CACHE_DIR'] = os.path.join(config.CACHE_DIR, 'flask-cache')


def configure_multipass(app, config):
    app.config['MULTIPASS_AUTH_PROVIDERS'] = config.AUTH_PROVIDERS
    app.config['MULTIPASS_IDENTITY_PROVIDERS'] = config.IDENTITY_PROVIDERS
    app.config['MULTIPASS_PROVIDER_MAP'] = config.PROVIDER_MAP or {x: x for x in config.AUTH_PROVIDERS}
    if 'indico' in app.config['MULTIPASS_AUTH_PROVIDERS'] or 'indico' in app.config['MULTIPASS_IDENTITY_PROVIDERS']:
        raise ValueError('The name `indico` is reserved and cannot be used as an Auth/Identity provider name.')
    if config.LOCAL_IDENTITIES:
        configure_multipass_local(app)
    app.config['MULTIPASS_IDENTITY_INFO_KEYS'] = {'first_name', 'last_name', 'email', 'affiliation', 'phone',
                                                  'address'}
    app.config['MULTIPASS_LOGIN_ENDPOINT'] = 'auth.login'
    app.config['MULTIPASS_LOGIN_URLS'] = None  # registered in a blueprint
    app.config['MULTIPASS_SUCCESS_ENDPOINT'] = 'categories.display'
    app.config['MULTIPASS_FAILURE_MESSAGE'] = _('Login failed: {error}')


def configure_multipass_local(app):
    app.config['MULTIPASS_AUTH_PROVIDERS'] = dict(app.config['MULTIPASS_AUTH_PROVIDERS'], indico={
        'type': IndicoAuthProvider,
        'title': 'Indico',
        'default': not any(p.get('default') for p in app.config['MULTIPASS_AUTH_PROVIDERS'].itervalues())
    })
    app.config['MULTIPASS_IDENTITY_PROVIDERS'] = dict(app.config['MULTIPASS_IDENTITY_PROVIDERS'], indico={
        'type': IndicoIdentityProvider,
        # We don't want any user info from this provider
        'identity_info_keys': {}
    })
    app.config['MULTIPASS_PROVIDER_MAP'] = dict(app.config['MULTIPASS_PROVIDER_MAP'], indico='indico')


def configure_webpack(app):
    pkg_path = os.path.dirname(get_root_path('indico'))
    project = WebpackBundleProject(pkg_path, None)
    app.config['WEBPACKEXT_PROJECT'] = project
    app.config['WEBPACKEXT_MANIFEST_LOADER'] = IndicoManifestLoader
    app.config['WEBPACKEXT_MANIFEST_PATH'] = os.path.join('dist', 'manifest.json')


def configure_xsendfile(app, method):
    if not method:
        return
    elif isinstance(method, basestring):
        args = None
    else:
        method, args = method
        if not method:
            return
    app.config['USE_X_SENDFILE'] = True
    if method == 'xsendfile':  # apache mod_xsendfile, lighttpd
        pass
    elif method == 'xaccelredirect':  # nginx
        if not args or not hasattr(args, 'items'):
            raise ValueError('STATIC_FILE_METHOD args must be a dict containing at least one mapping')
        app.wsgi_app = XAccelMiddleware(app.wsgi_app, args)
    else:
        raise ValueError('Invalid static file method: %s' % method)


def _get_indico_version():
    version = Version(indico.__version__)
    version_parts = [version.base_version]
    if version.is_prerelease:
        version_parts.append('pre')
    return 'v' + '-'.join(version_parts)


def setup_jinja(app):
    app.jinja_env.policies['ext.i18n.trimmed'] = True
    # Unicode hack
    app.jinja_env.add_extension(EnsureUnicodeExtension)
    app.add_template_filter(EnsureUnicodeExtension.ensure_unicode)
    # Useful (Python) builtins
    app.add_template_global(dict)
    # Global functions
    app.add_template_global(url_for)
    app.add_template_global(url_for_plugin)
    app.add_template_global(url_rule_to_js)
    app.add_template_global(IndicoConfig(exc=Exception), 'indico_config')
    app.add_template_global(call_template_hook, 'template_hook')
    app.add_template_global(is_single_line_field, '_is_single_line_field')
    app.add_template_global(render_field, '_render_field')
    app.add_template_global(iter_form_fields, '_iter_form_fields')
    app.add_template_global(format_currency)
    app.add_template_global(get_currency_name)
    app.add_template_global(url_for_index)
    app.add_template_global(url_for_login)
    app.add_template_global(url_for_logout)
    app.add_template_global(lambda: unicode(uuid.uuid4()), 'uuid')
    app.add_template_global(icon_from_mimetype)
    app.add_template_global(render_sidemenu)
    app.add_template_global(slugify)
    app.add_template_global(lambda: date_time_util.now_utc(False), 'now')
    app.add_template_global(render_session_bar)
    app.add_template_global(get_request_stats)
    app.add_template_global(_get_indico_version(), 'indico_version')
    # Global variables
    app.add_template_global(LocalProxy(get_current_locale), 'current_locale')
    app.add_template_global(LocalProxy(lambda: current_plugin.manifest if current_plugin else None), 'plugin_webpack')
    # Useful constants
    app.add_template_global('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$', name='time_regex_hhmm')  # for input[type=time]
    # Filters (indico functions returning UTF8)
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_date))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_time))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_datetime))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_human_date))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_timedelta))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_number))
    # Filters (new ones returning unicode)
    app.add_template_filter(date_time_util.format_human_timedelta)
    app.add_template_filter(date_time_util.format_pretty_date)
    app.add_template_filter(date_time_util.format_pretty_datetime)
    app.add_template_filter(lambda d: Markup(html_params(**d)), 'html_params')
    app.add_template_filter(underline)
    app.add_template_filter(markdown)
    app.add_template_filter(dedent)
    app.add_template_filter(html_to_plaintext)
    app.add_template_filter(natsort)
    app.add_template_filter(groupby)
    app.add_template_filter(plusdelta)
    app.add_template_filter(decodeprincipal)
    app.add_template_filter(any)
    app.add_template_filter(alpha_enum)
    app.add_template_filter(crc32)
    app.add_template_filter(bool)
    app.add_template_filter(lambda s: Markup(sanitize_html(s or '')), 'sanitize_html')
    app.add_template_filter(RichMarkup, 'rich_markup')
    # Tests
    app.add_template_test(instanceof)  # only use this test if you really have to!
    app.add_template_test(subclassof)  # only use this test if you really have to!
    # i18n
    app.jinja_env.add_extension('jinja2.ext.i18n')
    app.jinja_env.install_gettext_callables(gettext_context, ngettext_context, True)


def setup_jinja_customization(app):
    # add template customization paths provided by plugins
    paths = values_from_signal(signals.plugin.get_template_customization_paths.send())
    app.jinja_env.loader.fs_loader.searchpath += sorted(paths)


def configure_db(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if app.config['TESTING']:
        # tests do not actually use sqlite but run a postgres instance and
        # reconfigure flask-sqlalchemy to use that database.  by setting
        # a dummy uri explicitly instead of letting flask-sqlalchemy do
        # the exact same thing we avoid a warning when running tests.
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
    else:
        if config.SQLALCHEMY_DATABASE_URI is None:
            raise Exception("No proper SQLAlchemy store has been configured. Please edit your indico.conf")

        app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_RECORD_QUERIES'] = False
        app.config['SQLALCHEMY_POOL_SIZE'] = config.SQLALCHEMY_POOL_SIZE
        app.config['SQLALCHEMY_POOL_TIMEOUT'] = config.SQLALCHEMY_POOL_TIMEOUT
        app.config['SQLALCHEMY_POOL_RECYCLE'] = config.SQLALCHEMY_POOL_RECYCLE
        app.config['SQLALCHEMY_MAX_OVERFLOW'] = config.SQLALCHEMY_MAX_OVERFLOW

    import_all_models()
    db.init_app(app)
    if not app.config['TESTING']:
        apply_db_loggers(app)

    plugins_loaded.connect(lambda sender: configure_mappers(), app, weak=False)


def extend_url_map(app):
    app.url_map.converters['list'] = ListConverter


def add_handlers(app):
    app.before_request(reject_nuls)
    app.after_request(inject_current_url)
    app.register_blueprint(errors_bp)


def add_blueprints(app):
    blueprints, compat_blueprints = discover_blueprints()
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    if config.ROUTE_OLD_URLS:
        for blueprint in compat_blueprints:
            app.register_blueprint(blueprint)


def add_plugin_blueprints(app):
    blueprint_names = set()
    for plugin, blueprint in values_from_signal(signals.plugin.get_blueprints.send(app), return_plugins=True):
        expected_names = {'plugin_{}'.format(plugin.name), 'plugin_compat_{}'.format(plugin.name)}
        if blueprint.name not in expected_names:
            raise Exception("Blueprint '{}' does not match plugin name '{}'".format(blueprint.name, plugin.name))
        if blueprint.name in blueprint_names:
            raise Exception("Blueprint '{}' defined by multiple plugins".format(blueprint.name))
        if not config.ROUTE_OLD_URLS and blueprint.name.startswith('plugin_compat_'):
            continue
        blueprint_names.add(blueprint.name)
        with plugin.plugin_context():
            app.register_blueprint(blueprint)


def reject_nuls():
    for key, values in request.values.iterlists():
        if '\0' in key or any('\0' in x for x in values):
            raise BadRequest('NUL byte found in request data')


def inject_current_url(response):
    # Make the current URL available. This is useful e.g. in case of
    # AJAX requests that were redirected due to url normalization if
    # we need to know the actual URL
    url = request.relative_url
    # Headers cannot continue linebreaks; and while Flask rejects such
    # headers on its own it comes with a ValueError.
    if '\r' in url or '\n' in url:
        return response
    try:
        # Werkzeug encodes header values as latin1 in Python2.
        # In case of URLs containing utter garbage (usually a 404
        # anyway) they may not be latin1-compatible so let's not
        # add the header at all in this case instead of failing later
        url.encode('latin1')
    except UnicodeEncodeError:
        return response
    response.headers['X-Indico-URL'] = url
    return response


def make_app(set_path=False, testing=False, config_override=None):
    # If you are reading this code and wonder how to access the app:
    # >>> from flask import current_app as app
    # This only works while inside an application context but you really shouldn't have any
    # reason to access it outside this method without being inside an application context.
    # When set_path is enabled, SERVER_NAME and APPLICATION_ROOT are set according to BASE_URL
    # so URLs can be generated without an app context, e.g. in the indico shell

    if _app_ctx_stack.top:
        Logger.get('flask').warn('make_app called within app context, using existing app')
        return _app_ctx_stack.top.app
    app = IndicoFlask('indico', static_folder='web/static', static_url_path='/', template_folder='web/templates')
    app.config['TESTING'] = testing
    app.config['INDICO'] = load_config(only_defaults=testing, override=config_override)
    configure_app(app, set_path)

    with app.app_context():
        if not testing:
            Logger.init(app)
        celery.init_app(app)
        cache.init_app(app)
        babel.init_app(app)
        multipass.init_app(app)
        oauth.init_app(app)
        webpack.init_app(app)
        setup_jinja(app)
        configure_db(app)
        mm.init_app(app)  # must be called after `configure_db`!
        extend_url_map(app)
        add_handlers(app)
        setup_request_stats(app)
        add_blueprints(app)
        plugin_engine.init_app(app, Logger.get('plugins'))
        if not plugin_engine.load_plugins(app):
            raise Exception('Could not load some plugins: {}'.format(', '.join(plugin_engine.get_failed_plugins(app))))
        setup_jinja_customization(app)
        # Below this points plugins are available, i.e. sending signals makes sense
        add_plugin_blueprints(app)
        # themes can be provided by plugins
        signals.app_created.send(app)
    return app
