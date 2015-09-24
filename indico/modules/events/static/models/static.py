# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import errno
import os

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum


class StaticSiteState(TitledIntEnum):
    __titles__ = [_("Pending"), _("Running"), _("Success"), _("Failed"), _("Expired")]
    pending = 0
    running = 1
    success = 2
    failed = 3
    expired = 4


class StaticSite(db.Model):
    """Static site for an Indico event."""
    __tablename__ = 'static_sites'
    __table_args__ = {'schema': 'events'}

    #: Entry ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The state of the static site (a :class:`StaticSiteState` member)
    state = db.Column(
        PyIntEnum(StaticSiteState),
        default=StaticSiteState.pending,
        nullable=False
    )
    #: The date and time the static site was requested
    requested_dt = db.Column(
        UTCDateTime,
        default=now_utc,
        nullable=False
    )
    #: path to the zip archive of the static site
    path = db.Column(
        db.String,
        nullable=True
    )
    #: ID of the user who created the static site
    creator_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )

    #: The user who created the static site
    creator = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'static_sites',
            lazy='dynamic'
        )
    )
    #: The Event this static site is associated with
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'static_sites',
            lazy='dynamic'
        )
    )

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id))

    @property
    def locator(self):
        return {'confId': self.event_id,
                'id': self.id}

    def delete_file(self):
        if not self.path:
            return
        try:
            os.remove(self.path)
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise

    def __committed__(self, change):
        super(StaticSite, self).__committed__(change)
        if change == 'delete':
            self.delete_file()

    @return_ascii
    def __repr__(self):
        state = self.state.name if self.state is not None else None
        return '<StaticSite({}, {}, {})>'.format(self.id, self.event_id, state)
