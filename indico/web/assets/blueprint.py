# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import Response, current_app, redirect, send_from_directory
from werkzeug.exceptions import NotFound

from indico.core.config import config
from indico.core.plugins import plugin_engine
from indico.modules.events.layout import theme_settings
from indico.util.string import crc32
from indico.web.assets.util import get_asset_path
from indico.web.assets.vars_js import generate_global_file, generate_i18n_file, generate_user_file
from indico.web.flask.util import send_file, url_for
from indico.web.flask.wrappers import IndicoBlueprint


assets_blueprint = IndicoBlueprint('assets', __name__, url_prefix='/assets')

assets_blueprint.add_url_rule('!/css/<path:filename>', 'css', build_only=True)
assets_blueprint.add_url_rule('!/images/<path:filename>', 'image', build_only=True)
assets_blueprint.add_url_rule('!/fonts/<path:filename>', 'fonts', build_only=True)
assets_blueprint.add_url_rule('!/dist/<path:filename>', 'dist', build_only=True)


@assets_blueprint.route('!/<any(images,fonts):folder>/<path:filename>__v<version>.<fileext>')
@assets_blueprint.route('!/<any(images,fonts):folder>/<path:filename>.<fileext>')
@assets_blueprint.route('!/<any(css,dist,images,fonts):folder>/<path:filename>.<fileext>')
def folder_file(folder, filename, fileext, version=None):
    assets_dir = os.path.join(current_app.root_path, 'web', 'static')
    return send_from_directory(assets_dir, os.path.join(folder, filename + '.' + fileext))


@assets_blueprint.route('!/<filename>')
def root(filename):
    assets_dir = os.path.join(current_app.root_path, 'web', 'static')
    return send_from_directory(assets_dir, filename)


@assets_blueprint.route('/js-vars/global.js')
def js_vars_global():
    """
    Provides a JS file with global definitions (all users)
    Useful for server-wide config options, URLs, etc...
    """
    cache_file = os.path.join(config.CACHE_DIR, 'assets_global_{}.js'.format(config.hash))

    if not os.path.exists(cache_file):
        data = generate_global_file()
        with open(cache_file, 'wb') as f:
            f.write(data)

    return send_file('global.js', cache_file, mimetype='application/javascript', no_cache=False, conditional=True)


@assets_blueprint.route('/js-vars/user.js')
def js_vars_user():
    """
    Provides a JS file with user-specific definitions
    Useful for favorites, settings etc.
    """
    return Response(generate_user_file(), mimetype='application/javascript')


@assets_blueprint.route('/i18n/<locale_name>.js')
def i18n_locale(locale_name):
    """
    Retrieve a locale in a Jed-compatible format
    """

    plugin_key = ','.join(sorted(plugin_engine.get_active_plugins()))
    cache_file = os.path.join(config.CACHE_DIR, 'assets_i18n_{}_{}.js'.format(locale_name, crc32(plugin_key)))

    if not os.path.exists(cache_file):
        i18n_data = generate_i18n_file(locale_name)
        with open(cache_file, 'wb') as f:
            f.write("window.TRANSLATIONS = {};".format(i18n_data))

    return send_file('{}.js'.format(locale_name), cache_file, mimetype='application/javascript',
                     no_cache=False, conditional=True)


@assets_blueprint.route('!/static/assets/core/<path:path>')
@assets_blueprint.route('!/static/assets/theme-<theme>/<path:path>')
def static_asset(path, theme=None):
    # Ensure there's no weird stuff in the plugin/theme name
    if theme and theme not in theme_settings.themes:
        raise NotFound
    return send_from_directory(config.ASSETS_DIR, get_asset_path(path, theme=theme))


@assets_blueprint.route('!/static/custom/<path:filename>', endpoint='custom')
def static_custom(filename):
    customization_dir = config.CUSTOMIZATION_DIR
    if not customization_dir:
        raise NotFound
    customization_dir = os.path.join(customization_dir, 'static')
    return send_from_directory(customization_dir, filename)


@assets_blueprint.route('!/favicon.ico')
def favicon():
    return redirect(url_for('.image', filename='indico.ico'))
