# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from authlib.oauth2.rfc6749 import InvalidScopeError, scope_to_list
from authlib.oauth2.rfc6749.grants import AuthorizationCodeGrant
from authlib.oauth2.rfc7636.challenge import CodeChallenge

from indico.core.cache import make_scoped_cache
from indico.core.oauth.models.tokens import OAuth2AuthorizationCode
from indico.modules.users import User


auth_code_store = make_scoped_cache('oauth-grant-tokens')


class IndicoAuthorizationCodeGrant(AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ('client_secret_basic', 'client_secret_post', 'none')

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


class IndicoCodeChallenge(CodeChallenge):
    SUPPORTED_CODE_CHALLENGE_METHOD = ('S256',)
