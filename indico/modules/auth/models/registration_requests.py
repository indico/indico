# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import ARRAY, JSON

from indico.core.db import db
from indico.util.locators import locator_property
from indico.util.string import return_ascii, format_repr


class RegistrationRequest(db.Model):
    __tablename__ = 'registration_requests'
    __table_args__ = (
        db.CheckConstraint('email = lower(email)', 'lowercase_email'),
        {'schema': 'users'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    comment = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    email = db.Column(
        db.String,
        unique=True,
        nullable=False,
        index=True
    )
    extra_emails = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    user_data = db.Column(
        JSON,
        nullable=False
    )
    identity_data = db.Column(
        JSON,
        nullable=False
    )
    settings = db.Column(
        JSON,
        nullable=False
    )

    @locator_property
    def locator(self):
        return {'request_id': self.id}

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'email')
