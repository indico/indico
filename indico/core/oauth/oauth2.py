# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from authlib.common.security import generate_token
from authlib.integrations.flask_oauth2 import AuthorizationServer

from indico.core.oauth.endpoints import IndicoIntrospectionEndpoint, IndicoRevocationEndpoint
from indico.core.oauth.grants import IndicoAuthorizationCodeGrant, IndicoCodeChallenge
from indico.core.oauth.protector import IndicoAuthlibHTTPError, IndicoBearerTokenValidator, IndicoResourceProtector
from indico.core.oauth.scopes import SCOPES
from indico.core.oauth.util import TOKEN_PREFIX_OAUTH, query_client, save_token


auth_server = AuthorizationServer(query_client=query_client, save_token=save_token)
require_oauth = IndicoResourceProtector()


def setup_oauth_provider(app):
    app.config.update({
        'OAUTH2_SCOPES_SUPPORTED': list(SCOPES),
        'OAUTH2_ACCESS_TOKEN_GENERATOR': lambda *args, **kw: TOKEN_PREFIX_OAUTH + generate_token(42),
        'OAUTH2_TOKEN_EXPIRES_IN': {
            'authorization_code': 0,
        }
    })
    app.register_error_handler(IndicoAuthlibHTTPError, lambda exc: exc.get_response())
    auth_server.init_app(app)
    auth_server.register_grant(IndicoAuthorizationCodeGrant, [IndicoCodeChallenge(required=True)])
    auth_server.register_endpoint(IndicoIntrospectionEndpoint)
    auth_server.register_endpoint(IndicoRevocationEndpoint)
    require_oauth.register_token_validator(IndicoBearerTokenValidator())
