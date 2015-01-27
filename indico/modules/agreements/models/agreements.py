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

from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.struct.enum import IndicoEnum


class AgreementState(int, IndicoEnum):
    pending = 1
    accepted = 2
    rejected = 3
    #: agreement accepted on behalf of the person
    accepted_on_behalf = 4
    #: agreement rejected on behalf of the person
    rejected_on_behalf = 5


class Agreement(db.Model):
    """Agreements between a person and Indico"""
    __tablename__ = 'agreements'
    __table_args__ = (db.UniqueConstraint('event_id', 'type', 'person_email'),
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
    #: Attachment
    attachment = db.Column(
        db.LargeBinary,
        nullable=True
    )

    @hybrid_property
    def accepted(self):
        return self.state == AgreementState.accepted or self.state == AgreementState.accepted_on_behalf

    @accepted.expression
    def accepted(self):
        return (self.state == AgreementState.accepted) | (self.state == AgreementState.accepted_on_behalf)

    @hybrid_property
    def pending(self):
        return self.state == AgreementState.pending

    @hybrid_property
    def rejected(self):
        return self.state == AgreementState.rejected or self.state == AgreementState.rejected_on_behalf

    @rejected.expression
    def rejected(self):
        return (self.state == AgreementState.rejected) | (self.state == AgreementState.rejected_on_behalf)

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id))

    @property
    def user(self):
        if not self.user_id:
            return None
        from MaKaC.user import AvatarHolder
        return AvatarHolder().getById(str(self.user_id))

    def __repr__(self):
        state = self.state.name if self.state is not None else None
        return '<Agreement({}, {}, {}, {}, {})>'.format(self.id, self.event_id, self.type, state, self.person_email)
