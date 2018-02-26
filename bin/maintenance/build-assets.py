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

import errno
import json
import os
import re
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


def _get_webpack_build_config(url_root='/'):
    with open('indico/modules/events/themes.yaml') as f:
        themes = yaml.safe_load(f.read())
    root_path = os.path.abspath('indico')
    return {
        'build': {
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


def _get_plugin_bundle_config(plugin_dir):
    try:
        with open(os.path.join(plugin_dir, 'webpack-bundles.json')) as f:
            return json.load(f)
    except IOError as e:
        if e.errno == errno.ENOENT:
            return {}
        raise


def _parse_plugin_theme_yaml(plugin_yaml):
    # This is very similar to what ThemeSettingsProxy does
    with open('indico/modules/events/themes.yaml') as f:
        core_data = f.read()
    core_data = re.sub(r'^(\S+:)$', r'__core_\1', core_data, flags=re.MULTILINE)
    settings = {k: v
                for k, v in yaml.safe_load(core_data + '\n' + plugin_yaml).viewitems()
                if not k.startswith('__core_')}
    return {name: {'stylesheet': theme['stylesheet'], 'print_stylesheet': theme.get('print_stylesheet')}
            for name, theme in settings.get('definitions', {}).viewitems()
            if set(theme) & {'stylesheet', 'print_stylesheet'}}


def _get_plugin_themes(plugin_dir):
    bundle_config = _get_plugin_bundle_config(plugin_dir)
    try:
        theme_file = bundle_config['indicoTheme']
    except KeyError:
        return {}
    with open(os.path.join(plugin_dir, theme_file)) as f:
        return _parse_plugin_theme_yaml(f.read())


def _get_plugin_webpack_build_config(plugin_dir, url_root='/'):
    core_config = _get_webpack_build_config(url_root)
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
            'indicoSourcePath': os.path.abspath('.'),
            'clientPath': os.path.join(plugin_root_path, 'client'),
            'rootPath': plugin_root_path,
            'staticPath': os.path.join(plugin_root_path, 'static'),
            'staticURL': os.path.join(url_root, 'static', 'plugins', plugin_name) + '/',
            'distPath': os.path.join(plugin_root_path, 'static', 'dist'),
            'distURL': os.path.join(url_root, 'static', 'plugins', plugin_name, 'dist/')
        },
        'themes': _get_plugin_themes(plugin_dir),
    }


def _get_webpack_args(dev, watch):
    args = []
    if dev:
        args.append('--env.NODE_ENV=development')
    else:
        args += ['-p', '--env.NODE_ENV=production']
    if watch:
        args.append('--watch')
    return args


@click.group()
def cli():
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))


def _common_build_options(allow_watch=True):
    def decorator(fn):
        fn = click.option('--dev', is_flag=True, default=False, help="Build in dev mode")(fn)
        fn = click.option('--url-root', default='/', metavar='PATH',
                          help='URL root from which the assets are loaded. '
                               'Defaults to / and should usually not be changed')(fn)
        if allow_watch:
            fn = click.option('--watch', is_flag=True, default=False, help="Run the watcher to rebuild on changes")(fn)
        return fn
    return decorator


@cli.command()
@_common_build_options()
def build(dev, watch, url_root):
    """Run webpack to build assets"""
    webpack_build_config_file = 'webpack-build-config.json'
    webpack_build_config = _get_webpack_build_config(url_root)
    with open(webpack_build_config_file, 'w') as f:
        json.dump(webpack_build_config, f, indent=2, sort_keys=True)
    args = _get_webpack_args(dev, watch)
    try:
        subprocess.check_call(['npx', 'webpack'] + args)
    except subprocess.CalledProcessError:
        fail('running webpack failed')
    finally:
        if not dev:
            os.unlink(webpack_build_config_file)


def _validate_plugin_dir(ctx, param, value):
    if not os.path.exists(os.path.join(value, 'setup.py')):
        raise click.BadParameter('no setup.py found in {}'.format(value))
    if (not os.path.exists(os.path.join(value, 'webpack.config.js')) and
            not os.path.exists(os.path.join(value, 'webpack-bundles.json'))):
        raise click.BadParameter('no webpack.config.js or webpack-bundles.json found in {}'.format(value))
    return value


def _is_plugin_dir(path):
    try:
        _validate_plugin_dir(None, None, path)
    except click.BadParameter:
        return False
    else:
        return True


@cli.command()
@click.argument('plugin_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                callback=_validate_plugin_dir)
@_common_build_options()
def build_plugin(plugin_dir, dev, watch, url_root):
    """Run webpack to build plugin assets"""
    webpack_build_config_file = os.path.join(plugin_dir, 'webpack-build-config.json')
    webpack_build_config = _get_plugin_webpack_build_config(plugin_dir, url_root)
    with open(webpack_build_config_file, 'w') as f:
        json.dump(webpack_build_config, f, indent=2, sort_keys=True)
    webpack_config_file = '{}/webpack.config.js'.format(plugin_dir)
    if not os.path.exists(webpack_config_file):
        webpack_config_file = 'plugin.webpack.config.js'
    args = _get_webpack_args(dev, watch)
    args += ['--config', webpack_config_file]
    os.environ['NODE_PATH'] = os.path.abspath('node_modules')
    os.environ['INDICO_PLUGIN_ROOT'] = plugin_dir
    try:
        subprocess.check_call(['npx', 'webpack'] + args)
    except subprocess.CalledProcessError:
        fail('running webpack failed')
    finally:
        if not dev:
            os.unlink(webpack_build_config_file)


@cli.command()
@click.argument('plugins_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@_common_build_options(allow_watch=False)
@click.pass_context
def build_all_plugins(ctx, plugins_dir, dev, url_root):
    """Run webpack to build plugin assets"""
    plugins = sorted(d for d in os.listdir(plugins_dir) if _is_plugin_dir(os.path.join(plugins_dir, d)))
    for plugin in plugins:
        step('plugin: {}', plugin)
        ctx.invoke(build_plugin, plugin_dir=os.path.join(plugins_dir, plugin), dev=dev, watch=False, url_root=url_root)


if __name__ == '__main__':
    cli()
