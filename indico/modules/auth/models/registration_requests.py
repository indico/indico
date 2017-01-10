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

from sqlalchemy.dialects.postgresql import ARRAY, JSON
from werkzeug.datastructures import MultiDict

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
    _identity_data = db.Column(
        'identity_data',
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

    @property
    def identity_data(self):
        identity_data = self._identity_data.copy()
        # if we have data in identity_data, it was converted from a
        # MultiDict so we need to convert it back.
        if 'data' in identity_data:
            tmp = MultiDict()
            tmp.update(self._identity_data['data'])
            identity_data['data'] = tmp
        return identity_data

    @identity_data.setter
    def identity_data(self, identity_data):
        identity_data = identity_data.copy()
        # `identity_data['data']` for multipass-based identities is a
        # MultiDict, but json-encoding it would lose all extra values
        # for a key, so we convert it to a dict of lists first
        if 'data' in identity_data:
            identity_data['data'] = dict(identity_data['data'].lists())
        self._identity_data = identity_data

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'email')
