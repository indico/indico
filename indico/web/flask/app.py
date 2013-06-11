# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from flask import redirect, url_for, send_from_directory, request
from flask import current_app as app
from functools import partial
from werkzeug.exceptions import NotFound

from MaKaC.common import Config
from MaKaC.common.db import DBMgr
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.logger import Logger
from MaKaC.i18n import _
from MaKaC.webinterface.pages.error import WErrorWSGI
from MaKaC.services.interface.rpc.json import process as jsonrpc_handler

from indico.web.flask.util import create_modpython_rules, create_plugin_rules, shorturl_handler, XAccelMiddleware
from indico.web.flask.wrappers import IndicoFlask
from indico.web.http_api.handlers import handler as api_handler


def fix_root_path(app):
    """Fix the app's root path when using namespace packages.

    Flask's get_root_path is not reliable in this case so we derive it from
    __name__ and __file__ instead."""

    # __name__:       'indico.web.flask.app'
    # __file__:  '..../indico/web/flask/app.py'
    # For each dot in the module name we go up one path segment
    up_segments = ['..'] * __name__.count('.')
    app.root_path = os.path.normpath(os.path.join(__file__, *up_segments))


def configure_app(app):
    cfg = Config.getInstance()
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['SESSION_COOKIE_NAME'] = 'indico_session'
    app.config['PERMANENT_SESSION_LIFETIME'] = cfg.getSessionLifetime()
    app.config['INDICO_SESSION_PERMANENT'] = cfg.getSessionLifetime() > 0
    app.config['HTDOCS'] = cfg.getHtdocsDir()
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


def extend_url_map(app):
    # Doesn't do anything currently. But if you ever need to add a custom url converter register
    # it in here and put its class definition into indicoweb.flask.util
    pass


def add_handlers(app):
    app.add_url_rule('/', view_func=lambda: redirect(url_for('mp-index-index')))
    app.add_url_rule('/services/json-rpc', view_func=jsonrpc_handler, endpoint='services', methods=('POST',))
    app.add_url_rule('/export/<path:path>', view_func=partial(api_handler, '/export'), endpoint='export')
    app.add_url_rule('/api/<path:path>', view_func=partial(api_handler, '/api'), endpoint='api', methods=('POST',))
    # TODO: Remove the shorturl route and handle them in the main /event/ and /categ/ handlers
    app.add_url_rule('/<any(event, categ):what>/<tag>', view_func=shorturl_handler, endpoint='shorturl')
    app.register_error_handler(404, handle_404)
    app.register_error_handler(Exception, handle_exception)


def handle_404(exception):
    try:
        return send_from_directory(app.config['HTDOCS'], request.path[1:], conditional=True)
    except NotFound:
        msg = (_("Page not found"), _("The page you were looking for doesn't exist."))
        return WErrorWSGI(msg).getHTML(), 404


def handle_exception(exception):
    Logger.get('wsgi').exception(exception.message or 'WSGI Exception')
    with DBMgr.getInstance().global_connection():
        if HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive():
            raise
    msg = (str(exception), _("An unexpected error ocurred."))
    return WErrorWSGI(msg).getHTML(), 500


def make_app():
    # If you are reading this code and wonder how to access the app:
    # >>> from flask import current_app as app
    # This only works while inside an application context but you really shouldn't have any
    # reason to access it outside this method without being inside an application context.
    app = IndicoFlask('indico', static_folder=None)
    fix_root_path(app)
    configure_app(app)
    extend_url_map(app)
    add_handlers(app)
    create_modpython_rules(app)
    create_modpython_rules(app, 'scripts')
    create_plugin_rules(app)
    return app
