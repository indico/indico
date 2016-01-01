# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from __future__ import absolute_import

import os
import re
import traceback
import uuid

from babel.numbers import format_currency, get_currency_name
from flask import send_from_directory, request, _app_ctx_stack
from flask import current_app
from flask_sqlalchemy import models_committed
from flask_pluginengine import plugins_loaded
from markupsafe import Markup
from sqlalchemy.orm import configure_mappers
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.exceptions import NotFound
from werkzeug.urls import url_parse
from wtforms.widgets import html_params

from MaKaC.common import HelperMaKaCInfo
from MaKaC.webinterface.pages.error import WErrorWSGI

import indico.util.date_time as date_time_util
from indico.core.config import Config
from indico.core import signals
from indico.util.i18n import gettext_context, ngettext_context, babel, _
from indico.core.logger import Logger

from indico.core.auth import multipass
from indico.core.celery import celery
from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.core import on_models_committed
from indico.core.db.sqlalchemy.logging import apply_db_loggers
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.core.plugins import plugin_engine, include_plugin_css_assets, include_plugin_js_assets, url_for_plugin
from indico.modules.auth.providers import IndicoAuthProvider
from indico.modules.auth.providers import IndicoIdentityProvider
from indico.modules.auth.util import url_for_login, url_for_logout
from indico.modules.oauth import oauth
from indico.util.mimetypes import icon_from_mimetype
from indico.util.signals import values_from_signal
from indico.util.string import alpha_enum
from indico.web.assets import core_env, register_all_css, register_all_js, include_js_assets, include_css_assets
from indico.web.flask.templating import (EnsureUnicodeExtension, underline, markdown, dedent, natsort, instanceof,
                                         subclassof, call_template_hook, groupby, strip_tags)
from indico.web.flask.util import (XAccelMiddleware, make_compat_blueprint, ListConverter, url_for, url_rule_to_js,
                                   IndicoConfigWrapper, discover_blueprints)
from indico.web.flask.wrappers import IndicoFlask
from indico.web.forms.jinja_helpers import is_single_line_field, render_field, iter_form_fields


#: Blueprint names for which legacy rules are auto-generated based on the endpoint name
AUTO_COMPAT_BLUEPRINTS = {'admin', 'category', 'category_mgmt', 'event', 'event_creation', 'event_mgmt',
                          'misc', 'rooms', 'rooms_admin'}


def fix_root_path(app):
    """Fix the app's root path when using namespace packages.

    Flask's get_root_path is not reliable in this case so we derive it from
    __name__ and __file__ instead."""

    # __name__:       'indico.web.flask.app'
    # __file__:  '..../indico/web/flask/app.py'
    # For each dot in the module name we go up one path segment
    up_segments = ['..'] * __name__.count('.')
    app.root_path = os.path.normpath(os.path.join(__file__, *up_segments))


def configure_app(app, set_path=False):
    cfg = Config.getInstance()
    app.config['DEBUG'] = cfg.getDebug()
    app.config['SECRET_KEY'] = cfg.getSecretKey()
    if not app.config['SECRET_KEY'] or len(app.config['SECRET_KEY']) < 16:
        raise ValueError('SecretKey must be set to a random secret of at least 16 characters. '
                         'You can generate one using os.urandom(32) in Python shell.')
    if cfg.getMaxUploadFilesTotalSize() > 0:
        app.config['MAX_CONTENT_LENGTH'] = cfg.getMaxUploadFilesTotalSize() * 1024 * 1024
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['SESSION_COOKIE_NAME'] = 'indico_session'
    app.config['PERMANENT_SESSION_LIFETIME'] = cfg.getSessionLifetime()
    app.config['INDICO_SESSION_PERMANENT'] = cfg.getSessionLifetime() > 0
    app.config['INDICO_HTDOCS'] = cfg.getHtdocsDir()
    app.config['INDICO_COMPAT_ROUTES'] = cfg.getRouteOldUrls()
    configure_multipass(app)
    app.config['PLUGINENGINE_NAMESPACE'] = 'indico.plugins'
    app.config['PLUGINENGINE_PLUGINS'] = cfg.getPlugins()
    if set_path:
        base = url_parse(cfg.getBaseURL())
        app.config['PREFERRED_URL_SCHEME'] = base.scheme
        app.config['SERVER_NAME'] = base.netloc
        if base.path:
            app.config['APPLICATION_ROOT'] = base.path
    static_file_method = cfg.getStaticFileMethod()
    if static_file_method:
        app.config['USE_X_SENDFILE'] = True
        method, args = static_file_method
        if method in ('xsendfile', 'lighttpd'):  # apache mod_xsendfile, lighttpd
            pass
        elif method in ('xaccelredirect', 'nginx'):  # nginx
            if not args or not hasattr(args, 'items'):
                raise ValueError('StaticFileMethod args must be a dict containing at least one mapping')
            app.wsgi_app = XAccelMiddleware(app.wsgi_app, args)
        else:
            raise ValueError('Invalid static file method: %s' % method)
    if Config.getInstance().getUseProxy():
        app.wsgi_app = ProxyFix(app.wsgi_app)


