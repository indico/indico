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

from __future__ import unicode_literals, print_function

import os
import shutil
import sys

import click
from flask.helpers import get_root_path

from indico.util.console import cformat

click.disable_unicode_literals_warning = True


def _copy(src, dst, force=False):
    if not force and os.path.exists(dst):
        print(cformat('%{yellow!}{}%{reset}%{yellow} already exists; not copying %{yellow!}{}')
              .format(dst, src))
        return
    print(cformat('%{green}Copying %{green!}{}%{reset}%{green} to %{green!}{}').format(src, dst))
    shutil.copy(src, dst)


def _link(src, dst):
    print(cformat('%{cyan}Linking %{cyan!}{}%{reset}%{cyan} -> %{cyan!}{}').format(dst, src))
    if os.path.exists(dst) or os.path.islink(dst):
        os.unlink(dst)
    os.symlink(src, dst)


def _get_dirs(target_dir):
    if not os.path.isdir(target_dir):
        print(cformat('%{red}Directory not found:%{red!} {}').format(target_dir))
        sys.exit(1)
    return get_root_path('indico'), os.path.abspath(target_dir)


@click.group()
def cli():
    """This script helps with the initial steps of installing Indico"""
    # XXX: Using a standalone CLI instead of manage.py since
    # this code must be able to run without having an indico.conf.
    # In the future this can most likely be merged into the `indico`
    # cli (once we don't need config access at import time)


@cli.command()
@click.argument('target_dir')
def create_symlinks(target_dir):
    """Creates useful symlinks to run Indico from a webserver.

    This lets you use static paths for the WSGI file and the htdocs
    folder so you do not need to update your webserver config when
    updating Indico.
    """
    root_dir, target_dir = _get_dirs(target_dir)
    _copy(os.path.join(root_dir, 'web', 'indico.wsgi'), os.path.join(target_dir, 'indico.wsgi'), force=True)
    _link(os.path.join(root_dir, 'htdocs'), os.path.join(target_dir, 'htdocs'))


@cli.command()
@click.argument('target_dir')
def create_configs(target_dir):
    """Creates the initial config files for Indico.

    If a file already exists it is left untouched. This command is
    usually only used when doing a fresh indico installation.
    """
    root_dir, target_dir = _get_dirs(target_dir)
    _copy(os.path.normpath(os.path.join(root_dir, 'indico.conf.sample')), os.path.join(target_dir, 'indico.conf'))
    _copy(os.path.normpath(os.path.join(root_dir, 'logging.conf.sample')), os.path.join(target_dir, 'logging.conf'))


# TODO: Add another command that sets up the directory structure
# and possibly a config with useful default values for development.
