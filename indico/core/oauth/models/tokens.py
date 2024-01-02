# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from authlib.oauth2.rfc6749 import list_to_scope
from authlib.oauth2.rfc6749.models import AuthorizationCodeMixin, TokenMixin
from sqlalchemy.dialects.postgresql import ARRAY, INET

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.passwords import TokenProperty


class TokenModelBase(TokenMixin, db.Model):
    __abstract__ = True

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    access_token_hash = db.Column(
        db.String,
        unique=True,
        index=True,
        nullable=False
    )
    _scopes = db.Column(
        'scopes',
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    last_used_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    last_used_ip = db.Column(
        INET,
        nullable=True
    )
    use_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    access_token = TokenProperty('access_token_hash')

    @property
    def locator(self):
        return {'id': self.id}

    @property
    def scopes(self):
        """The set of scopes this token has access to."""
        return set(self._scopes)

    @scopes.setter
    def scopes(self, value):
        self._scopes = sorted(value)

    def get_expires_in(self):
        return 0

    def is_expired(self):
        return False


class OAuthToken(TokenModelBase):
    """OAuth tokens."""

    __tablename__ = 'tokens'
    __table_args__ = {'schema': 'oauth'}

    app_user_link_id = db.Column(
        db.ForeignKey('oauth.application_user_links.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    app_user_link = db.relationship(
        'OAuthApplicationUserLink',
        lazy=False,
        backref=db.backref(
            'tokens',
            lazy='dynamic',
            cascade='all, delete-orphan',
            passive_deletes=True
        )
    )

    @property
    def user(self):
        return self.app_user_link.user

    @property
    def application(self):
        return self.app_user_link.application

    def __repr__(self):  # pragma: no cover
        return f'<OAuthToken({self.id}, {self.app_user_link_id}, {self.scopes})>'

    def check_client(self, client):
        return self.application == client

    def get_scope(self):
        # scopes are restricted by what's authorized for the particular user and what's whitelisted for the app
        scopes = self.scopes & set(self.app_user_link.scopes) & set(self.application.allowed_scopes)
        return list_to_scope(sorted(scopes))

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
