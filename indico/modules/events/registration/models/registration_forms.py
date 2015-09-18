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

from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum


class RegistrationFormModificationMode(int, IndicoEnum):
    allowed_always = 1
    allowed_until_payment = 2
    not_allowed = 3


class RegistrationForm(db.Model):
    __tablename__ = 'registration_forms'
    __table_args__ = {'schema': 'event_registration'}

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
    #: Whether registration modifications are allowed
    modification_mode = db.Column(
        PyIntEnum(RegistrationFormModificationMode),
        nullable=False,
        default=RegistrationFormModificationMode.not_allowed
    )
    #: Datetime when the modification period is over
    modification_end_dt = db.Column(
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

    @hybrid_property
    def has_ended(self):
        return self.end_dt is not None and self.end_dt <= now_utc()

    @has_ended.expression
    def has_ended(cls):
        return (cls.end_dt != None) & (cls.end_dt <= now_utc())  # noqa

    @hybrid_property
    def has_started(self):
        return self.start_dt is not None and self.start_dt <= now_utc()

    @has_started.expression
    def has_started(cls):
        return (cls.start_dt != None) & (cls.start_dt <= now_utc())  # noqa

    @hybrid_property
    def is_active(self):
        return not self.is_deleted and self.has_started and not self.has_ended

    @is_active.expression
    def is_active(cls):
        return ~cls.is_deleted & cls.has_started & ~cls.has_ended

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id), True)

    @property
    def locator(self):
        return dict(self.event.getLocator(), reg_form_id=self.id)

    @property
    def active_fields(self):
        return [field for field in self.form_items if not field.is_section and field.parent.is_enabled
                and not field.parent.is_deleted and field.is_enabled and not field.is_deleted]

    @return_ascii
    def __repr__(self):
        return '<RegistrationForm({}, {}, {})>'.format(self.id, self.event_id, self.title)

    def can_submit(self, user):
        return self.is_active and (not self.require_user or user)
