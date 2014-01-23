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
from flask import request


from datetime import timedelta
from urllib import urlencode
import oauth2 as oauth

from indico.core.index import Catalog
from indico.modules.oauth.db import OAuthServer, Token, ConsumerHolder, AccessTokenHolder, RequestTokenHolder, TempRequestTokenHolder
from indico.modules.oauth.errors import OAuthError
from indico.modules.oauth.components import OAuthUtils

from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.logger import Logger
from MaKaC.webinterface.rh import base
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.urlHandlers import UHOAuthThirdPartyAuth
from MaKaC.errors import AccessControlError, MaKaCError
from MaKaC.webinterface.rh.services import RHServicesBase
from MaKaC.webinterface.rh.users import RHUserBase
from MaKaC.webinterface.pages.oauth import WPAdminOAuthConsumers, WPAdminOAuthAuthorized, WPOAuthThirdPartyAuth, WPOAuthUserThirdPartyAuth
from indico.core.config import Config


class RHOAuth(base.RH):

    def _checkParams(self, params):
        self._oauth_request = oauth.Request.from_request(request.method, request.base_url, headers=request.headers,
                                                         parameters=params)


class RHOAuthRequestToken(RHOAuth):

    def _checkParams(self, params):
        try:
            RHOAuth._checkParams(self, params)
            consumer_key = self._oauth_request.get_parameter('oauth_consumer_key')
            Logger.get('oauth.request_token').info(consumer_key)
            if not ConsumerHolder().hasKey(consumer_key):
                raise OAuthError("Invalid Consumer Key", 401)
            self._consumer = ConsumerHolder().getById(consumer_key)
            #Logger.get('oauth.request_token').info(consumer.getSecret())
            oauth_consumer = oauth.Consumer(self._consumer.getId(), self._consumer.getSecret())
            OAuthServer.getInstance().verify_request(self._oauth_request, oauth_consumer, None)
        except oauth.Error, err:
            raise OAuthError(err.message, 401)

    def _process(self):
        # TODO: Token should have flag authorized=False
        token = oauth.Token(OAuthUtils.gen_random_string(), OAuthUtils.gen_random_string())
        token.set_callback(self._oauth_request.get_parameter('oauth_callback'))
        timestamp = nowutc()
        TempRequestTokenHolder().add(Token(token.key, token, timestamp, self._consumer, None))
        Logger.get('oauth.request_token').info(token.to_string())
        return token.to_string()


class RHOAuthAuthorization(RHOAuth, base.RHProtected):
    def _checkParams(self, params):
        try:
            RHOAuth._checkParams(self, params)
            base.RHProtected._checkParams(self, params)
            request_token_key = self._oauth_request.get_parameter('oauth_token')
            if not TempRequestTokenHolder().hasKey(request_token_key):
                raise OAuthError("Invalid Token", 401)
            self._request_token = TempRequestTokenHolder().getById(request_token_key)
            if not ConsumerHolder().getById(self._request_token.getConsumer().getId()):
                raise OAuthError("Invalid Consumer Key", 401)
        except oauth.Error, err:
            raise OAuthError(err.message, 401)

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        user = self.getAW().getUser()
        old_request_token = self._checkThirdPartyAuthPermissible(self._request_token.getConsumer().getName(), user.getId())
        TempRequestTokenHolder().remove(self._request_token)
        self._request_token.setUser(user)
        if old_request_token is not None:
            self._request_token.setAuthorized(old_request_token.isAuthorized())
            RequestTokenHolder().update(old_request_token, self._request_token)
        else:
            RequestTokenHolder().add(self._request_token)
        if not self._request_token.getConsumer().isTrusted() and not self._request_token.isAuthorized():
            redirectURL = UHOAuthThirdPartyAuth.getURL()
            redirectURL.addParams({'callback': self._request_token.getToken().get_callback_url(),
                                   #'returnURL': str(urlHandlers.UHOAuthAuthorizeConsumer.getURL()),
                                   'third_party_app': self._request_token.getConsumer().getName()})
            self._redirect(redirectURL)
            return
        verifier = OAuthUtils.gen_random_string()
        self._request_token.getToken().set_verifier(verifier)
        self._request_token._p_changed = 1
        self._redirect(self._request_token.getToken().get_callback_url())

    def _checkThirdPartyAuthPermissible(self, consumer, user_id):
        request_token = Catalog.getIdx('user_oauth_request_token').get(user_id)
        if request_token is not None:
            for token in list(request_token):
                if token.getConsumer().getName() == consumer:
                    return token
        return None


