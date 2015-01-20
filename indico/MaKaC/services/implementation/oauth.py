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

from indico.core.index import Catalog
from indico.modules.oauth.db import ConsumerHolder, Consumer, AccessTokenHolder, RequestTokenHolder
from indico.modules.oauth.components import OAuthUtils
from MaKaC.services.implementation.base import ParameterManager, AdminService
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.services.implementation.user import UserModifyBase
from MaKaC.common.fossilize import fossilize

class OAuthAddConsumer(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._consumerName = pm.extract("consumer_name", pType=str, allowEmpty=False)

    def _getAnswer(self):
        consumer = Consumer(OAuthUtils.gen_random_string(),OAuthUtils.gen_random_string(), self._consumerName)
        ConsumerHolder().add(consumer)
        return fossilize(consumer)

class OAuthConsumerEditBase(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        self._pm = ParameterManager(self._params)
        consumerKey = self._pm.extract("consumer_key", pType=str, allowEmpty=False)
        if not ConsumerHolder().hasKey(consumerKey):
            raise ServiceError("", _("Consumer key not found"))
        self._consumer = ConsumerHolder().getById(consumerKey)

class OAuthRemoveConsumer(OAuthConsumerEditBase):

    def _getAnswer(self):
        ConsumerHolder().remove(self._consumer)
        return True

class OAuthToogleConsumerTrusted(OAuthConsumerEditBase):

    def _getAnswer(self):
        self._consumer.setTrusted(not self._consumer.isTrusted())
        return self._consumer.isTrusted()

class OAuthUnauthorizeConsumer(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._third_party_app = pm.extract("third_party_app", pType=str, allowEmpty=False)
        if self._third_party_app is None:
            raise ServiceError("ERR-U5", _("Third party ap not specified"))

    def _getAnswer(self):
        request_tokens = Catalog.getIdx('user_oauth_request_token').get(self._target.getId())
        access_tokens = Catalog.getIdx('user_oauth_access_token').get(self._target.getId())
        if request_tokens:
            for token in list(request_tokens):
                if token.getConsumer().getName() == self._third_party_app:
                    RequestTokenHolder().remove(token)
        if access_tokens:
            for token in list(access_tokens):
                if token.getConsumer().getName() == self._third_party_app:
                    AccessTokenHolder().remove(token)
        return True

methodMap = {
    "addConsumer": OAuthAddConsumer,
    "removeConsumer": OAuthRemoveConsumer,
    "toogleCosumerTrusted": OAuthToogleConsumerTrusted,
    "unauthorizeConsumer": OAuthUnauthorizeConsumer,
}
