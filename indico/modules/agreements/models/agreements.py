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

from collections import namedtuple
from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.i18n import _
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum


class AgreementPersonInfo(namedtuple('Person', ('name', 'email', 'user', 'data'))):
    __slots__ = ()

    def __new__(cls, name=None, email=None, user=None, data=None):
        if user:
            if not name:
                name = user.getStraightFullName()
            if not email:
                email = user.getEmail()
        if not name:
            raise ValueError('name is missing')
        if not email:
            raise ValueError('email is missing')
        return super(AgreementPersonInfo, cls).__new__(cls, name, email, user, data)


class AgreementState(TitledIntEnum):
    __titles__ = [_("Pending"), _("Accepted"), _("Rejected"), _("Accepted on behalf"), _("Rejected on behalf")]
    pending = 0
    accepted = 1
    rejected = 2
    #: agreement accepted on behalf of the person
    accepted_on_behalf = 3
    #: agreement rejected on behalf of the person
    rejected_on_behalf = 4


class Agreement(db.Model):
    """Agreements between a person and Indico"""
    __tablename__ = 'agreements'
    __table_args__ = {'schema': 'events'}

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
        index=True,
        nullable=False
    )
    #: Type of agreement
    type = db.Column(
        db.String,
        nullable=False
    )
    #: Email of the person agreeing
    person_email = db.Column(
        db.String,
        nullable=False
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
        index=True
    )
    #: The date and time the agreement was signed
    signed_dt = db.Column(
        UTCDateTime,
        index=True
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
    attachment = db.Column(
        db.LargeBinary
    )
    #: Filename and extension of the attachment
    attachment_filename = db.Column(
        db.String
    )
    #: Definition-specific data of the agreement
    data = db.Column(
        JSON
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

    @property
    def definition(self):
        from indico.modules.agreements.util import get_agreement_definitions
        return get_agreement_definitions().get(self.type)

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id))

    @property
    def locator(self):
        return {'confId': self.event_id,
                'id': self.id}

    @property
    def user(self):
        if self.user_id is None:
            return None
        from MaKaC.user import AvatarHolder
        return AvatarHolder().getById(str(self.user_id))

    @user.setter
    def user(self, user):
        if user is None:
            return
        self.user_id = user.getId()

    @return_ascii
    def __repr__(self):
        state = self.state.name if self.state is not None else None
        return '<Agreement({}, {}, {}, {}, {})>'.format(self.id, self.event_id, self.type, self.person_email, state)

    @staticmethod
    def create_from_data(event_id, type, person):
        agreement = Agreement(event_id=event_id, type=type, state=AgreementState.pending, uuid=str(uuid4()))
        agreement.person_email = person.email
        agreement.person_name = person.name
        if person.user:
            agreement.user = person.user
        return agreement

    def accept(self, on_behalf=False):
        self.state = AgreementState.accepted if not on_behalf else AgreementState.accepted_on_behalf
        self.signed_dt = now_utc()
        self.definition.handle_accepted(self)

    def reject(self, on_behalf=False):
        self.state = AgreementState.rejected if not on_behalf else AgreementState.rejected_on_behalf
        self.signed_dt = now_utc()
        self.definition.handle_rejected(self)

    def reset(self):
        self.definition.handle_reset(self)
        self.state = AgreementState.pending
        self.attachment = None
        self.attachment_filename = None
        self.data = None
        self.reason = None
        self.signed_dt = None
        self.signed_from_ip = None

    def render(self, form, **kwargs):
        return self.definition.render_form(self, form, **kwargs)
