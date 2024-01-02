# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib
from uuid import UUID

from authlib.oauth2.rfc6749 import list_to_scope, scope_to_list
from sqlalchemy.dialects.postgresql.array import ARRAY
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.oauth.logger import logger
from indico.core.oauth.models.applications import OAuthApplication, OAuthApplicationUserLink
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.core.oauth.models.tokens import OAuthToken


# The maximum number of tokens to keep for any given app/user and scope combination
MAX_TOKENS_PER_SCOPE = 50
# The prefix for OAuth tokens
TOKEN_PREFIX_OAUTH = 'indo_'  # noqa: S105
# The prefix for personal tokens
TOKEN_PREFIX_PERSONAL = 'indp_'  # noqa: S105
# The prefix for service tokens (not handled by this module)
TOKEN_PREFIX_SERVICE = 'inds_'  # noqa: S105


def query_token(token_string, allow_personal=False):
    token_hash = hashlib.sha256(token_string.encode()).hexdigest()

    if token_string.startswith(TOKEN_PREFIX_PERSONAL):
        if not allow_personal:
            return None
        return (PersonalToken.query
                .filter_by(access_token_hash=token_hash)
                .first())

    # XXX: oauth tokens may be from pre-3.0 and thus not use a token prefix, so we simply
    # assume that any token without another known prefix is an oauth token

    # we always need the app link (which already loads the application) and the user
    # since we need those to check if the token is still valid
    return (OAuthToken.query
            .filter_by(access_token_hash=token_hash)
            .options(joinedload('app_user_link').joinedload('user'))
            .first())


def query_client(client_id):
    try:
        UUID(hex=client_id)
    except ValueError:
        return None
    return OAuthApplication.query.filter_by(client_id=client_id, is_enabled=True).first()


def save_token(token_data, request):
    requested_scopes = set(scope_to_list(token_data.get('scope', '')))
    application = OAuthApplication.query.filter_by(client_id=request.client.client_id).one()
    link = OAuthApplicationUserLink.query.with_parent(application).with_parent(request.user).first()

    if link is None:
        link = OAuthApplicationUserLink(application=application, user=request.user, scopes=requested_scopes)
    else:
        if not requested_scopes:
            # for already-authorized apps not specifying a scope uses all scopes the
            # user previously granted to the app
            requested_scopes = set(link.scopes)
            token_data['scope'] = list_to_scope(requested_scopes)
        new_scopes = requested_scopes - set(link.scopes)
        if new_scopes:
            logger.info('New scopes for %r: %s', link, new_scopes)
            link.update_scopes(new_scopes)

    link.tokens.append(OAuthToken(access_token=token_data['access_token'], scopes=requested_scopes))

    # get rid of old tokens if there are too many
    q = (db.session.query(OAuthToken.id)
         .with_parent(link)
         .filter_by(_scopes=db.cast(sorted(requested_scopes), ARRAY(db.String)))
         .order_by(OAuthToken.created_dt.desc())
         .offset(MAX_TOKENS_PER_SCOPE)
         .scalar_subquery())
    OAuthToken.query.filter(OAuthToken.id.in_(q)).delete(synchronize_session='fetch')
