#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime
from distutils.log import ERROR, set_threshold
from distutils.text_file import TextFile
from glob import glob

import click
from setuptools import find_packages
from setuptools.command.egg_info import FileList


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
        fail('{} failed'.format(title), verbose_msg=exc.output)


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
    info('cleaning build dirs')
    try:
        subprocess.check_output([sys.executable, 'setup.py', 'clean', '-a'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('clean failed', verbose_msg=exc.output)


def compile_catalogs():
    path = None
    # find ./xxx/translations/ with at least one subdir
    for root, dirs, files in os.walk('.'):
        segments = root.split(os.sep)
        if segments[-1] == 'translations' and len(segments) == 3 and dirs:
            path = root
            break
    if path is None:
        noop('plugin has no translations')
        return
    info('compiling translations')
    try:
        subprocess.check_output([sys.executable, 'setup.py', 'compile_catalog', '-d', path],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('compile_catalog failed', verbose_msg=exc.output)


def build_wheel(target_dir):
    info('building wheel')
    try:
        subprocess.check_output([sys.executable, 'setup.py', 'bdist_wheel', '-d', target_dir], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('build failed', verbose_msg=exc.output)


def git_is_clean_indico():
    toplevel = list({x.split('.')[0] for x in find_packages(include=('indico', 'indico.*',))})
    cmds = [['git', 'diff', '--stat', '--color=always'] + toplevel,
            ['git', 'diff', '--stat', '--color=always', '--staged'] + toplevel,
            ['git', 'clean', '-dn', '-e', '__pycache__'] + toplevel]
    for cmd in cmds:
        rv = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if rv:
            return False, rv
    return True, None


def _iter_package_modules(package_masks):
    for package in find_packages(include=package_masks):
        path = '/'.join(package.split('.'))
        if not os.path.exists(os.path.join(path, '__init__.py')):
            continue
        for f in glob(os.path.join(path, '*.py')):
            yield f


def _get_included_files(package_masks):
    old_threshold = set_threshold(ERROR)
    file_list = FileList()
    file_list.extend(_iter_package_modules(package_masks))
    manifest = TextFile('MANIFEST.in', strip_comments=1, skip_blanks=1, join_lines=1, lstrip_ws=1, rstrip_ws=1,
                        collapse_join=1)
    for line in manifest.readlines():
        file_list.process_template_line(line)
    set_threshold(old_threshold)
    return file_list.files


def _get_ignored_package_files_indico():
    files = set(_get_included_files(('indico', 'indico.*')))
    output = subprocess.check_output(['git', 'ls-files', '--others', '--ignored', '--exclude-standard', 'indico/'])
    ignored = {line for line in output.splitlines()}
    dist_path = 'indico/web/static/dist/'
    i18n_re = re.compile(r'^indico/translations/[a-zA-Z_]+/LC_MESSAGES/(?:messages\.mo|messages-react\.json)')
    return {path for path in ignored & files if not path.startswith(dist_path) and not i18n_re.match(path)}


def package_is_clean_indico():
    garbage = _get_ignored_package_files_indico()
    if garbage:
        return False, '\n'.join(garbage)
    return True, None


def git_is_clean_plugin():
    toplevel = list({x.split('.')[0] for x in find_packages(include=('indico', 'indico.*',))})
    cmds = [['git', 'diff', '--stat', '--color=always'] + toplevel,
            ['git', 'diff', '--stat', '--color=always', '--staged'] + toplevel]
    if toplevel:
        # only check for ignored files if we have packages. for single-module
        # plugins we don't have any package data to include anyway...
        cmds.append(['git', 'clean', '-dn', '-e', '__pycache__'] + toplevel)
    for cmd in cmds:
        rv = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if rv:
            return False, rv
    if not toplevel:
        # If we have just a single pyfile we don't need to check for ignored files
        return True, None
    rv = subprocess.check_output(['git', 'ls-files', '--others', '--ignored', '--exclude-standard'] + toplevel,
                                 stderr=subprocess.STDOUT)
    garbage_re = re.compile(r'(\.(py[co]|mo)$)|(/__pycache__/)|(^({})/static/dist/)'.format('|'.join(toplevel)))
    garbage = [x for x in rv.splitlines() if not garbage_re.search(x)]
    if garbage:
        return False, '\n'.join(garbage)
    return True, None


def patch_indico_version(add_version_suffix):
    return _patch_version(add_version_suffix, 'indico/__init__.py',
                          r"^__version__ = '([^']+)'$", r"__version__ = '\1{}'")


def patch_plugin_version(add_version_suffix):
    return _patch_version(add_version_suffix, 'setup.py', r"^(\s+)version='([^']+)'(,?)$", r"\1version='\2{}'\3")


@contextmanager
def _chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


@contextmanager
def _patch_version(add_version_suffix, file_name, search, replace):
    if not add_version_suffix:
        yield
        return
    rev = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
    suffix = '+{}.{}'.format(datetime.now().strftime('%Y%m%d%H%M'), rev)
    info('adding version suffix: ' + suffix, unimportant=True)
    with open(file_name, 'rb+') as f:
        old_content = f.read()
        f.seek(0)
        f.truncate()
        f.write(re.sub(search, replace.format(suffix), old_content, flags=re.M))
        f.flush()
        try:
            yield
        finally:
            f.seek(0)
            f.truncate()
            f.write(old_content)


@click.group()
@click.option('--target-dir', '-d', type=click.Path(file_okay=False, resolve_path=True), default='dist/',
              help='target dir for build wheels relative to the current dir')
@click.pass_obj
def cli(obj, target_dir):
    obj['target_dir'] = target_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))


@cli.command('indico')
@click.option('--no-assets', 'assets', is_flag=True, flag_value=False, default=True, help='skip building assets')
@click.option('--add-version-suffix', is_flag=True, help='Add a local suffix (+yyyymmdd.hhmm.commit) to the version')
@click.option('--ignore-unclean', is_flag=True, help='Ignore unclean working tree')
@click.pass_obj
def build_indico(obj, assets, add_version_suffix, ignore_unclean):
    """Builds the indico wheel."""
    target_dir = obj['target_dir']
    # check for unclean git status
    clean, output = git_is_clean_indico()
    if not clean and ignore_unclean:
        warn('working tree is not clean [ignored]')
    elif not clean:
        fail('working tree is not clean', verbose_msg=output)
    # check for git-ignored files included in the package
    clean, output = package_is_clean_indico()
    if not clean and ignore_unclean:
        warn('package contains unexpected files listed in git exclusions [ignored]')
    elif not clean:
        fail('package contains unexpected files listed in git exclusions', verbose_msg=output)
    if assets:
        build_assets()
    else:
        warn('building assets disabled')
    clean_build_dirs()
    with patch_indico_version(add_version_suffix):
        build_wheel(target_dir)
    clean_build_dirs()


def _validate_plugin_dir(ctx, param, value):
    if not os.path.exists(os.path.join(value, 'setup.py')):
        raise click.BadParameter('no setup.py found in {}'.format(value))
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
@click.pass_obj
def build_plugin(obj, assets, plugin_dir, add_version_suffix, ignore_unclean):
    """Builds a plugin wheel.

    PLUGIN_DIR is the path to the folder containing the plugin's setup.py
    """
    target_dir = obj['target_dir']
    with _chdir(plugin_dir):
        clean, output = git_is_clean_plugin()
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
        compile_catalogs()
        clean_build_dirs()
        with patch_plugin_version(add_version_suffix):
            build_wheel(target_dir)
        clean_build_dirs()


@cli.command('all-plugins', short_help='Builds all plugin wheels in a directory.')
@click.argument('plugins_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option('--add-version-suffix', is_flag=True, help='Add a local suffix (+yyyymmdd.hhmm.commit) to the version')
@click.option('--ignore-unclean', is_flag=True, help='Ignore unclean working tree')
@click.pass_context
def build_all_plugins(ctx, plugins_dir, add_version_suffix, ignore_unclean):
    """Builds all plugin wheels in a directory.

    PLUGINS_DIR is the path to the folder containing the plugin directories
    """
    plugins = sorted(d for d in os.listdir(plugins_dir) if os.path.exists(os.path.join(plugins_dir, d, 'setup.py')))
    for plugin in plugins:
        step('plugin: {}', plugin)
        ctx.invoke(build_plugin, plugin_dir=os.path.join(plugins_dir, plugin),
                   add_version_suffix=add_version_suffix, ignore_unclean=ignore_unclean)


if __name__ == '__main__':
    cli(obj={})
