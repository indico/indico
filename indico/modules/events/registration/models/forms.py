# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from uuid import UUID

from babel.numbers import format_currency
from flask import session
from sqlalchemy import orm, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property, subqueryload
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.events.registration.models.form_fields import RegistrationFormPersonalDataField
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
from indico.util.caching import memoize_request
from indico.util.date_time import now_utc
from indico.util.i18n import L_
from indico.util.string import return_ascii
from indico.util.struct.enum import RichIntEnum


class ModificationMode(RichIntEnum):
    __titles__ = [None, L_('Until modification deadline'), L_('Until payment'), L_('Never'), L_('Until approved')]
    allowed_always = 1
    allowed_until_payment = 2
    not_allowed = 3
    allowed_until_approved = 4


class RegistrationForm(db.Model):
    """A registration form for an event."""

    __tablename__ = 'forms'
    principal_type = PrincipalType.registration_form
    principal_order = 2
    is_group = False
    is_network = False
    is_single_person = False
    is_event_role = False
    is_category_role = False
    is_registration_form = True

    __table_args__ = (db.Index('ix_uq_forms_participation', 'event_id', unique=True,
                               postgresql_where=db.text('is_participation AND NOT is_deleted')),
                      db.UniqueConstraint('id', 'event_id'),  # useless but needed for the registrations fkey
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
    #: Whether it's the 'Participants' form of a meeting/lecture
    is_participation = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
    #: Whether registrations should be displayed in the participant list
    publish_registrations_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether to display the number of registrations
    publish_registration_count = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether checked-in status should be displayed in the event pages and participant list
    publish_checkin_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether registrations must be approved by a manager
    moderation_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The base fee users have to pay when registering
    base_price = db.Column(
        db.Numeric(11, 2),  # max. 999999999.99
        nullable=False,
        default=0
    )
    #: Currency for prices in the registration form
    currency = db.Column(
        db.String,
        nullable=False
    )
    #: Notifications sender address
    notification_sender_address = db.Column(
        db.String,
        nullable=True
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
    #: The ID of the template used to generate tickets
    ticket_template_id = db.Column(
        db.Integer,
        db.ForeignKey(DesignerTemplate.id),
        nullable=True,
        index=True
    )

    #: The Event containing this registration form
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'registration_forms',
            primaryjoin='(RegistrationForm.event_id == Event.id) & ~RegistrationForm.is_deleted',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    #: The template used to generate tickets
    ticket_template = db.relationship(
        'DesignerTemplate',
        lazy=True,
        foreign_keys=ticket_template_id,
        backref=db.backref(
            'ticket_for_regforms',
            lazy=True
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

    # relationship backrefs:
    # - in_attachment_acls (AttachmentPrincipal.registration_form)
    # - in_attachment_folder_acls (AttachmentFolderPrincipal.registration_form)
    # - in_contribution_acls (ContributionPrincipal.registration_form)
    # - in_event_acls (EventPrincipal.registration_form)
    # - in_session_acls (SessionPrincipal.registration_form)

    def __contains__(self, user):
        if user is None:
            return False
        return (Registration.query.with_parent(self)
                .join(Registration.registration_form)
                .filter(Registration.user == user,
                        Registration.state.in_([RegistrationState.unpaid, RegistrationState.complete]),
                        ~Registration.is_deleted,
                        ~RegistrationForm.is_deleted)
                .has_rows())

    @property
    def identifier(self):
        return 'RegistrationForm:{}'.format(self.id)

    @hybrid_property
    def has_ended(self):
        return self.end_dt is not None and self.end_dt <= now_utc()

    @has_ended.expression
    def has_ended(cls):
        return cls.end_dt.isnot(None) & (cls.end_dt <= now_utc())

    @hybrid_property
    def has_started(self):
        return self.start_dt is not None and self.start_dt <= now_utc()

    @has_started.expression
    def has_started(cls):
        return cls.start_dt.isnot(None) & (cls.start_dt <= now_utc())

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
        return ~cls.is_deleted & cls.start_dt.isnot(None)

    @property
    def locator(self):
        return dict(self.event.locator, reg_form_id=self.id)

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
    def disabled_sections(self):
        return [x for x in self.sections if not x.is_visible and not x.is_deleted]

    @property
    def limit_reached(self):
        return self.registration_limit and len(self.active_registrations) >= self.registration_limit

    @property
    def is_active(self):
        return self.is_open and not self.limit_reached

    @property
    @memoize_request
    def active_registrations(self):
        return (Registration.query.with_parent(self)
                .filter(Registration.is_active)
                .options(subqueryload('data'))
                .all())

    @property
    def sender_address(self):
        contact_email = self.event.contact_emails[0] if self.event.contact_emails else None
        return self.notification_sender_address or contact_email

    @return_ascii
    def __repr__(self):
        return '<RegistrationForm({}, {}, {})>'.format(self.id, self.event_id, self.title)

    def is_modification_allowed(self, registration):
        """Check whether a registration may be modified."""
        if not registration.is_active:
            return False
        elif self.modification_mode == ModificationMode.allowed_always:
            return True
        elif self.modification_mode == ModificationMode.allowed_until_approved:
            return registration.state == RegistrationState.pending
        elif self.modification_mode == ModificationMode.allowed_until_payment:
            return not registration.is_paid
        else:
            return False

    def can_submit(self, user):
        return self.is_active and (not self.require_login or user)

    @memoize_request
    def get_registration(self, user=None, uuid=None, email=None):
        """Retrieve registrations for this registration form by user or uuid."""
        if (bool(user) + bool(uuid) + bool(email)) != 1:
            raise ValueError("Exactly one of `user`, `uuid` and `email` must be specified")
        if user:
            return user.registrations.filter_by(registration_form=self).filter(~Registration.is_deleted).first()
        if uuid:
            try:
                UUID(hex=uuid)
            except ValueError:
                raise BadRequest('Malformed registration token')
            return Registration.query.with_parent(self).filter_by(uuid=uuid).filter(~Registration.is_deleted).first()
        if email:
            return Registration.query.with_parent(self).filter_by(email=email).filter(~Registration.is_deleted).first()

    def render_base_price(self):
        return format_currency(self.base_price, self.currency, locale=session.lang or 'en_GB')

    def get_personal_data_field_id(self, personal_data_type):
        """Return the field id corresponding to the personal data field with the given name."""
        for field in self.active_fields:
            if (isinstance(field, RegistrationFormPersonalDataField) and
                    field.personal_data_type == personal_data_type):
                return field.id


@listens_for(orm.mapper, 'after_configured', once=True)
def _mappers_configured():
    query = (select([db.func.count(Registration.id)])
             .where((Registration.registration_form_id == RegistrationForm.id) & Registration.is_active)
             .correlate_except(Registration))
    RegistrationForm.active_registration_count = column_property(query, deferred=True)

    query = (select([db.func.count(Registration.id)])
             .where((Registration.registration_form_id == RegistrationForm.id) & ~Registration.is_deleted)
             .correlate_except(Registration))
    RegistrationForm.existing_registrations_count = column_property(query, deferred=True)