def configure_multipass(app):
    cfg = Config.getInstance()
    app.config['MULTIPASS_AUTH_PROVIDERS'] = cfg.getAuthProviders()
    app.config['MULTIPASS_IDENTITY_PROVIDERS'] = cfg.getIdentityProviders()
    app.config['MULTIPASS_PROVIDER_MAP'] = cfg.getProviderMap() or {x: x for x in cfg.getAuthProviders()}
    if 'indico' in app.config['MULTIPASS_AUTH_PROVIDERS'] or 'indico' in app.config['MULTIPASS_IDENTITY_PROVIDERS']:
        raise ValueError('The name `indico` is reserved and cannot be used as an Auth/Identity provider name.')
    if cfg.getLocalIdentities():
        configure_multipass_local(app)
    app.config['MULTIPASS_IDENTITY_INFO_KEYS'] = {'first_name', 'last_name', 'email', 'affiliation', 'phone',
                                                  'address'}
    app.config['MULTIPASS_LOGIN_ENDPOINT'] = 'auth.login'
    app.config['MULTIPASS_LOGIN_URLS'] = None  # registered in a blueprint
    app.config['MULTIPASS_SUCCESS_ENDPOINT'] = 'misc.index'
    app.config['MULTIPASS_FAILURE_MESSAGE'] = _(u'Login failed: {error}')


def configure_multipass_local(app):
    app.config['MULTIPASS_AUTH_PROVIDERS']['indico'] = {
        'type': IndicoAuthProvider,
        'title': 'Indico',
        'default': not any(p.get('default') for p in app.config['MULTIPASS_AUTH_PROVIDERS'].itervalues())
    }
    app.config['MULTIPASS_IDENTITY_PROVIDERS']['indico'] = {
        'type': IndicoIdentityProvider,
        # We don't want any user info from this provider
        'identity_info_keys': {}
    }
    app.config['MULTIPASS_PROVIDER_MAP']['indico'] = 'indico'


def setup_jinja(app):
    config = Config.getInstance()
    # Unicode hack
    app.jinja_env.add_extension(EnsureUnicodeExtension)
    app.add_template_filter(EnsureUnicodeExtension.ensure_unicode)
    # Useful (Python) builtins
    app.add_template_global(dict)
    # Global functions
    app.add_template_global(url_for)
    app.add_template_global(url_for_plugin)
    app.add_template_global(url_rule_to_js)
    app.add_template_global(IndicoConfigWrapper(config), 'indico_config')
    app.add_template_global(config.getSystemIconURL, 'system_icon')
    app.add_template_global(include_css_assets)
    app.add_template_global(include_js_assets)
    app.add_template_global(include_plugin_css_assets)
    app.add_template_global(include_plugin_js_assets)
    app.add_template_global(call_template_hook, 'template_hook')
    app.add_template_global(is_single_line_field, '_is_single_line_field')
    app.add_template_global(render_field, '_render_field')
    app.add_template_global(iter_form_fields, '_iter_form_fields')
    app.add_template_global(format_currency)
    app.add_template_global(get_currency_name)
    app.add_template_global(url_for_login)
    app.add_template_global(url_for_logout)
    app.add_template_global(lambda: unicode(uuid.uuid4()), 'uuid')
    app.add_template_global(icon_from_mimetype)
    # Filters (indico functions returning UTF8)
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_date))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_time))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_datetime))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_human_date))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_timedelta))
    # Filters (new ones returning unicode)
    app.add_template_filter(date_time_util.format_human_timedelta)
    app.add_template_filter(lambda d: Markup(html_params(**d)), 'html_params')
    app.add_template_filter(underline)
    app.add_template_filter(markdown)
    app.add_template_filter(dedent)
    app.add_template_filter(natsort)
    app.add_template_filter(groupby)
    app.add_template_filter(any)
    app.add_template_filter(strip_tags)
    app.add_template_filter(alpha_enum)
    # Tests
    app.add_template_test(instanceof)  # only use this test if you really have to!
    app.add_template_test(subclassof)  # only use this test if you really have to!
    # i18n
    app.jinja_env.add_extension('jinja2.ext.i18n')
    app.jinja_env.install_gettext_callables(gettext_context, ngettext_context, True)
    app.add_template_global(lambda: HelperMaKaCInfo.getMaKaCInfoInstance().getLang(), 'get_default_language')
    # webassets
    app.jinja_env.add_extension('webassets.ext.jinja2.AssetsExtension')
    app.jinja_env.assets_environment = core_env


