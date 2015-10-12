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

from uuid import uuid4

from flask import has_request_context, session, request
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.ext.hybrid import hybrid_property


from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.payment import event_settings as event_payment_settings
from indico.util.date_time import now_utc
from indico.util.i18n import L_
from indico.util.locators import locator_property
from indico.util.string import return_ascii, format_repr
from indico.util.struct.enum import TitledIntEnum


class RegistrationState(TitledIntEnum):
    __titles__ = [None, L_('Completed'), L_('Pending'), L_('Rejected'), L_('Withdrawn'), L_('Unpaid')]
    complete = 1
    pending = 2
    rejected = 3
    withdrawn = 4
    unpaid = 5


class Registration(db.Model):
    """Somebody's registration for an event through a registration form"""
    __tablename__ = 'registrations'
    __table_args__ = (db.CheckConstraint('email = lower(email)', 'lowercase_email'),
                      db.Index(None, 'registration_form_id', 'user_id', unique=True,
                               postgresql_where=db.text('state NOT IN (3, 4)')),
                      db.Index(None, 'registration_form_id', 'email', unique=True,
                               postgresql_where=db.text('state NOT IN (3, 4)')),
                      {'schema': 'event_registration'})

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The unguessable ID for the object
    uuid = db.Column(
        UUID,
        index=True,
        unique=True,
        nullable=False,
        default=lambda: unicode(uuid4())
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
    #: The state a registration is in
    state = db.Column(
        PyIntEnum(RegistrationState),
        nullable=False,
    )
    #: The date/time when the registration was recorded
    submitted_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc,
    )
    #: The email of the registrant
    email = db.Column(
        db.String,
        nullable=False
    )
    #: The first name of the registrant
    first_name = db.Column(
        db.String,
        nullable=False
    )
    #: The last name of the registrant
    last_name = db.Column(
        db.String,
        nullable=False
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
    #: The registration this data is associated with
    data = db.relationship(
        'RegistrationData',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'registration',
            lazy=True
        )
    )

    # relationship backrefs:
    # - registration_form (RegistrationForm.registrations)

    @hybrid_property
    def is_cancelled(self):
        return self.state in (RegistrationState.rejected, RegistrationState.withdrawn)

    @is_cancelled.expression
    def is_cancelled(self):
        return self.state.in_((RegistrationState.rejected, RegistrationState.withdrawn))

    @locator_property
    def locator(self):
        return dict(self.registration_form.locator, registration_id=self.id)

    @locator.registrant
    def locator(self):
        """A locator suitable for 'display' pages.

        It includes the UUID of the registration unless the current
        request doesn't contain the uuid and the registration is tied
        to the currently logged-in user.
        """
        loc = self.registration_form.locator
        if (not self.user or not has_request_context() or self.user != session.user or
                request.args.get('token') == self.uuid):
            loc['token'] = self.uuid
        return loc

    @property
    def data_by_field(self):
        return {x.field_data.field_id: x for x in self.data}

    @return_ascii
    def __repr__(self):
        full_name = '{} {}'.format(self.first_name, self.last_name)
        return format_repr(self, 'id', 'registration_form_id', 'email', 'state', user_id=None, _text=full_name)

    def init_state(self, event):
        """Initialize state of the object"""
        if self.state is not None:
            raise Exception("The registration already has a state")
        with db.session.no_autoflush:
            if self.registration_form.moderation_enabled:
                self.state = RegistrationState.pending
            elif event_payment_settings.get(event, 'enabled') and self.price:
                self.state = RegistrationState.unpaid
            else:
                self.state = RegistrationState.complete

    @property
    def price(self):
        return sum(data.price for data in self.data)


class RegistrationData(db.Model):
    """Data entry within a registration for a field in a registration form"""

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
    file = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))
    #: metadata of the uploaded file
    file_metadata = db.Column(
        JSON,
        nullable=False
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

    # relationship backrefs:
    # - registration (Registration.data)

    @locator_property
    def locator(self):
        # a normal locator doesn't make much sense
        raise NotImplementedError

    @locator.file
    def locator(self):
        """A locator that pointsto the associated file."""
        if not self.file_metadata:
            raise Exception('The file locator is only available if there is a file.')
        return dict(self.registration.locator, field_data_id=self.field_data_id,
                    filename=self.file_metadata['filename'])

    @property
    def friendly_data(self):
        return self.field_data.field.field_impl.get_friendly_data(self)

    @property
    def price(self):
        return self.field_data.field.calculate_price(self)

    @return_ascii
    def __repr__(self):
        return '<RegistrationData({}, {}): {}>'.format(self.registration_id, self.field_data_id, self.data)
