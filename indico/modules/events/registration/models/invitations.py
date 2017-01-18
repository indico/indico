# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import UUID

from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.i18n import L_
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import RichIntEnum
from indico.core.db import db


class InvitationState(RichIntEnum):
    __titles__ = [L_('Pending'), L_('Accepted'), L_('Declined')]
    pending = 0
    accepted = 1
    declined = 2


class RegistrationInvitation(db.Model):
    """An invitation for someone to register"""
    __tablename__ = 'invitations'
    __table_args__ = (db.CheckConstraint("(state = {state}) OR (registration_id IS NULL)"
                                         .format(state=InvitationState.accepted), name='registration_state'),
                      db.UniqueConstraint('registration_form_id', 'email'),
                      {'schema': 'event_registration'})

    #: The ID of the invitation
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The UUID of the invitation
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
    #: The ID of the registration (if accepted)
    registration_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registrations.id'),
        index=True,
        unique=True,
        nullable=True
    )
    #: The state of the invitation
    state = db.Column(
        PyIntEnum(InvitationState),
        nullable=False,
        default=InvitationState.pending
    )
    #: Whether registration moderation should be skipped
    skip_moderation = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The email of the invited person
    email = db.Column(
        db.String,
        nullable=False
    )
    #: The first name of the invited person
    first_name = db.Column(
        db.String,
        nullable=False
    )
    #: The last name of the invited person
    last_name = db.Column(
        db.String,
        nullable=False
    )
    #: The affiliation of the invited person
    affiliation = db.Column(
        db.String,
        nullable=False
    )

    #: The associated registration
    registration = db.relationship(
        'Registration',
        lazy=True,
        backref=db.backref(
            'invitation',
            lazy=True,
            uselist=False
        )
    )

    # relationship backrefs:
    # - registration_form (RegistrationForm.invitations)

    @locator_property
    def locator(self):
        return dict(self.registration_form.locator, invitation_id=self.id)

    @locator.uuid
    def locator(self):
        """A locator suitable for 'display' pages.

        Instead of the numeric ID it uses the UUID
        """
        assert self.uuid is not None
        return dict(self.registration_form.locator, invitation=self.uuid)

    @return_ascii
    def __repr__(self):
        full_name = '{} {}'.format(self.first_name, self.last_name)
        return format_repr(self, 'id', 'registration_form_id', 'email', 'state', _text=full_name)
