#!/usr/bin/env python
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

import json
import os
import subprocess
import sys

import click
import yaml
from setuptools import find_packages


def fail(message, *args, **kwargs):
    click.echo(click.style('Error: ' + message.format(*args), fg='red', bold=True), err=True)
    if 'verbose_msg' in kwargs:
        click.echo(kwargs['verbose_msg'], err=True)
    sys.exit(1)


def warn(message, *args):
    click.echo(click.style(message.format(*args), fg='yellow', bold=True), err=True)


def info(message, *args):
    click.echo(click.style(message.format(*args), fg='green', bold=True), err=True)


def step(message, *args):
    click.echo(click.style(message.format(*args), fg='white', bold=True), err=True)


def _get_webpack_config(url_root='/', debug=False):
    with open('indico/modules/events/themes.yaml') as f:
        themes = yaml.safe_load(f.read())
    root_path = os.path.abspath('indico')
    return {
        'build': {
            'debug': debug,
            'clientPath': os.path.join(root_path, 'web', 'client'),
            'rootPath': root_path,
            'staticPath': os.path.join(root_path, 'web', 'static'),
            'staticURL': url_root.rstrip('/') + '/',
            'distPath': os.path.join(root_path, 'web', 'static', 'dist'),
            'distURL': os.path.join(url_root, 'dist/')
        },
        'themes': {key: {'stylesheet': theme['stylesheet'], 'print_stylesheet': theme.get('print_stylesheet')}
                   for key, theme in themes['definitions'].viewitems()
                   if set(theme) & {'stylesheet', 'print_stylesheet'}}
    }


def _get_plugin_webpack_config(plugin_dir, url_root='/', debug=False):
    core_config = _get_webpack_config(url_root, debug)
    packages = find_packages(plugin_dir)
    assert len(packages) == 1
    plugin_root_path = os.path.join(plugin_dir, packages[0])
    plugin_name = packages[0].replace('indico_', '')  # XXX: find a better solution for this
    return {
        'isPlugin': True,
        'indico': {
            'build': core_config['build']
        },
        'build': {
            'debug': debug,
            'indicoSourcePath': os.path.abspath('.'),
            'clientPath': os.path.join(plugin_root_path, 'client'),
            'rootPath': plugin_root_path,
            'staticPath': os.path.join(plugin_root_path, 'static'),
            'staticURL': os.path.join(url_root, 'static', 'plugins', plugin_name) + '/',
            'distPath': os.path.join(plugin_root_path, 'static', 'dist'),
            'distURL': os.path.join(url_root, 'static', 'plugins', plugin_name, 'dist/')
        },
        # TODO: themes
    }


def _get_webpack_args(debug, watch):
    args = []
    if debug:
        args.append('--env.NODE_ENV=development')
    else:
        args += ['-p', '--env.NODE_ENV=production']
    if watch:
        args.append('--watch')
    return args


@click.group()
def cli():
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))


@cli.command()
@click.option('--debug', is_flag=True, default=False, help="Build in debug mode")
@click.option('--watch', is_flag=True, default=False, help="Run the watcher to rebuild on changes")
@click.option('--url-root', default='/', metavar='PATH', help='URL root from which the assets are loaded. Defaults to '
                                                              '/ and should usually not be changed')
def build(debug, watch, url_root):
    """Run webpack to build assets"""
    webpack_config_file = 'webpack-build-config.json'
    webpack_config = _get_webpack_config(url_root, debug)
    with open(webpack_config_file, 'w') as f:
        json.dump(webpack_config, f, indent=2, sort_keys=True)
    args = _get_webpack_args(debug, watch)
    try:
        subprocess.check_call(['npx', 'webpack'] + args)
    except subprocess.CalledProcessError:
        fail('running webpack failed')
    # finally:
    #     os.unlink(webpack_config_file)


def _validate_plugin_dir(ctx, param, value):
    if not os.path.exists(os.path.join(value, 'setup.py')):
        raise click.BadParameter('no setup.py found in {}'.format(value))
    if not os.path.exists(os.path.join(value, 'webpack.config.js')):
        raise click.BadParameter('no webpack.config.js found in {}'.format(value))
    return value


@cli.command()
@click.argument('plugin_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                callback=_validate_plugin_dir)
@click.option('--debug', is_flag=True, default=False, help="Build in debug mode")
@click.option('--watch', is_flag=True, default=False, help="Run the watcher to rebuild on changes")
@click.option('--url-root', default='/', metavar='PATH', help='URL root from which the assets are loaded. Defaults to '
                                                              '/ and should usually not be changed')
def build_plugin(plugin_dir, debug, watch, url_root):
    """Run webpack to build plugin assets"""
    webpack_config_file = os.path.join(plugin_dir, 'webpack-build-config.json')
    webpack_config = _get_plugin_webpack_config(plugin_dir, url_root, debug)
    with open(webpack_config_file, 'w') as f:
        json.dump(webpack_config, f, indent=2, sort_keys=True)
    args = _get_webpack_args(debug, watch)
    args += ['--config', '{}/webpack.config.js'.format(plugin_dir)]
    os.environ['NODE_PATH'] = os.path.abspath('node_modules')
    try:
        subprocess.check_call(['npx', 'webpack'] + args)
    except subprocess.CalledProcessError:
        fail('running webpack failed')
    # finally:
    #     os.unlink(webpack_config_file)


if __name__ == '__main__':
    cli()
