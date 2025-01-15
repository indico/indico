#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import errno
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import click
import yaml


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
    themes = yaml.safe_load(Path('indico/modules/events/themes.yaml').read_text())
    root_path = os.path.abspath('indico')
    return {
        'build': {
            'baseURLPath': url_root,
            'clientPath': os.path.join(root_path, 'web', 'client'),
            'rootPath': root_path,
            'urlMapPath': os.path.normpath(os.path.join(root_path, '..', 'url_map.json')),
            'staticPath': os.path.join(root_path, 'web', 'static'),
            'staticURL': url_root.rstrip('/') + '/',
            'distPath': os.path.join(root_path, 'web', 'static', 'dist'),
            'distURL': os.path.join(url_root, 'dist/')
        },
        'themes': {key: {'stylesheet': theme['stylesheet'], 'print_stylesheet': theme.get('print_stylesheet')}
                   for key, theme in themes['definitions'].items()
                   if set(theme) & {'stylesheet', 'print_stylesheet'}}
    }


def _get_plugin_bundle_config(plugin_dir):
    try:
        with open(os.path.join(plugin_dir, 'webpack-bundles.json')) as f:
            return json.load(f)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return {}
        raise


def _get_plugin_build_deps(plugin_dir):
    try:
        with open(os.path.join(plugin_dir, 'required-build-plugins.json')) as f:
            return json.load(f)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return []
        raise


def _parse_plugin_theme_yaml(plugin_yaml):
    # This is very similar to what ThemeSettingsProxy does
    core_data = Path('indico/modules/events/themes.yaml').read_text()
    core_data = re.sub(r'^(\S+:)$', r'__core_\1', core_data, flags=re.MULTILINE)
    settings = {k: v
                for k, v in yaml.safe_load(core_data + '\n' + plugin_yaml).items()
                if not k.startswith('__core_')}
    return {name: {'stylesheet': theme['stylesheet'], 'print_stylesheet': theme.get('print_stylesheet')}
            for name, theme in settings.get('definitions', {}).items()
            if set(theme) & {'stylesheet', 'print_stylesheet'}}


def _get_plugin_themes(plugin_dir):
    bundle_config = _get_plugin_bundle_config(plugin_dir)
    try:
        theme_file = bundle_config['indicoTheme']
    except KeyError:
        return {}
    data = Path(plugin_dir, theme_file).read_text()
    return _parse_plugin_theme_yaml(data)


def _get_plugin_webpack_build_config(plugin_dir: Path, url_root='/'):
    core_config = _get_webpack_build_config(url_root)
    packages = [x.parent.name for x in plugin_dir.glob('*/__init__.py')]
    assert len(packages) == 1
    plugin_root_path = os.path.join(plugin_dir, packages[0])
    plugin_name = packages[0].replace('indico_', '')  # XXX: find a better solution for this
    return {
        'isPlugin': True,
        'plugin': plugin_name,
        'indico': {
            'build': core_config['build']
        },
        'build': {
            'indicoSourcePath': os.path.abspath('.'),
            'clientPath': os.path.join(plugin_root_path, 'client'),
            'rootPath': plugin_root_path,
            'urlMapPath': os.path.join(plugin_dir, 'url_map.json'),
            'staticPath': os.path.join(plugin_root_path, 'static'),
            'staticURL': os.path.join(url_root, 'static', 'plugins', plugin_name) + '/',
            'distPath': os.path.join(plugin_root_path, 'static', 'dist'),
            'distURL': os.path.join(url_root, 'static', 'plugins', plugin_name, 'dist/')
        },
        'themes': _get_plugin_themes(plugin_dir),
    }


def _get_webpack_args(dev, watch):
    args = ['--profile', '--progress', '--mode', 'development' if dev else 'production']
    if watch:
        args.append('--watch')
    return args


@click.group()
def cli():
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))


def _common_build_options(allow_watch=True):
    def decorator(fn):
        fn = click.option('--dev', is_flag=True, default=False, help='Build in dev mode')(fn)
        fn = click.option('--clean/--no-clean', default=None,
                          help='Delete everything in dist. This is disabled by default for `--dev` builds.')(fn)
        fn = click.option('--url-root', default='/', metavar='PATH',
                          help='URL root from which the assets are loaded. '
                               'Defaults to / and should usually not be changed')(fn)
        if allow_watch:
            fn = click.option('--watch', is_flag=True, default=False, help='Run the watcher to rebuild on changes')(fn)
        return fn
    return decorator


