# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.exceptions import ServiceUnavailable

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import RichIntEnum


class AgreementState(RichIntEnum):
    __titles__ = [_("Pending"), _("Accepted"), _("Rejected"), _("Accepted on behalf"), _("Rejected on behalf")]
    pending = 0
    accepted = 1
    rejected = 2
    #: agreement accepted on behalf of the person
    accepted_on_behalf = 3
    #: agreement rejected on behalf of the person
    rejected_on_behalf = 4


class Agreement(db.Model):
    """Agreements between a person and Indico."""
    __tablename__ = 'agreements'
    __table_args__ = (db.UniqueConstraint('event_id', 'type', 'identifier'),
                      {'schema': 'events'})

    #: Entry ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: Entry universally unique ID
    uuid = db.Column(
        db.String,
        nullable=False
    )
    #: ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )
    #: Type of agreement
    type = db.Column(
        db.String,
        nullable=False
    )
    #: Unique identifier within the event and type
    identifier = db.Column(
        db.String,
        nullable=False
    )
    #: Email of the person agreeing
    person_email = db.Column(
        db.String,
        nullable=True
    )
    #: Full name of the person agreeing
    person_name = db.Column(
        db.String,
        nullable=False
    )
    #: A :class:`AgreementState`
    state = db.Column(
        PyIntEnum(AgreementState),
        default=AgreementState.pending,
        nullable=False
    )
    #: The date and time the agreement was created
    timestamp = db.Column(
        UTCDateTime,
        default=now_utc,
        nullable=False
    )
    #: ID of a linked user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    #: The date and time the agreement was signed
    signed_dt = db.Column(
        UTCDateTime
    )
    #: The IP from which the agreement was signed
    signed_from_ip = db.Column(
        db.String
    )
    #: Explanation as to why the agreement was accepted/rejected
    reason = db.Column(
        db.String
    )
    #: Attachment
    attachment = db.deferred(db.Column(
        db.LargeBinary
    ))
    #: Filename and extension of the attachment
    attachment_filename = db.Column(
        db.String
    )
    #: Definition-specific data of the agreement
    data = db.Column(
        JSONB
    )

    #: The user this agreement is linked to
    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'agreements',
            lazy='dynamic'
        )
    )
    #: The Event this agreement is associated with
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'agreements',
            lazy='dynamic'
        )
    )

    @hybrid_property
    def accepted(self):
        return self.state in {AgreementState.accepted, AgreementState.accepted_on_behalf}

    @accepted.expression
    def accepted(self):
        return self.state.in_((AgreementState.accepted, AgreementState.accepted_on_behalf))

    @hybrid_property
    def pending(self):
        return self.state == AgreementState.pending

    @hybrid_property
    def rejected(self):
        return self.state in {AgreementState.rejected, AgreementState.rejected_on_behalf}

    @rejected.expression
    def rejected(self):
        return self.state.in_((AgreementState.rejected, AgreementState.rejected_on_behalf))

    @hybrid_property
    def signed_on_behalf(self):
        return self.state in {AgreementState.accepted_on_behalf, AgreementState.rejected_on_behalf}

    @signed_on_behalf.expression
    def signed_on_behalf(self):
        return self.state.in_((AgreementState.accepted_on_behalf, AgreementState.rejected_on_behalf))

    @property
    def definition(self):
        from indico.modules.events.agreements.util import get_agreement_definitions
        return get_agreement_definitions().get(self.type)

    @property
    def locator(self):
        return {'confId': self.event_id,
                'id': self.id}

    @return_ascii
    def __repr__(self):
        state = self.state.name if self.state is not None else None
        return '<Agreement({}, {}, {}, {}, {}, {})>'.format(self.id, self.event_id, self.type, self.identifier,
                                                            self.person_email, state)

    @staticmethod
    def create_from_data(event, type_, person):
        agreement = Agreement(event=event, type=type_, state=AgreementState.pending, uuid=str(uuid4()))
        agreement.identifier = person.identifier
        agreement.person_email = person.email
        agreement.person_name = person.name
        if person.user:
            agreement.user = person.user
        agreement.data = person.data
        return agreement

    def accept(self, from_ip, reason=None, on_behalf=False):
        self.state = AgreementState.accepted if not on_behalf else AgreementState.accepted_on_behalf
        self.signed_from_ip = from_ip
        self.reason = reason
        self.signed_dt = now_utc()
        self.definition.handle_accepted(self)

    def reject(self, from_ip, reason=None, on_behalf=False):
        self.state = AgreementState.rejected if not on_behalf else AgreementState.rejected_on_behalf
        self.signed_from_ip = from_ip
        self.reason = reason
        self.signed_dt = now_utc()
        self.definition.handle_rejected(self)

    def reset(self):
        self.definition.handle_reset(self)
        self.state = AgreementState.pending
        self.attachment = None
        self.attachment_filename = None
        self.reason = None
        self.signed_dt = None
        self.signed_from_ip = None

    def render(self, form, **kwargs):
        definition = self.definition
        if definition is None:
            raise ServiceUnavailable('This agreement type is currently not available.')
        return definition.render_form(self, form, **kwargs)

    def belongs_to(self, person):
        return self.identifier == person.identifier

    def is_orphan(self):
        definition = self.definition
        if definition is None:
            raise ServiceUnavailable('This agreement type is currently not available.')
        return definition.is_agreement_orphan(self.event, self)