class RHOAuthAuthorizeConsumer(RHOAuth, base.RHProtected):

    def _checkParams(self, params):
        RHOAuth._checkParams(self, params)
        base.RHProtected._checkParams(self, params)
        try:
            self.user_id = self._oauth_request.get_parameter('userId')
            self.response = self._oauth_request.get_parameter('response')
            self.callback = self._oauth_request.get_parameter('callback')
        except oauth.Error, err:
            raise OAuthError(err.message, 400)

    def _process(self):
        request_tokens = Catalog.getIdx('user_oauth_request_token').get(self.user_id)
        if request_tokens:
            for request_token in request_tokens:
                if self.response == 'accept':
                    verifier = OAuthUtils.gen_random_string()
                    request_token.getToken().set_verifier(verifier)
                    request_token.setAuthorized(True)
                    request_token._p_changed = 1
                else:
                    RequestTokenHolder().remove(request_token)
                self._redirect(request_token.getToken().get_callback_url())
        else:
            raise MaKaCError(_("""There was a problem while authenticating.
                                  Please, start again the login process from the beginning"""))


class RHOAuthAccessTokenURL(RHOAuth):
    def _checkParams(self, params):
        RHOAuth._checkParams(self, params)
        try:
            request_token_key = self._oauth_request.get_parameter('oauth_token')
            self.verifier = self._oauth_request.get_parameter('oauth_verifier')
            if not RequestTokenHolder().hasKey(request_token_key):
                raise OAuthError("Invalid Token", 401)
            self._request_token = RequestTokenHolder().getById(request_token_key)
            if self._request_token.getToken().verifier != self.verifier:
                raise OAuthError("Invalid Token", 401)
            if not ConsumerHolder().hasKey(self._request_token.getConsumer().getId()):
                raise OAuthError("Invalid Consumer Key", 401)
            consumer = oauth.Consumer(self._request_token.getConsumer().getId(), self._request_token.getConsumer().getSecret())
            OAuthServer.getInstance().verify_request(self._oauth_request, consumer, self._request_token.getToken())
        except oauth.Error, err:
            raise OAuthError(err.message, 401)

    def _process(self):
        try:
            user = self._request_token.getUser()
            access_tokens = Catalog.getIdx('user_oauth_access_token').get(user.getId())
            timestamp = nowutc()
            if access_tokens is not None:
                for access_token in list(access_tokens):
                    if access_token.getConsumer().getName() == self._request_token.getConsumer().getName():
                        access_token.setTimestamp(timestamp)
                        response = {'oauth_token': access_token.getId(),
                                    'oauth_token_secret': access_token.getToken().secret,
                                    'user_id': user.getId(),
                                    'oauth_token_ttl': Config.getInstance().getOAuthAccessTokenTTL(),
                                    'oauth_token_expiration_timestamp': access_token.getTimestamp() +
                                    timedelta(seconds=Config.getInstance().getOAuthAccessTokenTTL())}
                        return urlencode(response)
            access_token_key = OAuthUtils.gen_random_string()
            access_token_secret = OAuthUtils.gen_random_string()
            access_token = Token(access_token_key, oauth.Token(access_token_key, access_token_secret),
                                 timestamp, self._request_token.getConsumer(), user)
            AccessTokenHolder().add(access_token)
            response = {'oauth_token': access_token_key,
                        'oauth_token_secret': access_token_secret,
                        'user_id': user.getId(),
                        'oauth_token_ttl': Config.getInstance().getOAuthAccessTokenTTL(),
                        'oauth_token_expiration_timestamp': access_token.getTimestamp() +
                        timedelta(seconds=Config.getInstance().getOAuthAccessTokenTTL())}
            return urlencode(response)
        except oauth.Error, err:
            raise OAuthError(err.message, 401)


# ADMINISTRATION SERVICES
class RHAdminOAuthConsumers(RHServicesBase):
    def _process(self):
        p = WPAdminOAuthConsumers(self)
        return p.display()


class RHAdminOAuthAuthorized(RHServicesBase):
    def _process(self):
        p = WPAdminOAuthAuthorized(self)
        return p.display()


# User related
class RHOAuthThirdPartyAuth(base.RHProtected):

    def _process(self):
        p = WPOAuthThirdPartyAuth(self)
        return p.display(userId=self._getUser().getId(), **self._reqParams)


class RHOAuthUserThirdPartyAuth(RHUserBase):
    _uh = urlHandlers.UHOAuthUserThirdPartyAuth

    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        if self._aw.getUser():
            if not self._avatar.canModify(self._aw):
                raise AccessControlError("user")

    def _process(self):
        p = WPOAuthUserThirdPartyAuth(self, self._avatar)
        return p.display()
