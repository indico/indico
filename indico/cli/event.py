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

from __future__ import unicode_literals

import sys

import click

from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.events import Event


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
