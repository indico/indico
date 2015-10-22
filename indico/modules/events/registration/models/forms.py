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

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.registration.models.registrations import Registration
from indico.util.caching import memoize_request
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum


class ModificationMode(int, IndicoEnum):
    allowed_always = 1
    allowed_until_payment = 2
    not_allowed = 3


class RegistrationForm(db.Model):
    """A registration form for an event"""

    __tablename__ = 'forms'
    __table_args__ = (db.UniqueConstraint('id', 'event_id'),  # useless but needed for the registrations fkey
                      {'schema': 'event_registration'})

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
    #: Contact information for registrants
    contact_info = db.Column(
        db.String,
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
        PyIntEnum(ModificationMode),
        nullable=False,
        default=ModificationMode.not_allowed
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
    #: Whether users must be logged in to register
    require_login = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether registrations must be associated with an Indico account
    require_user = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Maximum number of registrations allowed
    registration_limit = db.Column(
        db.Integer,
        nullable=True
    )
    #: Whether registrations must be approved by a manager
    moderation_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The base fee users have to pay when registering
    base_price = db.Column(
        db.Numeric(8, 2),  # max. 999999.99
        nullable=False,
        default=0
    )
    #: Custom message to include in emails for pending registrations
    message_pending = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: Custom message to include in emails for unpaid registrations
    message_unpaid = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: Custom message to include in emails for complete registrations
    message_complete = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: Whether the manager notifications for this event are enabled
    manager_notifications_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: List of emails that should receive management notifications
    manager_notification_recipients = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    #: Whether tickets are enabled for this form
    tickets_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether to send tickets by e-mail
    ticket_on_email = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Whether to show a ticket download link on the event homepage
    ticket_on_event_page = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Whether to show a ticket download link on the registration summary page
    ticket_on_summary_page = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    #: The Event containing this registration form
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'registration_forms',
            lazy='dynamic'
        )
    )
    # The items (sections, text, fields) in the form
    form_items = db.relationship(
        'RegistrationFormItem',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='RegistrationFormItem.position',
        backref=db.backref(
            'registration_form',
            lazy=True
        )
    )
    #: The registrations associated with this form
    registrations = db.relationship(
        'Registration',
        lazy=True,
        cascade='all, delete-orphan',
        foreign_keys=[Registration.registration_form_id],
        backref=db.backref(
            'registration_form',
            lazy=True
        )
    )
    #: The registration invitations associated with this form
    invitations = db.relationship(
        'RegistrationInvitation',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'registration_form',
            lazy=True
        )
    )

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
    def is_modification_open(self):
        end_dt = self.modification_end_dt if self.modification_end_dt else self.end_dt
        return now_utc() <= end_dt if end_dt else True

    @is_modification_open.expression
    def is_modification_open(self):
        now = now_utc()
        return now <= db.func.coalesce(self.modification_end_dt, self.end_dt, now)

    @hybrid_property
    def is_open(self):
        return not self.is_deleted and self.has_started and not self.has_ended

    @is_open.expression
    def is_open(cls):
        return ~cls.is_deleted & cls.has_started & ~cls.has_ended

    @hybrid_property
    def is_scheduled(self):
        return not self.is_deleted and self.start_dt is not None

    @is_scheduled.expression
    def is_scheduled(cls):
        return ~cls.is_deleted & (cls.start_dt != None)  # noqa

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id), True)

    @property
    def locator(self):
        return dict(self.event.getLocator(), reg_form_id=self.id)

    @property
    def active_fields(self):
        return [field
                for field in self.form_items
                if (field.is_field and
                    field.is_enabled and not field.is_deleted and
                    field.parent.is_enabled and not field.parent.is_deleted)]

    @property
    def sections(self):
        return [x for x in self.form_items if x.is_section]

    @property
    def limit_reached(self):
        return self.registration_limit and len(self.registrations) >= self.registration_limit

    @property
    def is_active(self):
        return self.is_open and not self.limit_reached

    @return_ascii
    def __repr__(self):
        return '<RegistrationForm({}, {}, {})>'.format(self.id, self.event_id, self.title)

    def is_modification_allowed(self, registration):
        if self.modification_mode == ModificationMode.allowed_always:
            return True
        elif self.modification_mode == ModificationMode.allowed_until_payment:
            return registration.transaction is None
        else:
            return False

    def can_submit(self, user):
        return self.is_active and (not self.require_login or user)

    @memoize_request
    def get_registration(self, user=None, uuid=None, email=None):
        """Retrieves registrations for this registration form by user or uuid"""
        if (bool(user) + bool(uuid) + bool(email)) != 1:
            raise ValueError("Exactly one of `user`, `uuid` and `email` must be specified")
        if user:
            return (user.registrations
                    .filter_by(registration_form=self)
                    .filter(~Registration.is_cancelled, ~Registration.is_deleted)
                    .first())
        if uuid:
            return (Registration.query
                    .with_parent(self)
                    .filter_by(uuid=uuid)
                    .filter(~Registration.is_cancelled, ~Registration.is_deleted)
                    .first())
        if email:
            return (Registration.query
                    .with_parent(self)
                    .filter_by(email=email)
                    .filter(~Registration.is_cancelled, ~Registration.is_deleted)
                    .first())
