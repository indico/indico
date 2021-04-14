# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from authlib.oauth2.rfc7009 import RevocationEndpoint
from authlib.oauth2.rfc7662 import IntrospectionEndpoint

from indico.core.config import config
from indico.core.db import db
from indico.core.oauth.logger import logger
from indico.core.oauth.models.tokens import OAuthToken
from indico.core.oauth.util import query_token


class IndicoIntrospectionEndpoint(IntrospectionEndpoint):
    SUPPORTED_TOKEN_TYPES = ('access_token',)
    CLIENT_AUTH_METHODS = ('client_secret_basic', 'client_secret_post')

    def check_permission(self, token, client, request):
        return token.check_client(client)

    def query_token(self, token_string, token_type_hint):
        return query_token(token_string)

    def introspect_token(self, token: OAuthToken):
        return {
            'active': True,
            'client_id': token.application.client_id,
            'token_type': 'Bearer',
            'scope': token.get_scope(),
            'sub': str(token.user.id),
            'iss': config.BASE_URL
        }


class IndicoRevocationEndpoint(RevocationEndpoint):
    SUPPORTED_TOKEN_TYPES = ('access_token',)
    CLIENT_AUTH_METHODS = ('client_secret_basic', 'client_secret_post')

    def query_token(self, token, token_type_hint):
        return query_token(token)

    def revoke_token(self, token, request):
        db.session.delete(token)
        logger.info('Token %s was revoked', token)
