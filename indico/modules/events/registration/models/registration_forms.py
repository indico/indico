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

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.string import return_ascii


class RegistrationForm(db.Model):
    __tablename__ = 'registration_forms'
    __table_args__ = {'schema': 'events'}

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The title of the registration form
    title = db.Column(
        db.String,
        nullable=False
    )
    # An introduction text for users
    introduction = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: Datetime when the registration form is open
    start_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: Datetime when the registration form is closed
    end_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: Whether the registration has been marked as deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether registrations must be done by logged users
    require_user = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Maximum number of registrations allowed
    registration_limit = db.Column(
        db.Integer,
        nullable=True
    )
    # TODO: custom statuses???????
    # TODO: notification-related columns

    #: The Event containing this registration form
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'registration_forms',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - registrations (Registration.registration_form)
    # - form_items (RegistrationFormItem.registration_form)

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id), True)

    @return_ascii
    def __repr__(self):
        return '<RegistrationForm({})>'.format(self.id)
