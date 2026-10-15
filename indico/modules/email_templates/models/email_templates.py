# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import Comparator, hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.logs import CategoryLogRealm, EventLogRealm
from indico.util.enum import RichIntEnum
from indico.util.i18n import L_
from indico.util.locators import locator_property
from indico.util.placeholders import replace_placeholders
from indico.util.string import format_repr


class EmailTemplateType(RichIntEnum):
    __titles__ = [None, L_('Registration'), L_('Invitation')]
    registration = 1
    invitation = 2


class RegistrationNotificationType(RichIntEnum):
    __titles__ = [None, L_('Registration Creation'), L_('Registration State Update'), L_('Registration Modification'),
                  L_('Registration Receipt Creation')]
    registration_creation = 1
    registration_state_update = 2
    registration_modification = 3
    registration_receipt_creation = 4


class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    __table_args__ = (db.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)', 'event_xor_category_id_null'),
                      {'schema': 'indico'})
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    type = db.Column(
        PyIntEnum(EmailTemplateType),
        nullable=False
    )
    notification_type = db.Column(
        PyIntEnum(RegistrationNotificationType),
        nullable=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    #: The subject of the email
    subject = db.Column(
        db.String,
        nullable=False
    )
    #: The body of the template
    body = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        nullable=True
    )
    #: Conditions need to be met to send the email
    rules = db.Column(
        JSONB,
        nullable=False,
        default=lambda: None
    )
    #: If an email template is disabled
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    category = db.relationship(
        'Category',
        lazy=True,
        foreign_keys=category_id,
        backref=db.backref(
            'email_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'email_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    @hybrid_property
    def owner(self):
        return self.event or self.category

    @owner.comparator
    def owner(cls):
        return _OwnerComparator(cls)

    @locator_property
    def locator(self):
        return dict(self.owner.locator, email_template_id=self.id)

    @property
    def log_realm(self):
        return EventLogRealm.management if self.event else CategoryLogRealm.category

    def is_default(self, obj):
        # FIXME: Might involve too many queries while listing?
        from indico.modules.email_templates.util import get_email_template
        return self == get_email_template(obj, notification_type=self.notification_type,
                                          status=self.rules.get('status') if self.rules else None)

    def get_subject(self, registration=None, invitation=None):
        if self.type == EmailTemplateType.registration:
            subject = replace_placeholders('registration-email', self.subject, regform=registration.registration_form,
                                           registration=registration)
        else:
            subject = replace_placeholders('registration-invitation-email', self.subject, invitation=invitation)
        return f'[Indico] {subject}'

    def get_body(self, registration=None, invitation=None):
        if self.type == EmailTemplateType.registration:
            return replace_placeholders('registration-email', self.body, regform=registration.registration_form,
                                        registration=registration)
        else:
            return replace_placeholders('registration-invitation-email', self.body, invitation=invitation)

    def log(self, *args, **kwargs):
        """Log with prefilled metadata for the receipt template."""
        return self.owner.log(*args, meta={'email_template_id': self.id}, **kwargs)

    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'category_id', _text=self.title)


class _OwnerComparator(Comparator):
    def __init__(self, cls):
        self.cls = cls

    def __clause_element__(self):
        # just in case
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, db.m.Event):
            return self.cls.event == other
        elif isinstance(other, db.m.Category):
            return self.cls.category == other
        else:
            raise TypeError(f'Unexpected object type {type(other)}: {other}')
