# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import uuid

from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector
from authlib.oauth2.rfc6749 import InvalidScopeError, grants, scope_to_list
from authlib.oauth2.rfc6749.util import list_to_scope
from authlib.oauth2.rfc6750 import BearerTokenValidator
from authlib.oauth2.rfc7636 import CodeChallenge
from flask.ctx import after_this_request
from sqlalchemy.orm import joinedload

from indico.core.cache import make_scoped_cache
from indico.core.db import db
from indico.modules.oauth import logger
from indico.modules.oauth.models.applications import SCOPES, OAuthApplication
from indico.modules.oauth.models.tokens import OAuth2AuthorizationCode, OAuthToken
from indico.modules.users import User
from indico.util.date_time import now_utc


auth_code_store = make_scoped_cache('oauth-grant-tokens')


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_basic', 'client_secret_post', 'none']

    def save_authorization_code(self, code, request):
        code_challenge = request.data.get('code_challenge')
        code_challenge_method = request.data.get('code_challenge_method')
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=request.client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.id,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        auth_code_store.add(code, auth_code, 3600)
        return auth_code

    def query_authorization_code(self, code, client):
        auth_code = auth_code_store.get(code)
        if auth_code and auth_code.client_id == client.client_id and not auth_code.is_expired():
            return auth_code

    def delete_authorization_code(self, authorization_code):
        auth_code_store.delete(authorization_code.code)

    def authenticate_user(self, authorization_code):
        return User.get(authorization_code.user_id, is_deleted=False)

    def validate_requested_scope(self):
        """Validate if requested scope is supported by Authorization Server."""
        scope = self.request.scope
        state = self.request.state
        if scope:
            allowed = set(scope_to_list(self.request.client.get_allowed_scope(scope)))
            requested = set(scope_to_list(scope))
            if not (requested <= allowed):
                raise InvalidScopeError(state=state)
        return self.server.validate_requested_scope(scope, state)


def _query_client(client_id):
    return OAuthApplication.query.filter_by(client_id=client_id, is_enabled=True).first()


def _save_token(token_data, request):
    requested_scopes = set(scope_to_list(token_data.get('scope', '')))
    token = (OAuthToken.query
             .filter(OAuthApplication.client_id == request.client.client_id,
                     OAuthToken.user == request.user)
             .join(OAuthApplication)
             .first())
    if token is None:
        application = OAuthApplication.query.filter_by(client_id=request.client.client_id).one()
        token = OAuthToken(application=application, user=request.user, access_token=token_data['access_token'],
                           scopes=requested_scopes)
        db.session.add(token)
    elif requested_scopes - token.scopes:
        logger.info('Added scopes to %s: %s', token, requested_scopes - token.scopes)
        # use the new access_token when extending scopes
        token.access_token = token_data['access_token']
        token.scopes |= requested_scopes
        token_data['scope'] = list_to_scope(token.scopes)
    else:
        # XXX is mutating the token data really a good idea? :/
        token_data['access_token'] = token.access_token
        token_data['scope'] = list_to_scope(token.scopes)


authorization = AuthorizationServer(query_client=_query_client, save_token=_save_token)
require_oauth = ResourceProtector()


class _BearerTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string):
        try:
            uuid.UUID(hex=token_string)
        except ValueError:
            return None
        return (OAuthToken.query
                .filter_by(access_token=token_string)
                .options(joinedload('user'), joinedload('application'))
                .first())

    def validate_token(self, token, scopes):
        super().validate_token(token, scopes)

        # if we get here, the token is valid so we can mark it as used at the end of the request

        # XXX: should we wait or do it just now? even if the request failed for some reason, the
        # token could be considered used, since it was valid and most likely used by a client who
        # expected to do something with it...

        token_id = token.id  # avoid DetachedInstanceError in the callback

        @after_this_request
        def _update_last_use(response):
            with db.tmp_session() as sess:
                # do not modify `token` directly, it's attached to a different session!
                sess.query(OAuthToken).filter_by(id=token_id).update({OAuthToken.last_used_dt: now_utc()})
                sess.commit()
            return response


def setup_oauth_provider(app):
    app.config.update({
        'OAUTH2_SCOPES_SUPPORTED': list(SCOPES),
        'OAUTH2_ACCESS_TOKEN_GENERATOR': lambda *args, **kw: str(uuid.uuid4()),
        'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
        'OAUTH2_TOKEN_EXPIRES_IN': {
            'authorization_code': 0,
        }
    })
    authorization.init_app(app)
    authorization.register_grant(AuthorizationCodeGrant, [CodeChallenge(required=True)])
    require_oauth.register_token_validator(_BearerTokenValidator())
