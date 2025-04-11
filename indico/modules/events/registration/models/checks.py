# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.custom.int_enum import PyIntEnum
from indico.util.date_time import now_utc
from indico.util.enum import RichIntEnum
from indico.util.i18n import L_
from indico.util.locators import locator_property
from indico.util.string import format_repr


class CheckType(RichIntEnum):
    __titles__ = [None, L_('Checked in'), L_('Checked out')]
    check_in = 1
    check_out = 2


class RegistrationCheckRule(RichIntEnum):
    __titles__ = [None, L_('Once'), L_('Multiple'), L_('Once daily')]

    once = 1
    multiple = 2
    once_daily = 3


class RegistrationCheckType(db.Model):
    """Checks to be performed on registrations."""

    __tablename__ = 'check_types'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_check_types_title_lower', cls.event_id, db.func.lower(cls.title), unique=True),
                db.CheckConstraint('((is_system_defined = true AND event_id IS NULL) '
                                   'OR (is_system_defined = false AND event_id IS NOT NULL))',
                                   'valid_is_system_defined'),
                {'schema': 'event_registration'})

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event where this check was created
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
    )
    #: The name of the check
    title = db.Column(
        db.String,
        nullable=False
    )
    #: The associated `RegistrationCheckRule`
    rule = db.Column(
        PyIntEnum(RegistrationCheckRule),
        default=RegistrationCheckRule.once,
        nullable=False
    )
    #: If this is a system defined check type
    is_system_defined = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: If this check can be checked-out
    check_out_allowed = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: The Event where this rule was created
    event = db.relationship(
        'Event',
        lazy=True,
        foreign_keys=event_id,
        backref=db.backref(
            'check_types',
            lazy=True,
            cascade='all, delete-orphan',
        )
    )

    # relationship backrefs:
    # - default_check_type_of (Event.default_check_type)
    # - registration_checks (RegistrationCheck.check_type)

    @property
    def locator(self):
        if self.event:
            return dict(self.event.locator, check_type_id=self.id)
        else:
            return {'check_type_id': self.id}

    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)


class RegistrationCheck(db.Model):
    """Stores the histroy of checks performed on registrations."""

    __tablename__ = 'checks'
    __table_args__ = {'schema': 'event_registration'}

    #: The ID of the check
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the registration
    registration_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registrations.id'),
        index=True,
        nullable=False
    )
    #: Type of the check
    check_type_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.check_types.id'),
        index=True,
        nullable=False
    )
    #: The date/time of the check
    timestamp = db.Column(
        UTCDateTime,
        nullable=False,
        index=True,
        default=now_utc
    )
    #: If this is a checkin/checkout
    is_check_out = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The ID of the user who performed the check
    checked_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True
    )
    #: The associated registration
    registration = db.relationship(
        'Registration',
        lazy=True,
        backref=db.backref(
            'checks',
            cascade='all, delete-orphan',
            lazy=True,
        )
    )
    #: The associated RegistrationCheckType
    check_type = db.relationship(
        'RegistrationCheckType',
        lazy=True,
        backref=db.backref(
            'registration_checks',
            cascade='all, delete-orphan',
            lazy=True,
        )
    )
    #: The user who performed the check
    checked_by_user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'registration_checks_performed',
            lazy=True,
        )
    )

    @locator_property
    def locator(self):
        return dict(self.registration.locator, check_id=self.id)

    def __repr__(self):
        return format_repr(self, 'id', 'registration_id', 'timestamp',
                           _text=f'{"Check-out" if self.is_check_out else "Check-in"} - {self.check_type.title}')
