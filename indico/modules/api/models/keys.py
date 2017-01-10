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

from sqlalchemy.dialects.postgresql import UUID, INET

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class APIKey(db.Model):
    """API keys for users"""
    __tablename__ = 'api_keys'
    __table_args__ = (db.Index(None, 'user_id', unique=True, postgresql_where=db.text('is_active')),
                      {'schema': 'users'})

    #: api key id
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: unique api key for a user
    token = db.Column(
        UUID,
        nullable=False,
        unique=True,
        default=lambda: unicode(uuid4())
    )
    #: secret key used for signed requests
    secret = db.Column(
        UUID,
        nullable=False,
        default=lambda: unicode(uuid4())
    )
    #: ID of the user associated with the key
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True,
    )
    #: if the key is the currently active key for the user
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: if the key has been blocked by an admin
    is_blocked = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: if persistent signatures are allowed
    is_persistent_allowed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: the time when the key has been created
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    #: the last time when the key has been used
    last_used_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: the last ip address from which the key has been used
    last_used_ip = db.Column(
        INET,
        nullable=True
    )
    #: the last URI this key was used with
    last_used_uri = db.Column(
        db.String,
        nullable=True
    )
    #: if the last use was from an authenticated request
    last_used_auth = db.Column(
        db.Boolean,
        nullable=True
    )
    #: the number of times the key has been used
    use_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    #: the user associated with this API key
    user = db.relationship(
        'User',
        lazy=False
    )

    @return_ascii
    def __repr__(self):
        return '<APIKey({}, {}, {})>'.format(self.token, self.user_id, self.last_used_dt or 'never')

    def register_used(self, ip, uri, authenticated):
        """Updates the last used information"""
        self.last_used_dt = now_utc()
        self.last_used_ip = ip
        self.last_used_uri = uri
        self.last_used_auth = authenticated
        self.use_count = APIKey.use_count + 1
