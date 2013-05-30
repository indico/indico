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
from flask import redirect, url_for

from indico.web.flask.util import create_modpython_rules
from indico.web.flask.wrappers import IndicoFlask


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
    app = IndicoFlask('indico')
    fix_root_path(app)
    return app


app = make_app()
app.config['PROPAGATE_EXCEPTIONS'] = True
app.add_url_rule('/', view_func=lambda: redirect(url_for('mp-index-index')))
create_modpython_rules(app)
