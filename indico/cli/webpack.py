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

import click
from flask import current_app, json
from flask.helpers import get_root_path
from flask_webpackext import current_webpack

from indico.core.plugins import plugin_engine
from indico.core.webpack import get_webpack_config
from indico.cli.core import cli_group
from indico.modules.events.layout import theme_settings


def _generate_webpack_config(plugin):
    url_base_path = current_app.config['APPLICATION_ROOT'] or '/'
    static_path = os.path.join(plugin.root_path, 'static')
    static_url = os.path.join('{}/static/plugins/{}'.format(url_base_path, plugin.name))

    return {
        'indico': get_webpack_config(current_app),
        'build': {
            'debug': current_app.debug,
            'indicoRootPath': os.path.dirname(get_root_path('indico')),
            'clientPath': os.path.join(current_app.root_path, 'web', 'client'),
            'rootPath': plugin.root_path,
            'staticPath': static_path,
            'staticURL': static_url,
            'distPath': os.path.join(static_path, 'dist'),
            'distURL': os.path.join(static_url, 'dist')
        },
        # include themes that belong to this plugin
        'themes': {key: theme for key, theme in theme_settings.themes.viewitems()
                   if theme.pop('plugin', '') == plugin}
    }


def _webpack_build_plugin(project, plugin_name, watch=False):
    plugin = plugin_engine.get_plugin(plugin_name)
    plugin_path = os.path.dirname(plugin.root_path)
    webpack_config = os.path.join(plugin_path, 'webpack.config.js')

    with open(os.path.join(plugin_path, 'config.json'), 'w') as f:
        json.dump(_generate_webpack_config(plugin), f)

    # set NODE_PATH to Indico's node_modules
    os.environ['NODE_PATH'] = os.path.normpath(os.path.join(current_app.root_path, '..', 'node_modules'))
    project.run('watch' if watch else 'build', '--', '--config={}'.format(webpack_config))


def _generate_plugin_config(plugin):
    return {
        'indico_base_path': os.path.dirname(get_root_path('indico'))
    }


@cli_group()
@click.option('--plugin', metavar='PLUGIN', help='Execute the command for the given plugin')
@click.pass_context
def cli(ctx, plugin=None):
    pass


@cli.command()
@click.pass_context
def build(ctx):
    """Build Webpack bundles"""
    plugin = ctx.parent.params['plugin']
    if plugin:
        _webpack_build_plugin(current_webpack.project, plugin)
    else:
        current_webpack.project.build()


@cli.command()
@click.pass_context
def watch(ctx):
    """Start up Webpack in --watch mode"""
    plugin = ctx.parent.params['plugin']
    if plugin:
        _webpack_build_plugin(current_webpack.project, plugin, watch=True)
    else:
        current_webpack.project.run('watch')
