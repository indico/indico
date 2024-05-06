# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from pathlib import Path

from flask import Response, current_app, redirect, request, send_from_directory
from werkzeug.exceptions import NotFound

import indico
from indico.core.config import config
from indico.core.plugins import plugin_engine
from indico.util.i18n import get_all_locales
from indico.web.assets.vars_js import generate_global_file, generate_i18n_file, generate_user_file
from indico.web.flask.util import send_file, url_for
from indico.web.flask.wrappers import IndicoBlueprint


assets_blueprint = IndicoBlueprint('assets', __name__, url_prefix='/assets')

assets_blueprint.add_url_rule('!/css/<path:filename>', 'css', build_only=True)
assets_blueprint.add_url_rule('!/images/<path:filename>', 'image', build_only=True)
assets_blueprint.add_url_rule('!/fonts/<path:filename>', 'fonts', build_only=True)
assets_blueprint.add_url_rule('!/dist/<path:filename>', 'dist', build_only=True)


@assets_blueprint.route('!/<any(css,dist,images,fonts):folder>/<path:filename>.<fileext>')
@assets_blueprint.route('!/<any(images,fonts):folder>/<path:filename>__v<version>.<fileext>')
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
    cache_file = Path(config.CACHE_DIR) / f'assets_global_{indico.__version__}_{config.hash}.js'

    if config.DEBUG or not cache_file.exists():
        data = generate_global_file()
        cache_file.write_text(data)

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
    # Ensure we have a valid locale. en_GB is our source locale and thus always considered
    # valid, even if it doesn't exist (dev setup where the user did not compile any locales)
    # since otherwise we'd have no valid locales at all and get a redirect loop
    all_locales = get_all_locales()
    if locale_name not in all_locales and locale_name != 'en_GB':
        fallback = config.DEFAULT_LOCALE if config.DEFAULT_LOCALE in all_locales else 'en_GB'
        return redirect(url_for(request.endpoint, locale_name=fallback))

    react_suffix = '-react' if react else ''
    try:
        cache_file = (
            Path(config.CACHE_DIR) / f'assets_i18n_{locale_name}{react_suffix}_{indico.__version__}_{config.hash}.js'
        )
    except UnicodeEncodeError:
        raise NotFound

    if config.DEBUG or not cache_file.exists():
        i18n_data = generate_i18n_file(locale_name, react=react)
        if i18n_data is None:
            raise NotFound
        cache_file.write_text('window.{} = {};'.format('REACT_TRANSLATIONS' if react else 'TRANSLATIONS', i18n_data))

    return send_file(f'{locale_name}{react_suffix}.js', cache_file, mimetype='application/javascript',
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
    return redirect(config.FAVICON_URL or url_for('.image', filename='indico.ico'))


@assets_blueprint.route('/avatar/<name>.svg')
@assets_blueprint.route('/avatar/blank.svg')
def avatar(name=None):
    from indico.modules.users.util import send_default_avatar
    return send_default_avatar(name)
