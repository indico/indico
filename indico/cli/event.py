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

import sys

import click

from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.export import export_event, import_event


click.disable_unicode_literals_warning = True


@cli_group()
def cli():
    pass


@cli.command()
@click.argument('event_id', type=int)
def restore(event_id):
    """Restores a deleted event."""
    event = Event.get(event_id)
    if event is None:
        click.secho('This event does not exist', fg='red')
        sys.exit(1)
    elif not event.is_deleted:
        click.secho('This event is not deleted', fg='yellow')
        sys.exit(1)
    event.is_deleted = False
    db.session.commit()
    click.secho('Event undeleted: "{}"'.format(event.title), fg='green')


@cli.command()
@click.argument('event_id', type=int)
@click.argument('target_file', type=click.File('wb'))
def export(event_id, target_file):
    """Exports all data associated with an event.

    This exports the whole event as an archive which can be imported
    on another other Indico instance.  Importing an event is only
    guaranteed to work if it was exported on the same Indico version.
    """
    event = Event.get(event_id)
    if event is None:
        click.secho('This event does not exist', fg='red')
        sys.exit(1)
    elif event.is_deleted:
        click.secho('This event has been deleted', fg='yellow')
        click.confirm('Export it anyway?', abort=True)
    export_event(event, target_file)


@cli.command('import')
@click.argument('source_file', type=click.File('rb'))
@click.option('--create-users/--no-create-users', default=None,
              help='Whether to create missing user or skip them.  By default a confirmation prompt is shown when '
                   'the archive contains such users')
@click.option('--force', is_flag=True, help='Ignore Indico version mismatches (DANGER)')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose information on what is being imported')
@click.option('-y', '--yes', is_flag=True, help='Always commit the imported event without prompting')
@click.option('-c', '--category', 'category_id', type=int, default=0, metavar='ID',
              help='ID of the target category. Defaults to the root category.')
def import_(source_file, create_users, force, verbose, yes, category_id):
    """Imports an event exported from another Indico instance."""
    click.echo('Importing event...')
    event = import_event(source_file, category_id, create_users=create_users, verbose=verbose, force=force)
    if event is None:
        click.secho('Import failed.', fg='red')
        sys.exit(1)
    if not yes and not click.confirm(click.style('Import finished. Commit the changes?', fg='green'), default=True):
        db.session.rollback()
        sys.exit(1)
    db.session.commit()
    click.secho(event.external_url, fg='green', bold=True)
