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

import os

from flask import current_app, json, session, render_template, send_from_directory, Response
from werkzeug.exceptions import NotFound

from indico.core.config import Config
from indico.core.plugins import plugin_engine
from indico.modules.events.layout import theme_settings
from indico.modules.users.util import serialize_user
from indico.util.caching import make_hashable
from indico.util.i18n import po_to_json
from indico.util.string import crc32
from indico.web.assets.util import get_asset_path
from indico.web.assets.vars_js import generate_global_file
from indico.web.flask.util import send_file
from indico.web.flask.wrappers import IndicoBlueprint


assets_blueprint = IndicoBlueprint('assets', __name__, url_prefix='/assets')
assets_blueprint.add_url_rule('!/images/<path:filename>', 'image', build_only=True)


@assets_blueprint.route('/js-vars/global.js')
def js_vars_global():
    """
    Provides a JS file with global definitions (all users)
    Useful for server-wide config options, URLs, etc...
    """
    config = Config.getInstance()
    config_hash = crc32(repr(make_hashable(sorted(config._configVars.items()))))
    cache_file = os.path.join(config.getCacheDir(), 'assets_global_{}.js'.format(config_hash))

    if not os.path.exists(cache_file):
        data = generate_global_file(config)
        with open(cache_file, 'wb') as f:
            f.write(data)

    return send_file('global.js', cache_file,
                     mimetype='application/x-javascript', no_cache=False, conditional=True)


@assets_blueprint.route('/js-vars/user.js')
def js_vars_user():
    """
    Provides a JS file with user-specific definitions
    Useful for favorites, settings etc.
    """
    user = session.user
    if user is None:
        user_vars = {}
    else:
        user_vars = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'favorite_users': {u.id: serialize_user(u) for u in user.favorite_users}
        }
    data = render_template('assets/vars_user.js', user_vars=user_vars, user=user)
    return Response(data, mimetype='application/x-javascript')


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
    plugin_key = ','.join(sorted(plugin_engine.get_active_plugins()))
    cache_file = os.path.join(config.getCacheDir(), 'assets_i18n_{}_{}.js'.format(locale_name, crc32(plugin_key)))

    if not os.path.exists(cache_file):
        i18n_data = locale_data(root_path, locale_name, 'indico')
        if not i18n_data:
            # Dummy data, not having the indico domain would cause lots of failures
            i18n_data = {'indico': {'': {'domain': 'indico',
                                         'lang': locale_name}}}

        for pid, plugin in plugin_engine.get_active_plugins().iteritems():
            data = {}
            if plugin.translation_path:
                data = locale_data(plugin.translation_path, locale_name, pid)
            if not data:
                # Dummy entry so we can still load the domain
                data = {pid: {'': {'domain': pid,
                                   'lang': locale_name}}}
            i18n_data.update(data)

        with open(cache_file, 'wb') as f:
            f.write("window.TRANSLATIONS = {};".format(json.dumps(i18n_data)))

    return send_file('{}.js'.format(locale_name), cache_file, mimetype='application/x-javascript',
                     no_cache=False, conditional=True)


@assets_blueprint.route('!/static/assets/core/<path:path>')
@assets_blueprint.route('!/static/assets/plugin-<plugin>/<path:path>')
@assets_blueprint.route('!/static/assets/theme-<theme>/<path:path>')
def static_asset(path, plugin=None, theme=None):
    # Ensure there's no weird stuff in the plugin/theme name
    if plugin and not plugin_engine.get_plugin(plugin):
        raise NotFound
    elif theme and theme not in theme_settings.themes:
        raise NotFound
    return send_from_directory(Config.getInstance().getAssetsDir(), get_asset_path(path, plugin=plugin, theme=theme))


@assets_blueprint.route('!/static/custom/<path:filename>', endpoint='custom')
def static_custom(filename):
    customization_dir = Config.getInstance().getCustomizationDir()
    if not customization_dir:
        raise NotFound
    customization_dir = os.path.join(customization_dir, 'static')
    return send_from_directory(customization_dir, filename)
