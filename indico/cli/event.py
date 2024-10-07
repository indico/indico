# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import sys
from pathlib import Path

import click
import yaml

from indico.cli.core import cli_group
from indico.core import signals
from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.export import export_event, import_event
from indico.modules.events.models.series import EventSeries
from indico.modules.users.models.users import User


@cli_group()
def cli():
    pass


@cli.command()
@click.argument('event_id', type=int)
@click.option('-u', '--user', 'user_id', type=int, default=None, metavar='USER_ID',
              help='The user which will be shown on the log as having restored the event (default: no user).')
@click.option('-m', '--message', 'message', metavar='MESSAGE', help='An additional message for the log')
def restore(event_id, user_id, message):
    """Restore a deleted event."""
    event = Event.get(event_id)
    user = User.get(user_id) if user_id else None
    if event is None:
        click.secho('This event does not exist', fg='red')
        sys.exit(1)
    elif not event.is_deleted:
        click.secho('This event is not deleted', fg='yellow')
        sys.exit(1)
    event.restore(message, user)
    signals.core.after_process.send()
    db.session.commit()
    click.secho(f'Event undeleted: "{event.title}"', fg='green')


@cli.command()
@click.argument('event_id', type=int)
@click.argument('target_file', type=click.File('wb'))
@click.option('-U', '--keep-uuids', is_flag=True,
              help='Whether to keep UUIDs instead of generating new ones during import.')
def export(event_id, target_file, keep_uuids):
    """Export all data associated with an event.

    This exports the whole event as an archive which can be imported
    on another other Indico instance.  Importing an event is only
    guaranteed to work if it was exported on the same Indico version.

    When keeping UUIDs, the event cannot be imported again on the same instance unless
    (in most cases) the original event has been deleted, but it may be useful when you
    migrate an event to another instance and want to preserve links (usually by using a
    custom plugin on the source instance to map old IDs to new ones). Unless this is what
    you are doing, you probably do not want to use this flag.
    """
    event = Event.get(event_id)
    if event is None:
        click.secho('This event does not exist', fg='red')
        sys.exit(1)
    elif event.is_deleted:
        click.secho('This event has been deleted', fg='yellow')
        click.confirm('Export it anyway?', abort=True)
    export_event(event, target_file, keep_uuids=keep_uuids)


@cli.command('import')
@click.argument('source_file', type=click.File('rb'))
@click.option('--create-users/--no-create-users', default=None,
              help='Whether to create missing users or skip them.  By default a confirmation prompt is shown when '
                   'the archive contains such users')
@click.option('--create-affiliations/--no-create-affiliations', default=None,
              help='Whether to create missing affiliations or skip them.  By default a confirmation prompt is shown '
                   'when the archive contains such affiliations')
@click.option('--force', is_flag=True, help='Ignore Indico version mismatches (DANGER)')
@click.option('-v', '--verbose', is_flag=True, help='Show verbose information on what is being imported')
@click.option('-y', '--yes', is_flag=True, help='Always commit the imported event without prompting')
@click.option('-c', '--category', 'category_id', type=int, default=0, metavar='ID',
              help='ID of the target category. Defaults to the root category.')
@click.option('-m', '--id-map', 'id_map_path', type=click.Path(dir_okay=False, path_type=Path),
              help='Store the mapping between old and new IDs in this YAML file')
def import_(source_file, create_users, create_affiliations, force, verbose, yes, category_id,
            id_map_path: Path | None = None):
    """Import an event exported from another Indico instance."""
    click.echo('Importing event...')
    event, id_map = import_event(source_file, category_id, create_users=create_users,
                                 create_affiliations=create_affiliations, verbose=verbose, force=force)
    if event is None:
        click.secho('Import failed.', fg='red')
        sys.exit(1)
    if not yes and not click.confirm(click.style('Import finished. Commit the changes?', fg='green'), default=True):
        db.session.rollback()
        sys.exit(1)
    db.session.commit()
    click.secho(event.external_url, fg='green', bold=True)
    if id_map_path:
        id_map_path.write_text(yaml.dump(id_map, indent=2))
        click.echo(f'ID mapping written to {id_map_path}')


@cli.command('create-series')
@click.option('--title-sequence/--no-title-sequence', 'show_sequence_in_title', default=True,
              help='Whether to show the series sequence in the event titles (lectures only); enabled by default')
@click.option('--links/--no-links', 'show_links', default=True,
              help='Whether to show links to other events in the series on the event page; enabled by default')
@click.argument('event_ids', nargs=-1, type=int, metavar='EVENT_ID...')
def create_series(show_sequence_in_title, show_links, event_ids):
    """Create a series from a list of events."""
    events = Event.query.filter(Event.id.in_(event_ids), ~Event.is_deleted).all()

    if missing := (set(event_ids) - {e.id for e in events}):
        click.secho('Events not found:', fg='red', bold=True)
        for event_id in missing:
            click.echo(f'- {event_id}')
        sys.exit(1)
    elif conflict := [e for e in events if e.series]:
        click.secho('Events already assigned to a series:', fg='red', bold=True)
        for event in conflict:
            click.echo(format_event(event))
        sys.exit(1)

    click.echo('Selected events:')
    for event in events:
        click.echo(format_event(event))

    click.confirm('Create series?', default=True, abort=True)

    series = EventSeries(events=events, show_sequence_in_title=show_sequence_in_title, show_links=show_links)
    db.session.commit()

    click.secho(f'Series successfully created (id={series.id}).', fg='green', bold=True)


def format_event(event):
    return f'- {event.id}: [{event.start_dt_local.date()}] {event.title} ({event.external_url})'
