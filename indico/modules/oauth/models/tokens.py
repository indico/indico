# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import ARRAY, UUID

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.legacy.common.cache import GenericCache
from indico.util.string import return_ascii


class OAuthToken(db.Model):
    """OAuth tokens"""

    __tablename__ = 'tokens'
    __table_args__ = (db.UniqueConstraint('application_id', 'user_id'),
                      {'schema': 'oauth'})

    #: the unique identifier of the token
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the identifier of the linked application
    application_id = db.Column(
        db.Integer,
        db.ForeignKey('oauth.applications.id'),
        nullable=False
    )
    #: the identifier of the linked user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    #: an unguessable unique string of characters
    access_token = db.Column(
        UUID,
        unique=True,
        nullable=False
    )
    #: the list of scopes the linked application has access to
    _scopes = db.Column(
        'scopes',
        ARRAY(db.String)
    )
    #: the last time the token was used by the application
    last_used_dt = db.Column(
        UTCDateTime,
        nullable=True
    )

    #: application authorized by this token
    application = db.relationship(
        'OAuthApplication',
        lazy=True,
        backref=db.backref(
            'tokens',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
    )
    #: the user who owns this token
    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'oauth_tokens',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
    )

    @property
    def locator(self):
        return {'id': self.id}

    @property
    def expires(self):
        return None

    @property
    def scopes(self):
        """The set of scopes the linked application has access to."""
        return set(self._scopes)

    @scopes.setter
    def scopes(self, value):
        self._scopes = sorted(value)

    @property
    def type(self):
        return 'bearer'

    @return_ascii
    def __repr__(self):  # pragma: no cover
        return '<OAuthToken({}, {}, {})>'.format(self.id, self.application, self.user)


class OAuthGrant(object):
    """OAuth grant token"""

    #: cache entry to store grant tokens
    _cache = GenericCache('oauth-grant-tokens')

    def __init__(self, client_id, code, redirect_uri, user, scopes, expires):
        self.client_id = client_id
        self.code = code
        self.redirect_uri = redirect_uri
        self.user = user
        self.scopes = scopes
        self.expires = expires

    @property
    def key(self):
        return self.make_key(self.client_id, self.code)

    @property
    def ttl(self):
        return self.expires - datetime.utcnow()

    @classmethod
    def get(cls, client_id, code):
        key = cls.make_key(client_id, code)
        return cls._cache.get(key)

    @classmethod
    def make_key(cls, client_id, code):
        return '{}:{}'.format(client_id, code)

    def delete(self):
        self._cache.delete(self.key)

    def save(self):
        self._cache.set(key=self.key, val=self, time=self.ttl)
