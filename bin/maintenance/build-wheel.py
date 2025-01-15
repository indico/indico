#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import click


def fail(message, *args, **kwargs):
    click.echo(click.style('Error: ' + message.format(*args), fg='red', bold=True), err=True)
    if 'verbose_msg' in kwargs:
        click.echo(kwargs['verbose_msg'], err=True)
    sys.exit(1)


def warn(message, *args):
    click.echo(click.style(message.format(*args), fg='yellow', bold=True), err=True)


def noop(message, *args):
    click.echo(click.style(message.format(*args), fg='green'), err=True)


def info(message, *args, **kwargs):
    unimportant = kwargs.pop('unimportant', False)
    click.echo(click.style(message.format(*args), fg='green', bold=(not unimportant)), err=True)


def step(message, *args):
    click.echo(click.style(message.format(*args), fg='white', bold=True), err=True)


def run(cmd, title, shell=False):
    if shell:
        cmd = ' '.join(cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=shell)
    except subprocess.CalledProcessError as exc:
        fail(f'{title} failed', verbose_msg=exc.output)


def build_assets():
    info('building assets')
    try:
        subprocess.check_output(['./bin/maintenance/build-assets.py', 'indico', '--clean'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('building assets failed', verbose_msg=exc.output)


def build_assets_plugin(plugin_dir):
    info('building assets')
    try:
        subprocess.check_output(['./bin/maintenance/build-assets.py', 'plugin', '--clean', plugin_dir],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('building assets failed', verbose_msg=exc.output)


def clean_build_dirs():
    if not os.path.exists('build'):
        return
    # XXX this should no longer be needed now that we do a clean source -> sdist -> wheel
    # build (and no longer use setuptools for our own plugins anyway), but let's keep it
    # around just in case
    info('cleaning build dirs')
    shutil.rmtree('build')


def build_wheel(target_dir: Path):
    info('building wheel')
    old_sdists = set(target_dir.glob('*.tar.gz'))
    try:
        subprocess.check_output([sys.executable, '-m', 'build', '--installer', 'uv', '-o', target_dir],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('build failed', verbose_msg=exc.output)
    finally:
        # We do not use/support sdists, but by using a standard build where first an sdist is
        # built, and then a wheel is built using that sdist, we ensure that e.g. a plugin which
        # still uses setuptools as its build backend does not leave build artifacts such as the
        # `build` dir behind.
        for sdist in set(target_dir.glob('*.tar.gz')) - old_sdists:
            sdist.unlink()


def git_is_clean(*paths):
    cmds = [['git', 'diff', '--stat', '--color=always', *paths],
            ['git', 'diff', '--stat', '--color=always', '--staged', *paths],
            ['git', 'clean', '-dn', *paths]]
    for cmd in cmds:
        rv = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        if rv:
            return False, rv
    return True, None


def patch_indico_version(add_version_suffix):
    return _patch_version(add_version_suffix, 'indico/__init__.py',
                          r"^__version__ = '([^']+)'$", r"__version__ = '\1{}'")


def patch_plugin_version(add_version_suffix):
    return _patch_version(add_version_suffix, 'pyproject.toml', r"^version = '(.+)'$", r"version = '\1{}'")


@contextmanager
def _chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def _get_build_time():
    timestamp = int(os.environ.get('SOURCE_DATE_EPOCH', time.time()))
    return datetime.fromtimestamp(timestamp)


@contextmanager
def _patch_version(add_version_suffix, file_name, search, replace):
    if not add_version_suffix:
        yield
        return
    rev = subprocess.check_output(['git', 'rev-parse', '--short=10', 'HEAD'], text=True).strip()
    suffix = '+{}.{}'.format(_get_build_time().strftime('%Y%m%d%H%M'), rev)
    info('adding version suffix: ' + suffix, unimportant=True)
    with open(file_name, 'r+') as f:
        old_content = f.read()
        f.seek(0)
        f.truncate()
        f.write(re.sub(search, replace.format(suffix), old_content, flags=re.MULTILINE))
        f.flush()
        try:
            yield
        finally:
            f.seek(0)
            f.truncate()
            f.write(old_content)


@click.group()
@click.option('--target-dir', '-d', type=click.Path(file_okay=False, resolve_path=True, path_type=Path),
              default='dist/', help='target dir for build wheels relative to the current dir')
@click.pass_obj
def cli(obj, target_dir: Path):
    obj['target_dir'] = target_dir
    target_dir.mkdir(exist_ok=True)
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))


@cli.command('indico')
@click.option('--no-assets', 'assets', is_flag=True, flag_value=False, default=True, help='skip building assets')
@click.option('--add-version-suffix', is_flag=True, help='Add a local suffix (+yyyymmdd.hhmm.commit) to the version')
@click.option('--ignore-unclean', is_flag=True, help='Ignore unclean working tree')
@click.option('--no-git', is_flag=True, help='Skip git checks and assume clean working tree')
@click.pass_obj
def build_indico(obj, assets, add_version_suffix, ignore_unclean, no_git):
    """Build the indico wheel."""
    target_dir = obj['target_dir']
    if no_git:
        warn('Assuming clean non-git working tree')
        if add_version_suffix:
            fail('The --no-git option cannot be used with --add-version-suffix')
    else:
        # check for unclean git status
        clean, output = git_is_clean('indico')
        if not clean and ignore_unclean:
            warn('working tree is not clean [ignored]')
        elif not clean:
            fail('working tree is not clean', verbose_msg=output)
    if assets:
        build_assets()
    else:
        warn('building assets disabled')
    with patch_indico_version(add_version_suffix):
        build_wheel(target_dir)


def _validate_plugin_dir(ctx, param, value):
    if not os.path.exists(os.path.join(value, 'pyproject.toml')):
        raise click.BadParameter(f'no pyproject.toml found in {value}')
    return value


def _plugin_has_assets(plugin_dir):
    return (os.path.exists(os.path.join(plugin_dir, 'webpack.config.js')) or
            os.path.exists(os.path.join(plugin_dir, 'webpack-bundles.json')))


@cli.command('plugin', short_help='Builds a plugin wheel.')
@click.argument('plugin_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                callback=_validate_plugin_dir)
@click.option('--no-assets', 'assets', is_flag=True, flag_value=False, default=True, help='skip building assets')
@click.option('--add-version-suffix', is_flag=True, help='Add a local suffix (+yyyymmdd.hhmm.commit) to the version')
@click.option('--ignore-unclean', is_flag=True, help='Ignore unclean working tree')
@click.option('--no-git', is_flag=True, help='Skip git checks and assume clean working tree')
@click.pass_obj
def build_plugin(obj, assets, plugin_dir, add_version_suffix, ignore_unclean, no_git):
    """Build a plugin wheel.

    PLUGIN_DIR is the path to the folder containing the plugin's pyproject.toml
    """
    target_dir = obj['target_dir']
    with _chdir(plugin_dir):
        if no_git:
            clean, output = True, None
            warn('Assuming clean non-git working tree')
            if add_version_suffix:
                fail('The --no-git option cannot be used with --add-version-suffix')
        else:
            clean, output = git_is_clean('.')
            if not clean and ignore_unclean:
                warn('working tree is not clean, but ignored')
            elif not clean:
                fail('working tree is not clean', verbose_msg=output)
    if assets:
        if not _plugin_has_assets(plugin_dir):
            noop('plugin has no assets')
        else:
            build_assets_plugin(plugin_dir)
    else:
        warn('building assets disabled')
    with _chdir(plugin_dir):
        clean_build_dirs()
        with patch_plugin_version(add_version_suffix):
            build_wheel(target_dir)
        clean_build_dirs()


@cli.command('all-plugins', short_help='Builds all plugin wheels in a directory.')
@click.argument('plugins_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option('--no-assets', 'assets', is_flag=True, flag_value=False, default=True, help='skip building assets')
@click.option('--add-version-suffix', is_flag=True, help='Add a local suffix (+yyyymmdd.hhmm.commit) to the version')
@click.option('--ignore-unclean', is_flag=True, help='Ignore unclean working tree')
@click.option('--no-git', is_flag=True, help='Skip checks and assume clean non-git working tree')
@click.pass_context
def build_all_plugins(ctx, assets, plugins_dir, add_version_suffix, ignore_unclean, no_git):
    """Build all plugin wheels in a directory.

    PLUGINS_DIR is the path to the folder containing the plugin directories
    """
    plugins = sorted(d for d in os.listdir(plugins_dir)
                     if os.path.exists(os.path.join(plugins_dir, d, 'pyproject.toml')))
    for plugin in plugins:
        step('plugin: {}', plugin)
        ctx.invoke(build_plugin, plugin_dir=os.path.join(plugins_dir, plugin), assets=assets,
                   add_version_suffix=add_version_suffix, ignore_unclean=ignore_unclean, no_git=no_git)


if __name__ == '__main__':
    cli(obj={})
