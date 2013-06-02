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
from functools import partial

import os
from flask import redirect, url_for, send_from_directory, request
from werkzeug.exceptions import NotFound
from MaKaC.common.db import DBMgr
from MaKaC.common.info import HelperMaKaCInfo

from MaKaC.i18n import _
from MaKaC.webinterface.pages.error import WErrorWSGI
from MaKaC.services.interface.rpc.json import process as jsonrpc_handler

from indico.web.flask.util import create_modpython_rules
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


def make_app():
    app = IndicoFlask('indico', static_folder=None)
    fix_root_path(app)
    return app


def configure_app(app):
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['SESSION_COOKIE_NAME'] = 'indico_session'


def add_handlers(app):
    app.add_url_rule('/', view_func=lambda: redirect(url_for('mp-index-index')))
    app.add_url_rule('/services/json-rpc', view_func=jsonrpc_handler, endpoint='services', methods=('POST',))
    app.add_url_rule('/export/<path:path>', view_func=partial(api_handler, '/export'), endpoint='export')
    app.add_url_rule('/api/<path:path>', view_func=partial(api_handler, '/api'), endpoint='api', methods=('POST',))
    app.register_error_handler(404, handle_404)
    app.register_error_handler(Exception, handle_exception)


def handle_404(exception):
    folder = os.path.abspath(os.path.join(app.root_path, 'htdocs'))
    try:
        return send_from_directory(folder, request.path[1:])
    except NotFound:
        msg = (_("Page not found"), _("The page you were looking for doesn't exist."))
        return WErrorWSGI(msg).getHTML(), 404


def handle_exception(exception):
    with DBMgr.getInstance().global_connection():
        if HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive():
            raise
    msg = (str(exception), _("An unexpected error ocurred."))
    return WErrorWSGI(msg).getHTML(), 500


app = make_app()
configure_app(app)
add_handlers(app)
create_modpython_rules(app)