# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from datetime import datetime, timedelta
from uuid import UUID

from flask import session, after_this_request, g
from oauthlib.oauth2 import FatalClientError, InvalidClientIdError

from indico.core.db import db
from indico.core.config import Config
from indico.modules.oauth import oauth, logger
from indico.modules.oauth.models.applications import OAuthApplication
from indico.modules.oauth.models.tokens import OAuthGrant, OAuthToken
from indico.util.date_time import now_utc


class DisabledClientIdError(FatalClientError):
    error = 'application_disabled_by_admin'


@oauth.clientgetter
def load_client(client_id):
    try:
        UUID(hex=client_id)
    except ValueError:
        raise InvalidClientIdError
    app = OAuthApplication.find_first(client_id=client_id)
    if not app.is_enabled:
        raise DisabledClientIdError
    return app


@oauth.grantgetter
def load_grant(client_id, code):  # pragma: no cover
    return OAuthGrant.get(client_id, code)


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    ttl = Config.getInstance().getOAuthGrantTokenTTL()
    expires = datetime.utcnow() + timedelta(seconds=ttl)
    grant = OAuthGrant(client_id=client_id, code=code['code'], redirect_uri=request.redirect_uri,
                       user=session.user, scopes=request.scopes, expires=expires)
    grant.save()
    return grant


@oauth.tokengetter
def load_token(access_token, refresh_token=None):
    if not access_token:
        return None
    # ugly hack so we can know in other places that we received a token
    # e.g. to show an error if there was an invalid token specified but
    # not if there was no token at all
    g.received_oauth_token = True
    try:
        UUID(hex=access_token)
    except ValueError:
        # malformed oauth token
        return None
    token = OAuthToken.find(access_token=access_token).options(db.joinedload(OAuthToken.application)).first()
    if not token or not token.application.is_enabled:
        return None

    token_id = token.id  # avoid DetachedInstanceError in the callback

    @after_this_request
    def _update_last_use(response):
        with db.tmp_session() as sess:
            # do not modify `token` directly, it's attached to a different session!
            sess.query(OAuthToken).filter_by(id=token_id).update({OAuthToken.last_used_dt: now_utc()})
            sess.commit()
        return response

    return token


@oauth.tokensetter
def save_token(token_data, request, *args, **kwargs):
    # For the implicit flow
    # Check issue: https://github.com/lepture/flask-oauthlib/issues/209
    if request.grant_type == 'authorization_code':
        user = request.user
    elif request.grant_type is None:  # implicit flow
        user = session.user
    else:
        raise ValueError('Invalid grant_type')
    requested_scopes = set(token_data['scope'].split())
    token = OAuthToken.find_first(OAuthApplication.client_id == request.client.client_id,
                                  OAuthToken.user == user,
                                  _join=OAuthApplication)
    if token is None:
        application = OAuthApplication.find_one(client_id=request.client.client_id)
        token = OAuthToken(application=application, user=user)
        db.session.add(token)
        token.access_token = token_data['access_token']
        token.scopes = requested_scopes
    elif requested_scopes - token.scopes:
        logger.info('Added scopes to %s: %s', token, requested_scopes - token.scopes)
        # use the new access_token when extending scopes
        token.access_token = token_data['access_token']
        token.scopes |= requested_scopes
    else:
        token_data['access_token'] = token.access_token
    token_data.pop('refresh_token', None)  # we don't support refresh tokens so far
    token_data.pop('expires_in', None)  # our tokens currently do not expire
    return token
