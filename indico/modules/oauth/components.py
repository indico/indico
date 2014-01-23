# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from datetime import timedelta
import oauth2 as oauth
from flask import request
from random import choice
from string import ascii_letters, digits
from zope.interface import Interface

from indico.core.index import OOIndex
from indico.web.flask.util import create_flat_args
from indico.modules.oauth.errors import OAuthError
from MaKaC.common.logger import Logger
from indico.core.config import Config
from MaKaC.common.timezoneUtils import nowutc


class IIndexableByUserId(Interface):
    pass


class UserOAuthRequestTokenIndex(OOIndex):

    def __init__(self):
        super(UserOAuthRequestTokenIndex, self).__init__(IIndexableByUserId)

    def initialize(self, dbi=None):
        pass


class UserOAuthAccessTokenIndex(OOIndex):

    def __init__(self):
        super(UserOAuthAccessTokenIndex, self).__init__(IIndexableByUserId)

    def initialize(self, dbi=None):
        pass


class OAuthUtils:
    @classmethod
    def OAuthCheckAccessResource(cls):
        from indico.modules.oauth.db import ConsumerHolder, AccessTokenHolder, OAuthServer

        oauth_request = oauth.Request.from_request(request.method, request.base_url, request.headers,
                                                   parameters=create_flat_args())
        Logger.get('oauth.resource').info(oauth_request)
        try:
            now = nowutc()
            consumer_key = oauth_request.get_parameter('oauth_consumer_key')
            if not ConsumerHolder().hasKey(consumer_key):
                raise OAuthError('Invalid Consumer Key', 401)
            consumer = ConsumerHolder().getById(consumer_key)
            token = oauth_request.get_parameter('oauth_token')
            if not token or not AccessTokenHolder().hasKey(token):
                raise OAuthError('Invalid Token', 401)
            access_token = AccessTokenHolder().getById(token)
            oauth_consumer = oauth.Consumer(consumer.getId(), consumer.getSecret())
            OAuthServer.getInstance().verify_request(oauth_request, oauth_consumer, access_token.getToken())
            if access_token.getConsumer().getId() != oauth_consumer.key:
                raise OAuthError('Invalid Consumer Key', 401)
            elif (now - access_token.getTimestamp()) > timedelta(seconds=Config.getInstance().getOAuthAccessTokenTTL()):
                raise OAuthError('Expired Token', 401)
            return access_token
        except oauth.Error, e:
            if e.message.startswith("Invalid Signature"):
                raise OAuthError("Invalid Signature", 401)
            else:
                raise OAuthError(e.message, 400)

    #http://nullege.com/codes/show/src%40r%40e%40repoze-oauth-plugin-0.2%40repoze%40who%40plugins%40oauth%40plugin.py/45/oauth2.Server/python

    @classmethod
    def gen_random_string(cls, length=40, alphabet=ascii_letters + digits):
        """Generate a random string of the given length and alphabet"""
        return ''.join([choice(alphabet) for i in xrange(length)])
