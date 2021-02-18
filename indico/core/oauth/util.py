# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import UUID

from authlib.oauth2.rfc6749 import scope_to_list
from authlib.oauth2.rfc6749.util import list_to_scope
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.oauth.logger import logger
from indico.core.oauth.models.applications import OAuthApplication
from indico.core.oauth.models.tokens import OAuthToken


def query_token(token_string):
    try:
        UUID(hex=token_string)
    except ValueError:
        return None
    return (OAuthToken.query
            .filter_by(access_token=token_string)
            .options(joinedload('user'), joinedload('application'))
            .first())


def query_client(client_id):
    try:
        UUID(hex=client_id)
    except ValueError:
        return None
    return OAuthApplication.query.filter_by(client_id=client_id, is_enabled=True).first()


def save_token(token_data, request):
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
