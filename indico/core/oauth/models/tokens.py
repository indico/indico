# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from authlib.oauth2.rfc6749 import list_to_scope
from authlib.oauth2.rfc6749.models import AuthorizationCodeMixin, TokenMixin
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc


class OAuthToken(TokenMixin, db.Model):
    """OAuth tokens."""

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

    def __repr__(self):  # pragma: no cover
        return f'<OAuthToken({self.id}, {self.application}, {self.user})>'

    def check_client(self, client):
        return self.application == client

    def get_scope(self):
        return list_to_scope(sorted(self.scopes & set(self.application.allowed_scopes)))

    def get_expires_in(self):
        return 0

    def is_expired(self):
        return False

    def is_revoked(self):
        return self.user.is_blocked or self.user.is_deleted or not self.application.is_enabled


@dataclass(frozen=True)
class OAuth2AuthorizationCode(AuthorizationCodeMixin):
    code: str
    user_id: int
    client_id: str
    code_challenge: str
    code_challenge_method: str
    redirect_uri: str = ''
    scope: str = ''
    auth_time: datetime = field(default_factory=now_utc)

    def is_expired(self):
        return now_utc() - self.auth_time > timedelta(minutes=5)

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_scope(self):
        return self.scope

    def get_auth_time(self):
        return self.auth_time

    def get_nonce(self):
        # our grant types do not require nonces
        raise NotImplementedError
