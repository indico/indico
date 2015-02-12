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

from flask import current_app, json
from werkzeug.exceptions import NotFound

from indico.core.config import Config
from indico.core.plugins import plugin_engine
from indico.util.caching import make_hashable
from indico.util.i18n import po_to_json
from indico.web.flask.util import send_file
from indico.web.flask.wrappers import IndicoBlueprint
from indico.web.assets.vars_js import generate_global_file

assets_blueprint = IndicoBlueprint('assets', __name__, url_prefix='/assets')


@assets_blueprint.route('/js-vars/global.js')
def js_vars_global():
    """
    Provides a JS file with global definitions (all users)
    Useful for server-wide config options, URLs, etc...
    """
    config = Config.getInstance()
    config_hash = binascii.crc32(repr(make_hashable(sorted(config._configVars.items()))))
    cache_file = os.path.join(config.getXMLCacheDir(), 'assets_global_{}.js'.format(config_hash))

    if not os.path.exists(cache_file):
        with open(cache_file, 'wb') as f:
            f.write(generate_global_file(config))

    return send_file('vars.js', cache_file,
                     mimetype='application/x-javascript', no_cache=False, conditional=True)


def locale_data(path, name, domain):
    po_file = os.path.join(path, name, 'LC_MESSAGES', 'messages-js.po')
    return po_to_json(po_file, domain=domain, locale=name) if os.access(po_file, os.R_OK) else {}


@assets_blueprint.route('/i18n/<locale_name>.js')
def i18n_locale(locale_name):
    """
    Retrieve a locale in a Jed-compatible format
    """
    config = Config.getInstance()
    root_path = os.path.join(current_app.root_path, 'translations')
    cache_file = os.path.join(config.getXMLCacheDir(), 'assets_i18n_{}.js'.format(locale_name))

    if not os.path.exists(cache_file):
        i18n_data = {}
        i18n_data.update(locale_data(root_path, locale_name, 'indico'))

        for pid, plugin in plugin_engine.get_active_plugins().iteritems():
            if plugin.translation_path:
                i18n_data.update(locale_data(plugin.translation_path, locale_name, pid))

        if i18n_data:
            with open(cache_file, 'wb') as f:
                f.write("window.TRANSLATIONS = {};".format(json.dumps(i18n_data)))
        else:
            raise NotFound("Translation for language '{}' not found".format(locale_name))

    return send_file('{}.js'.format(locale_name), cache_file, mimetype='application/x-javascript',
                     no_cache=False, conditional=True)
