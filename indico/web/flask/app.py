# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import os
import re

from flask import send_from_directory, request, _app_ctx_stack
from flask import current_app as app
from flask.ext.sqlalchemy import models_committed
from sqlalchemy.orm import configure_mappers
from werkzeug.exceptions import NotFound
from werkzeug.urls import url_parse

import indico.util.date_time as date_time_util
from indico.core.config import Config
from indico.util.i18n import gettext, ngettext
from indico.core.logger import Logger
from MaKaC.i18n import _
from MaKaC.plugins.base import RHMapMemory
from MaKaC.webinterface.pages.error import WErrorWSGI

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.core import on_models_committed
from indico.core.db.sqlalchemy.logging import apply_db_loggers
from indico.web.assets import core_env, register_all_css, register_all_js
from indico.web.flask.templating import EnsureUnicodeExtension, underline
from indico.web.flask.util import (XAccelMiddleware, make_compat_blueprint, ListConverter, url_for, url_rule_to_js,
                                   IndicoConfigWrapper)
from indico.web.flask.wrappers import IndicoFlask

from indico.web.flask.blueprints.legacy import legacy
from indico.web.flask.blueprints.rooms import rooms
from indico.web.flask.blueprints.api import api
from indico.web.flask.blueprints.misc import misc
from indico.web.flask.blueprints.user import user
from indico.web.flask.blueprints.oauth import oauth
from indico.web.flask.blueprints.category import category
from indico.web.flask.blueprints.category_management import category_mgmt
from indico.web.flask.blueprints.event import event_display, event_creation, event_mgmt
from indico.web.flask.blueprints.files import files
from indico.web.flask.blueprints.admin import admin
from indico.web.flask.blueprints.rooms_admin import rooms_admin


BLUEPRINTS = (legacy, api, misc, user, oauth, rooms, category, category_mgmt, event_display,
              event_creation, event_mgmt, files, admin, rooms_admin)
COMPAT_BLUEPRINTS = map(make_compat_blueprint, (misc, user, oauth, rooms, category, category_mgmt, event_display,
                                                event_creation, event_mgmt, files, admin, rooms_admin))


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
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['SESSION_COOKIE_NAME'] = 'indico_session'
    app.config['PERMANENT_SESSION_LIFETIME'] = cfg.getSessionLifetime()
    app.config['INDICO_SESSION_PERMANENT'] = cfg.getSessionLifetime() > 0
    app.config['INDICO_HTDOCS'] = cfg.getHtdocsDir()
    app.config['INDICO_COMPAT_ROUTES'] = cfg.getRouteOldUrls()
    if set_path:
        base = url_parse(cfg.getBaseURL())
        app.config['SERVER_NAME'] = base.netloc
        if base.path:
            app.config['APPLICATION_ROOT'] = base.path
    app.config['WTF_CSRF_ENABLED'] = False  # for forms of room booking
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


def setup_jinja(app):
    config = Config.getInstance()
    # Unicode hack
    app.jinja_env.add_extension(EnsureUnicodeExtension)
    app.add_template_filter(EnsureUnicodeExtension.ensure_unicode)
    # Global functions
    app.add_template_global(url_for)
    app.add_template_global(url_rule_to_js)
    app.add_template_global(IndicoConfigWrapper(config), 'indico_config')
    app.add_template_global(config.getSystemIconURL, 'system_icon')
    # Filters (indico functions returning UTF8)
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_date))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_time))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_datetime))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_human_date))
    app.add_template_filter(EnsureUnicodeExtension.wrap_func(date_time_util.format_timedelta))
    # Filters (new ones returning unicode)
    app.add_template_filter(underline)
    # i18n
    app.jinja_env.add_extension('jinja2.ext.i18n')
    app.jinja_env.install_gettext_callables(gettext, ngettext, True)
    # webassets
    app.jinja_env.add_extension('webassets.ext.jinja2.AssetsExtension')
    app.jinja_env.assets_environment = core_env


