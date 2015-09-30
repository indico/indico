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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class Registration(db.Model):
    __tablename__ = 'registrations'
    __table_args__ = {'schema': 'event_registration'}

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the registration form
    registration_form_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.forms.id'),
        index=True,
        nullable=False
    )
    #: The ID of the user who registered
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    #: The date/time when the registration was recorded
    submitted_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc,
    )

    #: The registration form this registration is attached to
    registration_form = db.relationship(
        'RegistrationForm',
        lazy=True,
        backref=db.backref(
            'registrations',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )

    # The user linked to this registration
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'registrations',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
    )

    # relationship backref
    # - data (RegistrationData.registration)

    @return_ascii
    def __repr__(self):
        return '<Registration({}, {}, {})>'.format(self.id, self.registration_form_id, self.user_id)


class RegistrationData(db.Model):
    __tablename__ = 'registration_data'
    __table_args__ = (db.CheckConstraint("(file IS NULL) = (file_metadata::text = 'null')", name='valid_file'),
                      {'schema': 'event_registration'})

    #: The ID of the registration
    registration_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registrations.id'),
        primary_key=True,
        autoincrement=False
    )
    #: The ID of the field data
    field_data_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.form_field_data.id'),
        primary_key=True,
        autoincrement=False
    )
    #: The user's data for the field
    data = db.Column(
        JSON,
        nullable=False
    )
    #: file contents for a file field
    file = db.Column(
        db.LargeBinary,
        nullable=True
    )
    #: metadata of the uploaded file
    file_metadata = db.Column(
        JSON,
        nullable=False
    )

    #: The registration this data is associated with
    registration = db.relationship(
        'Registration',
        lazy=True,
        backref=db.backref(
            'data',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )

    #: The associated field data object
    field_data = db.relationship(
        'RegistrationFormFieldData',
        lazy=True,
        backref=db.backref(
            'registration_data',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )

    @return_ascii
    def __repr__(self):
        return '<RegistrationData({}, {}): {}>'.format(self.registration_id,
                                                       self.field_data_id, self.data)
