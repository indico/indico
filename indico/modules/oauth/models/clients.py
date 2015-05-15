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

from indico.core.db import db


class OAuthClient(db.Model):
    """OAuth clients registered in Indico"""

    __tablename__ = 'clients'
    __table_args__ = ({'schema': 'oauth'})

    #: the unique id of the client
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: human readable name
    name = db.Column(
        db.String,
        nullable=False
    )
    #: human readable description
    description = db.Column(
        db.Text
    )
    #: identifier issued to the client during the registration process
    client_id = db.Column(
        db.String,
        unique=True,
        nullable=False,
    )
    #: the client secret
    client_secret = db.Column(
        db.String,
        unique=True,
        nullable=False
    )
    #: whether the client is confidential or public
    is_confidential = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: whether the client is enabled or disabled
    is_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: whether the client can access user data without asking for permission
    is_trusted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: default scopes the client may request access to
    _default_scopes = db.Column(db.Text)
    #: absolute URIs that a client may use to redirect to after authorization
    _redirect_uris = db.Column(db.Text)

    @property
    def client_type(self):
        return 'confidential' if self.is_confidential else 'public'

    @property
    def default_redirect_uri(self):
        if self.redirect_uris:
            return self._default_redirect_uri[0]
        return None

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []        

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._default_redirect_uris.split()
        return []

    def __repr__(self):
        return '<OAuthClient({}, {}, {})>'.format(self.id, self.name, self.client_id)
