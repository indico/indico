# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

from authlib.oauth2.rfc6749 import ClientMixin, list_to_scope, scope_to_list
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.urls import url_parse

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.oauth.logger import logger
from indico.util.enum import IndicoEnum


class SystemAppType(int, IndicoEnum):
    none = 0
    checkin = 1

    __enforced_data__ = {
        checkin: {'allowed_scopes': {'registrants'},
                  'redirect_uris': ['http://localhost'],
                  'allow_pkce_flow': True,
                  'is_enabled': True},
    }

    __default_data__ = {
        checkin: {'is_trusted': True,
                  'name': 'Checkin App',
                  'description': 'The checkin app for mobile devices allows scanning ticket QR codes and '
                                 'checking-in event participants.'},
    }

    @property
    def enforced_data(self):
        return self.__enforced_data__.get(self, {})

    @property
    def default_data(self):
        return dict(self.__default_data__.get(self, {}), **self.enforced_data)


class OAuthApplication(ClientMixin, db.Model):
    """OAuth applications registered in Indico."""

    __tablename__ = 'applications'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_applications_name_lower', db.func.lower(cls.name), unique=True),
                db.Index(None, cls.system_app_type, unique=True,
                         postgresql_where=db.text(f'system_app_type != {SystemAppType.none.value}')),
                {'schema': 'oauth'})

    #: the unique id of the application
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
        db.Text,
        nullable=False,
        default=''
    )
    #: the OAuth client_id
    client_id = db.Column(
        UUID,
        unique=True,
        nullable=False,
        default=lambda: str(uuid4())
    )
    #: the OAuth client_secret
    client_secret = db.Column(
        UUID,
        nullable=False,
        default=lambda: str(uuid4())
    )
    #: the OAuth scopes the application may request access to
    allowed_scopes = db.Column(
        ARRAY(db.String),
        nullable=False
    )
    #: the OAuth absolute URIs that a application may use to redirect to after authorization
    redirect_uris = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    #: whether the application is enabled or disabled
    is_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: whether the application can access user data without asking for permission
    is_trusted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: whether the application can use the PKCE flow without a client secret
    allow_pkce_flow = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: the type of system app (if any). system apps cannot be deleted
    system_app_type = db.Column(
        PyIntEnum(SystemAppType),
        nullable=False,
        default=SystemAppType.none
    )

    # relationship backrefs:
    # - user_links (OAuthApplicationUserLink.application)

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0] if self.redirect_uris else None

    @property
    def locator(self):
        return {'id': self.id}

    def __repr__(self):  # pragma: no cover
        return f'<OAuthApplication({self.id}, {self.name}, {self.client_id})>'

    def reset_client_secret(self):
        self.client_secret = str(uuid4())
        logger.info('Client secret for %s has been reset.', self)

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.default_redirect_uri

    def get_allowed_scope(self, scope):
        if not scope:
            return ''
        allowed = set(self.allowed_scopes)
        scopes = set(scope_to_list(scope))
        return list_to_scope(allowed & scopes)

    def check_redirect_uri(self, redirect_uri):
        """Called by authlib to validate the redirect_uri.

        Uses a logic similar to the one at GitHub, i.e. protocol and
        host/port must match exactly and if there is a path in the
        whitelisted URL, the path of the redirect_uri must start with
        that path.
        """
        # TODO: maybe use a stricter implementation that does not use substrings?
        uri_data = url_parse(redirect_uri)
        for valid_uri_data in map(url_parse, self.redirect_uris):
            if (uri_data.scheme == valid_uri_data.scheme and uri_data.netloc == valid_uri_data.netloc and
                    uri_data.path.startswith(valid_uri_data.path)):
                return True
        return False

    def check_client_secret(self, client_secret):
        return self.client_secret == client_secret

    def check_endpoint_auth_method(self, method, endpoint):
        from indico.core.oauth.endpoints import IndicoIntrospectionEndpoint, IndicoRevocationEndpoint
        from indico.core.oauth.grants import IndicoAuthorizationCodeGrant

        if endpoint == 'token':
            if method == 'none' and not self.allow_pkce_flow:
                return False
            return method in IndicoAuthorizationCodeGrant.TOKEN_ENDPOINT_AUTH_METHODS
        elif endpoint == 'introspection':
            return method in IndicoIntrospectionEndpoint.CLIENT_AUTH_METHODS
        elif endpoint == 'revocation':
            return method in IndicoRevocationEndpoint.CLIENT_AUTH_METHODS

        # authlib returns True for unhandled cases, but since we do not have any other endpoints
        # I'd rather fail and implement other cases as needed instead of silently accepting
        # everything
        raise NotImplementedError

    def check_response_type(self, response_type):
        # We no longer allow the implicit flow, so `code` is all we need
        return response_type == 'code'

    def check_grant_type(self, grant_type):
        return grant_type == 'authorization_code'


class OAuthApplicationUserLink(db.Model):
    """The authorization link between an OAuth app and a user."""

    __tablename__ = 'application_user_links'
    __table_args__ = (db.UniqueConstraint('application_id', 'user_id'),
                      {'schema': 'oauth'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    application_id = db.Column(
        db.Integer,
        db.ForeignKey('oauth.applications.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    scopes = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )

    application = db.relationship(
        'OAuthApplication',
        lazy=False,
        backref=db.backref(
            'user_links',
            lazy='dynamic',
            cascade='all, delete-orphan',
            passive_deletes=True
        )
    )
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'oauth_app_links',
            lazy='dynamic',
            cascade='all, delete-orphan',
            passive_deletes=True
        )
    )

    # relationship backrefs:
    # - tokens (OAuthToken.app_user_link)

    def __repr__(self):
        return f'<OAuthApplicationUserLink({self.application_id}, {self.user_id}, {self.scopes})>'

    def update_scopes(self, scopes: set):
        self.scopes = sorted(set(self.scopes) | scopes)
