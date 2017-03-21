#!/usr/bin/env python
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
import re
import subprocess
import sys

import click
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


def run(cmd, title, shell=False):
    if shell:
        cmd = ' '.join(cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=shell)
    except subprocess.CalledProcessError as exc:
        fail('{} failed'.format(title), verbose_msg=exc.output)


def setup_deps():
    info('building deps')
    try:
        subprocess.check_output(['node', '--version'], stderr=subprocess.STDOUT)
    except OSError as exc:
        warn('could not run system node: {}', exc)
        warn('falling back to nodeenv')
        system_node = False
    else:
        system_node = True
    try:
        subprocess.check_output(['fab', 'setup_deps:system_node={}'.format(system_node)], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('setup_deps failed', verbose_msg=exc.output)


def clean_build_dirs():
    info('cleaning build dirs')
    try:
        subprocess.check_output([sys.executable, 'setup.py', 'clean', '-a'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('clean failed', verbose_msg=exc.output)


def build_wheel():
    info('building wheel')
    try:
        subprocess.check_output([sys.executable, 'setup.py', 'bdist_wheel'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('build failed', verbose_msg=exc.output)


def git_is_clean():
    libs_re = re.compile(r'^indico/htdocs/(css|sass|js)/lib')
    toplevel = list({x.split('.')[0] for x in find_packages()})
    cmds = [['git', 'diff', '--stat', '--color=always'] + toplevel,
            ['git', 'diff', '--stat', '--color=always', '--staged'] + toplevel,
            ['git', 'clean', '-dn'] + toplevel]
    for cmd in cmds:
        rv = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if rv:
            return False, rv
    rv = subprocess.check_output(['git', 'ls-files', '--others', '--ignored', '--exclude-standard', 'indico/htdocs'],
                                 stderr=subprocess.STDOUT)
    garbage = [x for x in rv.splitlines() if not libs_re.match(x)]
    if garbage:
        return False, '\n'.join(garbage)
    return True, None


@click.command()
@click.option('--no-deps', 'deps', is_flag=True, flag_value=False, default=True, help='skip setup_deps')
def main(deps):
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
    clean, output = git_is_clean()
    if not clean:
        fail('working tree is not clean', verbose_msg=output)
    if deps:
        setup_deps()
    else:
        warn('building deps disabled')
    clean_build_dirs()
    build_wheel()
    clean_build_dirs()


if __name__ == '__main__':
    main()