ASSETS_REGISTERED = False


def setup_assets():
    global ASSETS_REGISTERED
    if ASSETS_REGISTERED:
        # Avoid errors when forking after creating an app
        return
    ASSETS_REGISTERED = True
    register_all_js(core_env)
    register_all_css(core_env, Config.getInstance().getCssStylesheetName())


def configure_db(app):
    if not app.config['TESTING']:
        cfg = Config.getInstance()
        db_uri = cfg.getSQLAlchemyDatabaseURI()

        if db_uri is None:
            raise Exception("No proper SQLAlchemy store has been configured. Please edit your indico.conf")

        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

        # DB options
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        app.config['SQLALCHEMY_ECHO'] = cfg.getSQLAlchemyEcho()
        app.config['SQLALCHEMY_RECORD_QUERIES'] = cfg.getSQLAlchemyRecordQueries()
        app.config['SQLALCHEMY_POOL_SIZE'] = cfg.getSQLAlchemyPoolSize()
        app.config['SQLALCHEMY_POOL_TIMEOUT'] = cfg.getSQLAlchemyPoolTimeout()
        app.config['SQLALCHEMY_POOL_RECYCLE'] = cfg.getSQLAlchemyPoolRecycle()
        app.config['SQLALCHEMY_MAX_OVERFLOW'] = cfg.getSQLAlchemyMaxOverflow()

    import_all_models()
    db.init_app(app)
    if not app.config['TESTING']:
        apply_db_loggers(app)

    plugins_loaded.connect(lambda sender: configure_mappers(), app, weak=False)
    models_committed.connect(on_models_committed, app)


def extend_url_map(app):
    app.url_map.converters['list'] = ListConverter


def add_handlers(app):
    app.register_error_handler(404, handle_404)
    app.register_error_handler(Exception, handle_exception)


def add_blueprints(app):
    blueprints, compat_blueprints = discover_blueprints()
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    if app.config['INDICO_COMPAT_ROUTES']:
        compat_blueprints |= {make_compat_blueprint(bp) for bp in blueprints if bp.name in AUTO_COMPAT_BLUEPRINTS}
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
        if not app.config['INDICO_COMPAT_ROUTES'] and blueprint.name.startswith('plugin_compat_'):
            continue
        blueprint_names.add(blueprint.name)
        with plugin.plugin_context():
            app.register_blueprint(blueprint)


def handle_404(exception):
    try:
        if re.search(r'\.py(?:/\S+)?$', request.path):
            # While not dangerous per se, we never serve *.py files as static
            raise NotFound
        try:
            return send_from_directory(current_app.config['INDICO_HTDOCS'], request.path[1:], conditional=True)
        except UnicodeEncodeError:
            raise NotFound
    except NotFound:
        if exception.description == NotFound.description:
            # The default reason is too long and not localized
            msg = (_("Page not found"), _("The page you are looking for doesn't exist."))
        else:
            msg = (_("Page not found"), exception.description)
        return WErrorWSGI(msg).getHTML(), 404


def handle_exception(exception):
    Logger.get('wsgi').exception(exception.message or 'WSGI Exception')
    if current_app.debug:
        raise
    msg = (str(exception), _("An unexpected error ocurred."))
    return WErrorWSGI(msg).getHTML(), 500


def make_app(set_path=False, db_setup=True, testing=False):
    # If you are reading this code and wonder how to access the app:
    # >>> from flask import current_app as app
    # This only works while inside an application context but you really shouldn't have any
    # reason to access it outside this method without being inside an application context.
    # When set_path is enabled, SERVER_NAME and APPLICATION_ROOT are set according to BaseURL
    # so URLs can be generated without an app context, e.g. in the indico shell

    if _app_ctx_stack.top:
        Logger.get('flask').warn('make_app({}) called within app context, using existing app:\n{}'.format(
            set_path, '\n'.join(traceback.format_stack())))
        return _app_ctx_stack.top.app
    app = IndicoFlask('indico', static_folder=None, template_folder='web/templates')
    app.config['TESTING'] = testing
    fix_root_path(app)
    configure_app(app, set_path)
    celery.init_app(app)

    babel.init_app(app)
    multipass.init_app(app)
    oauth.init_app(app)
    setup_jinja(app)

    with app.app_context():
        setup_assets()

    if db_setup:
        configure_db(app)

    extend_url_map(app)
    add_handlers(app)
    add_blueprints(app)
    Logger.init_app(app)
    plugin_engine.init_app(app, Logger.get('plugins'))
    if not plugin_engine.load_plugins(app):
        raise Exception('Could not load some plugins: {}'.format(', '.join(plugin_engine.get_failed_plugins(app))))
    # Below this points plugins are available, i.e. sending signals makes sense
    add_plugin_blueprints(app)
    signals.app_created.send(app)
    return app
