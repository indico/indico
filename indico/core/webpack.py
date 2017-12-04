# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask_webpackext import FlaskWebpackExt

from indico.modules.events.layout import theme_settings


webpack = FlaskWebpackExt()


def _get_webpack_config(app):
    static_url_path = os.path.join(app.config['APPLICATION_ROOT'] or '/', app.static_url_path)
    return {
        'build': {
            'debug': app.debug,
            'rootPath': app.root_path,
            'staticPath': app.static_folder,
            'staticURL': static_url_path,
            'distPath': app.config['WEBPACKEXT_PROJECT_DISTDIR'],
            'distURL': os.path.join(static_url_path, 'dist/')
        },
        'themes': theme_settings.themes
    }
