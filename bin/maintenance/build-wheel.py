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
import subprocess
import sys

import click
from setuptools import find_packages
from termcolor import colored


def fail(message, *args, **kwargs):
    print >> sys.stderr, colored('Error: ' + message.format(*args), 'red', attrs=['bold'])
    if 'verbose_msg' in kwargs:
        print >> sys.stderr, kwargs['verbose_msg']
    sys.exit(1)


def warn(message, *args):
    print >> sys.stderr, colored(message.format(*args), 'yellow', attrs=['bold'])


def info(message, *args):
    print >> sys.stderr, colored(message.format(*args), 'green', attrs=['bold'])


def get_highest_mtime(path):
    maxt = 0
    for dirpath, _, fnames in os.walk(path):
        for fname in fnames:
            mtime = os.path.getmtime(os.path.join(dirpath, fname))
            if mtime > maxt:
                maxt = mtime
    return maxt


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


def build_docs(html, pdf, force):
    target_dir = os.path.join('indico', 'htdocs', 'ihelp')
    has_html_docs = bool(set(os.listdir('indico/htdocs/ihelp/html/')) - {'.keep'})
    has_pdf_docs = bool(set(os.listdir('indico/htdocs/ihelp/pdf/')) - {'.keep'})

    info('building docs')
    if ((not html or has_html_docs) and (not pdf or has_pdf_docs) and
            get_highest_mtime(target_dir) > get_highest_mtime('doc')):
        info('docs are up to date')
        if force:
            warn('force-rebuild enabled, building them anyway')
        else:
            return

    if pdf:
        try:
            subprocess.check_output(['pdflatex', '--version'], stderr=subprocess.STDOUT)
        except OSError as exc:
            fail('pdflatex not found {}', exc)

    if html:
        info('building html docs')
        run(['make', '-C', 'doc/guides', 'html'], 'building html docs')
    else:
        warn('building html docs disabled')
    if pdf:
        info('building pdf docs (takes some time)')
        run(['make', '-C', 'doc/guides', 'latexpdf'], 'building pdf docs')
    else:
        warn('building pdf docs disabled')
    run(['rm', '-rf', os.path.join(target_dir, 'html', '*'), os.path.join(target_dir, 'pdf', '*')], 'rm', shell=True)
    if html:
        run(['mv', 'doc/guides/build/html/*', os.path.join(target_dir, 'html', '')], 'moving html docs', shell=True)
    if pdf:
        run(['mv', 'doc/guides/build/latex/*.pdf', os.path.join(target_dir, 'pdf', '')], 'moving pdf docs', shell=True)
    run(['make', '-C', 'doc/guides', 'clean'], 'cleaning up')


def build_wheel():
    info('building wheel')
    try:
        subprocess.check_output([sys.executable, 'setup.py', 'bdist_wheel'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        fail('build failed', verbose_msg=exc.output)


def git_is_clean():
    toplevel = list({x.split('.')[0] for x in find_packages()})
    cmds = [['git', 'diff', '--stat', '--color=always'] + toplevel,
            ['git', 'diff', '--stat', '--color=always', '--staged'] + toplevel,
            ['git', 'clean', '-dn'] + toplevel]
    for cmd in cmds:
        rv = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if rv:
            return False, rv
    return True, None


@click.command()
@click.option('--no-deps', 'deps', is_flag=True, flag_value=False, default=True, help='skip setup_deps')
@click.option('--no-html-docs', 'html_docs', is_flag=True, flag_value=False, default=True, help='skip html docs')
@click.option('--no-pdf-docs', 'pdf_docs', is_flag=True, flag_value=False, default=True, help='skip pdf docs')
@click.option('--force-docs', is_flag=True, help='force rebuilding docs')
def main(deps, html_docs, pdf_docs, force_docs):
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
    clean, output = git_is_clean()
    if not clean:
        fail('working tree is not clean', verbose_msg=output)
    if deps:
        setup_deps()
    else:
        warn('building deps disabled')
    if html_docs or pdf_docs:
        build_docs(html_docs, pdf_docs, force_docs)
    elif force_docs:
        fail('cannot force doc rebuild with docs disabled')
    else:
        warn('building docs disabled')
    build_wheel()


if __name__ == '__main__':
    main()
