# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import binascii
import os

from indico.core.config import Config
from indico.util.caching import make_hashable
from indico.web.flask.util import send_file
from indico.web.flask.wrappers import IndicoBlueprint

from indico.web.assets.vars_js import generate_global_file


assets_blueprint = IndicoBlueprint('assets', __name__, url_prefix='/assets')


@assets_blueprint.route('/js_vars/global.js')
def js_vars_global():
    """
    Provides a JS file with global definitions (all users)
    Useful for server-wide config options, URLs, etc...
    """
    config = Config.getInstance()
    config_hash = binascii.crc32(repr(make_hashable(sorted(config._configVars.items()))))
    cache_file = os.path.join(config.getTempDir(), 'vars_global_{}.js.tmp'.format(config_hash))

    if not os.access(cache_file, os.R_OK):
        if not generate_global_file(cache_file, config):
            return "Impossible to generate cache file", 400

    return send_file('vars.js', cache_file, mimetype='application/x-javascript', no_cache=False,
                     conditional=True)
