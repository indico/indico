# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from flask import Response, current_app, redirect, send_from_directory
from werkzeug.exceptions import NotFound

import indico
from indico.core.config import config
from indico.core.plugins import plugin_engine
from indico.web.assets.vars_js import generate_global_file, generate_i18n_file, generate_user_file
from indico.web.flask.util import send_file, url_for
from indico.web.flask.wrappers import IndicoBlueprint


assets_blueprint = IndicoBlueprint('assets', __name__, url_prefix='/assets')

assets_blueprint.add_url_rule('!/css/<path:filename>', 'css', build_only=True)
assets_blueprint.add_url_rule('!/images/<path:filename>', 'image', build_only=True)
assets_blueprint.add_url_rule('!/fonts/<path:filename>', 'fonts', build_only=True)
assets_blueprint.add_url_rule('!/dist/<path:filename>', 'dist', build_only=True)


@assets_blueprint.route('!/<any(images,fonts):folder>/<path:filename>__v<version>.<fileext>')
@assets_blueprint.route('!/<any(css,dist,images,fonts):folder>/<path:filename>.<fileext>')
def folder_file(folder, filename, fileext, version=None):
    assets_dir = os.path.join(current_app.root_path, 'web', 'static')
    return send_from_directory(assets_dir, os.path.join(folder, filename + '.' + fileext))


@assets_blueprint.route('!/static/plugins/<plugin>/<path:filename>__v<version>.<fileext>')
@assets_blueprint.route('!/static/plugins/<plugin>/<path:filename>.<fileext>')
def plugin_file(plugin, filename, fileext, version=None):
    plugin = plugin_engine.get_plugin(plugin)
    if not plugin:
        raise NotFound
    assets_dir = os.path.join(plugin.root_path, 'static')
    return send_from_directory(assets_dir, filename + '.' + fileext)


@assets_blueprint.route('!/<filename>')
def root(filename):
    assets_dir = os.path.join(current_app.root_path, 'web', 'static')
    return send_from_directory(assets_dir, filename)


@assets_blueprint.route('/js-vars/global.js')
def js_vars_global():
    """Provide a JS file with global definitions (all users).

    Useful for server-wide config options, URLs, etc...
    """
    cache_file = os.path.join(config.CACHE_DIR, 'assets_global_{}_{}.js'.format(indico.__version__, config.hash))

    if config.DEBUG or not os.path.exists(cache_file):
        data = generate_global_file()
        with open(cache_file, 'wb') as f:
            f.write(data)

    return send_file('global.js', cache_file, mimetype='application/javascript', conditional=True)


@assets_blueprint.route('/js-vars/user.js')
def js_vars_user():
    """Provide a JS file with user-specific definitions.

    Useful for favorites, settings etc.
    """
    return Response(generate_user_file(), mimetype='application/javascript')


@assets_blueprint.route('/i18n/<locale_name>.js')
def i18n_locale(locale_name):
    return _get_i18n_locale(locale_name)


@assets_blueprint.route('/i18n/<locale_name>-react.js')
def i18n_locale_react(locale_name):
    return _get_i18n_locale(locale_name, react=True)


def _get_i18n_locale(locale_name, react=False):
    """Retrieve a locale in a Jed-compatible format."""

    react_suffix = '-react' if react else ''

    try:
        cache_file = os.path.join(config.CACHE_DIR, 'assets_i18n_{}{}_{}_{}.js'.format(
            locale_name, react_suffix, indico.__version__, config.hash))
    except UnicodeEncodeError:
        raise NotFound

    if config.DEBUG or not os.path.exists(cache_file):
        i18n_data = generate_i18n_file(locale_name, react=react)
        if i18n_data is None:
            raise NotFound
        with open(cache_file, 'wb') as f:
            f.write("window.{} = {};".format('REACT_TRANSLATIONS' if react else 'TRANSLATIONS', i18n_data))

    return send_file('{}{}.js'.format(locale_name, react_suffix), cache_file, mimetype='application/javascript',
                     conditional=True)


@assets_blueprint.route('!/static/custom/<any(css,js):folder>/<path:filename>', endpoint='custom')
@assets_blueprint.route('!/static/custom/files/<path:filename>', endpoint='custom', defaults={'folder': 'files'})
def static_custom(folder, filename):
    customization_dir = config.CUSTOMIZATION_DIR
    if not customization_dir:
        raise NotFound
    return send_from_directory(os.path.join(customization_dir, folder), filename)


@assets_blueprint.route('!/favicon.ico')
def favicon():
    return redirect(url_for('.image', filename='indico.ico'))
