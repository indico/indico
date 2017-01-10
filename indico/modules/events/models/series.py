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

from indico.core.db import db
from indico.util.string import return_ascii, format_repr


class EventSeries(db.Model):
    """A series of events."""

    __tablename__ = 'series'
    __table_args__ = {'schema': 'events'}

    #: The ID of the series
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: Whether to show the sequence number of an event in its title
    #: on category display pages and on the main event page.
    show_sequence_in_title = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Whether to show links to the other events in the same series
    #: on the main event page.
    show_links = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # relationship backrefs:
    # - events (Event.series)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id')
