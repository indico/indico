# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import session, after_this_request

from indico.core.db import db
from indico.core.config import Config
from indico.modules.oauth import oauth
from indico.modules.oauth.models.applications import OAuthApplication
from indico.modules.oauth.models.tokens import OAuthGrant, OAuthToken
from indico.util.date_time import now_utc


@oauth.clientgetter
def load_client(client_id):
    return OAuthApplication.find_first(client_id=client_id)


@oauth.grantgetter
def load_grant(client_id, code):
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
    token = OAuthToken.find_first(access_token=access_token)
    if not token:
        return None

    @after_this_request
    def _update_last_use(response):
        with db.tmp_session() as sess:
            # do not modify `token` directly, it's attached to a different session!
            sess.query(OAuthToken).filter_by(id=token.id).update({OAuthToken.last_used_dt: now_utc()})
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
        # use the new access_token when extending scopes
        token.access_token = token_data['access_token']
        token.scopes = token.scopes | requested_scopes
    else:
        token_data['access_token'] = token.access_token
    token_data.pop('refresh_token', None)  # we don't support refresh tokens so far
    token_data.pop('expires_in', None)  # our tokens currently do not expire
    return token
