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

from __future__ import unicode_literals

from datetime import timedelta

import click

from indico.core.config import config
from indico.util.fs import cleanup_dir


def _print_files(files):
    if not files:
        click.echo(click.style('  nothing to delete', fg='green'))
        return
    for path in sorted(files):
        click.echo('  * ' + click.style(path, fg='yellow'))


def cleanup_cmd(temp=False, cache=False, assets=False, min_age=1, dry_run=False, verbose=False):
    if cache:
        if verbose:
            click.echo(click.style('cleaning cache ({})'.format(config.CACHE_DIR), fg='white', bold=True))
        deleted = cleanup_dir(config.CACHE_DIR, timedelta(days=min_age), dry_run=dry_run,
                              exclude=lambda x: x.startswith('webassets-'))
        if verbose:
            _print_files(deleted)
    if temp:
        if verbose:
            click.echo(click.style('cleaning temp ({})'.format(config.TEMP_DIR), fg='white', bold=True))
        deleted = cleanup_dir(config.TEMP_DIR, timedelta(days=min_age), dry_run=dry_run)
        if verbose:
            _print_files(deleted)
    if assets:
        if verbose:
            click.echo(click.style('cleaning assets ({})'.format(config.ASSETS_DIR), fg='white', bold=True))
        deleted = cleanup_dir(config.ASSETS_DIR, timedelta(days=min_age), dry_run=dry_run)
        if verbose:
            _print_files(deleted)
    if dry_run:
        click.echo(click.style('dry-run enabled, nothing has been deleted', fg='green', bold=True))