def _clean(webpack_build_config, plugin_dir=None):
    dist_path = webpack_build_config['build']['distPath']
    if os.path.exists(dist_path):
        warn('deleting ' + os.path.relpath(dist_path, plugin_dir or os.curdir))
        shutil.rmtree(dist_path)


@cli.command('indico', short_help='Builds assets of Indico.')
@_common_build_options()
def build_indico(dev, clean, watch, url_root):
    """Run webpack to build assets."""
    clean = clean or (clean is None and not dev)
    webpack_build_config_file = 'webpack-build-config.json'
    webpack_build_config = _get_webpack_build_config(url_root)
    with open(webpack_build_config_file, 'w') as f:
        json.dump(webpack_build_config, f, indent=2, sort_keys=True)
    if clean:
        _clean(webpack_build_config)
    force_url_map = ['--force'] if clean or not dev else []
    url_map_path = webpack_build_config['build']['urlMapPath']
    subprocess.check_call([sys.executable, 'bin/maintenance/dump_url_map.py', '--output', url_map_path, *force_url_map])
    args = _get_webpack_args(dev, watch)
    try:
        subprocess.check_call(['npx', 'webpack', *args])
    except subprocess.CalledProcessError:
        fail('running webpack failed')
    finally:
        if not dev:
            os.unlink(webpack_build_config_file)


def _validate_plugin_dir(ctx, param, value):
    if not os.path.exists(os.path.join(value, 'pyproject.toml')):
        raise click.BadParameter(f'no pyproject.toml found in {value}')
    if (not os.path.exists(os.path.join(value, 'webpack.config.js')) and
            not os.path.exists(os.path.join(value, 'webpack-bundles.json'))):
        raise click.BadParameter(f'no webpack.config.js or webpack-bundles.json found in {value}')
    return value


def _is_plugin_dir(path):
    try:
        _validate_plugin_dir(None, None, path)
    except click.BadParameter:
        return False
    else:
        return True


@contextmanager
def _chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


@cli.command('plugin', short_help='Builds assets of a plugin.')
@click.argument('plugin_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
                callback=_validate_plugin_dir)
@_common_build_options()
def build_plugin(plugin_dir: Path, dev, clean, watch, url_root):
    """Run webpack to build plugin assets."""
    clean = clean or (clean is None and not dev)
    webpack_build_config_file = plugin_dir / 'webpack-build-config.json'
    webpack_build_config = _get_plugin_webpack_build_config(plugin_dir, url_root)
    webpack_build_config_file.write_text(json.dumps(webpack_build_config, indent=2, sort_keys=True))
    if clean:
        _clean(webpack_build_config, plugin_dir)
    force_url_map = ['--force'] if clean or not dev else []
    url_map_path = webpack_build_config['build']['urlMapPath']
    dump_plugin_args = ['--plugin', webpack_build_config['plugin']]
    for name in _get_plugin_build_deps(plugin_dir):
        dump_plugin_args += ['--plugin', name]
    subprocess.check_call([sys.executable, 'bin/maintenance/dump_url_map.py', '--output', url_map_path,
                           *dump_plugin_args, *force_url_map])
    webpack_config_file = plugin_dir / 'webpack.config.mjs'
    if not webpack_config_file.exists():
        webpack_config_file = 'plugin.webpack.config.mjs'
    if (plugin_dir / 'package.json').exists():
        with _chdir(plugin_dir):
            try:
                subprocess.check_call(['npm', 'install', '--quiet'])
            except subprocess.CalledProcessError:
                fail('running npm failed')
    args = _get_webpack_args(dev, watch)
    args += ['--config', webpack_config_file]
    os.environ['NODE_PATH'] = os.path.abspath('node_modules')
    os.environ['INDICO_PLUGIN_ROOT'] = str(plugin_dir)
    try:
        subprocess.check_call(['npx', 'webpack', *args])
    except subprocess.CalledProcessError:
        fail('running webpack failed')
    finally:
        if not dev:
            webpack_build_config_file.unlink()


@cli.command('all-plugins', short_help='Builds assets of all plugins in a directory.')
@click.argument('plugins_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path))
@_common_build_options(allow_watch=False)
@click.pass_context
def build_all_plugins(ctx, plugins_dir, dev, clean, url_root):
    """Run webpack to build plugin assets."""
    plugins = sorted(d for d in plugins_dir.iterdir() if _is_plugin_dir(plugins_dir / d))
    for plugin in plugins:
        step('plugin: {}', plugin)
        ctx.invoke(build_plugin, plugin_dir=(plugins_dir / plugin), dev=dev, clean=clean, watch=False,
                   url_root=url_root)


if __name__ == '__main__':
    cli()