ASSETS_REGISTERED = False
def setup_assets():
    global ASSETS_REGISTERED
    if ASSETS_REGISTERED:
        # Avoid errors when forking after creating an app (e.g. in scheduler tests)
        return
    ASSETS_REGISTERED = True
    register_all_js(core_env)
    register_all_css(core_env, Config.getInstance().getCssStylesheetName())


def configure_db(app):
    cfg = Config.getInstance()
    db_uri = cfg.getSQLAlchemyDatabaseURI()

    if db_uri is None:
        raise Exception("No proper SQLAlchemy store has been configured."
                        " Please edit your indico.conf")

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

    # DB options
    app.config['SQLALCHEMY_ECHO'] = cfg.getSQLAlchemyEcho()
    app.config['SQLALCHEMY_RECORD_QUERIES'] = cfg.getSQLAlchemyRecordQueries()
    app.config['SQLALCHEMY_POOL_SIZE'] = cfg.getSQLAlchemyPoolSize()
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = cfg.getSQLAlchemyPoolTimeout()
    app.config['SQLALCHEMY_POOL_RECYCLE'] = cfg.getSQLAlchemyPoolRecycle()
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = cfg.getSQLAlchemyMaxOverflow()
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False

    db.init_app(app)
    apply_db_loggers(app.debug)
    configure_mappers()  # Make sure all backrefs are set
    models_committed.connect(on_models_committed, app)


def extend_url_map(app):
    app.url_map.converters['list'] = ListConverter


def add_handlers(app):
    app.register_error_handler(404, handle_404)
    app.register_error_handler(Exception, handle_exception)


def add_blueprints(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


def add_compat_blueprints(app):
    for blueprint in COMPAT_BLUEPRINTS:
        app.register_blueprint(blueprint)


def add_plugin_blueprints(app):
    for blueprint in RHMapMemory()._blueprints:
        if not app.config['INDICO_COMPAT_ROUTES'] and blueprint.name.startswith('compat_'):
            continue
        app.register_blueprint(blueprint)


def handle_404(exception):
    try:
        if re.search(r'\.py(?:/\S+)?$', request.path):
            # While not dangerous per se, we never serve *.py files as static
            raise NotFound
        try:
            return send_from_directory(app.config['INDICO_HTDOCS'], request.path[1:], conditional=True)
        except UnicodeEncodeError:
            raise NotFound
    except NotFound:
        if exception.description == NotFound.description:
            # The default reason is too long and not localized
            msg = (_("Page not found"), _("The page you were looking for doesn't exist."))
        else:
            msg = (_("Page not found"), exception.description)
        return WErrorWSGI(msg).getHTML(), 404


def handle_exception(exception):
    Logger.get('wsgi').exception(exception.message or 'WSGI Exception')
    if app.debug:
        raise
    msg = (str(exception), _("An unexpected error ocurred."))
    return WErrorWSGI(msg).getHTML(), 500


def make_app(set_path=False, db_setup=True):
    # If you are reading this code and wonder how to access the app:
    # >>> from flask import current_app as app
    # This only works while inside an application context but you really shouldn't have any
    # reason to access it outside this method without being inside an application context.
    # When set_path is enabled, SERVER_NAME and APPLICATION_ROOT are set according to BaseURL
    # so URLs can be generated without an app context, e.g. in the indico shell
    if _app_ctx_stack.top:
        Logger.get('flask').warn('make_app({}) called within app context, using existing app'.format(set_path))
        return _app_ctx_stack.top.app
    app = IndicoFlask('indico', static_folder=None, template_folder='web/templates')
    fix_root_path(app)
    configure_app(app, set_path)
    setup_jinja(app)
    setup_assets()

    if db_setup:
        configure_db(app)

    extend_url_map(app)
    add_handlers(app)
    add_blueprints(app)
    if app.config['INDICO_COMPAT_ROUTES']:
        add_compat_blueprints(app)
    add_plugin_blueprints(app)
    return app
