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

from MaKaC.conference import ConferenceHolder
from MaKaC.epayment import TransactionPayLaterMod

from indico.core.fossils.registration import IRegFormRegistrantBasicFossil, IRegFormRegistrantFullFossil

from indico.web.http_api.hooks.base import HTTPAPIHook, DataFetcher
from indico.web.http_api.hooks.event import EventBaseHook
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.responses import HTTPAPIError

from indico.util.date_time import format_datetime, format_date
from indico.util.fossilize import fossilize


@HTTPAPIHook.register
class SetPaidHook(EventBaseHook):
    PREFIX = "api"
    RE = r'(?P<event>[\w\s]+)/registrant/(?P<registrant_id>[\w\s]+)/pay'
    NO_CACHE = True
    COMMIT = True
    HTTP_POST = True

    def _getParams(self):
        super(SetPaidHook, self)._getParams()
        self.auth_key = get_query_parameter(self._queryParams, ["auth_key"])
        self.is_paid = get_query_parameter(self._queryParams, ["is_paid"]) == "yes"
        registrant_id = self._pathParams["registrant_id"]
        self._conf = ConferenceHolder().getById(self._pathParams['event'])
        self._registrant = self._conf.getRegistrantById(registrant_id)
        self._type = "pay"
        if not self._conf.getModPay().isActivated():
            raise HTTPAPIError('E-payment is not enabled')

    def _hasAccess(self, aw):
        return self._conf.canManageRegistration(aw.getUser()) or self._conf.canModify(aw)

    def api_pay(self, aw):
        if self.is_paid:
            self._registrant.setPayed(True)
            data = {}
            data["OrderTotal"] = self._registrant.getTotal()
            data["Currency"] = self._registrant.getRegistrationForm().getCurrency()
            transaction = TransactionPayLaterMod(data)
            self._registrant.setTransactionInfo(transaction)
        else:
            self._registrant.setTransactionInfo(None)
            self._registrant.setPayed(False)
        return {
            "paid": self._registrant.getPayed(),
            "amount_paid": self._registrant.getTotal()
        }


@HTTPAPIHook.register
class CheckInHook(EventBaseHook):
    PREFIX = "api"
    RE = r'(?P<event>[\w\s]+)/registrant/(?P<registrant_id>[\w\s]+)/checkin'
    NO_CACHE = True
    COMMIT = True
    HTTP_POST = True

    def _getParams(self):
        super(CheckInHook, self)._getParams()
        self._check_in = get_query_parameter(self._queryParams, ["checked_in"]) == "yes"
        self._secret = get_query_parameter(self._queryParams, ["secret"])
        registrant_id = self._pathParams["registrant_id"]
        self._conf = ConferenceHolder().getById(self._pathParams['event'])
        self._registrant = self._conf.getRegistrantById(registrant_id)
        self._type = "checkin"

    def _hasAccess(self, aw):
        return (self._conf.canManageRegistration(aw.getUser()) or self._conf.canModify(aw)) \
            and self._secret == self._registrant.getCheckInUUID()

    def api_checkin(self, aw):
        self._registrant.setCheckedIn(self._check_in)
        checkin_date = format_datetime(self._registrant.getAdjustedCheckInDate(), format="short")

        return {
            "checked_in": self._check_in,
            "checkin_date": checkin_date if self._check_in else None
        }


@HTTPAPIHook.register
class RegistrantHook(EventBaseHook):
    RE = r'(?P<event>[\w\s]+)/registrant/(?P<registrant_id>[\w\s]+)'
    NO_CACHE = True
    DEFAULT_DETAIL = 'basic'

    def _getParams(self):
        super(RegistrantHook, self)._getParams()
        self.auth_key = get_query_parameter(self._queryParams, ["auth_key"])
        self._conf = ConferenceHolder().getById(self._pathParams['event'])
        registrant_id = self._pathParams["registrant_id"]
        self._registrant = self._conf.getRegistrantById(registrant_id)
        self._type = "registrant"

    def _hasAccess(self, aw):
        return self._conf.canManageRegistration(aw.getUser()) or self._conf.canModify(aw)

    def export_registrant(self, aw):
        expInt = RegistrantFetcher(aw, self)
        return expInt.registrant()


class RegistrantFetcher(DataFetcher):
    DETAIL_INTERFACES = {
        'basic': IRegFormRegistrantBasicFossil,
        'full': IRegFormRegistrantFullFossil
    }

    def __init__(self, aw, hook):
        super(RegistrantFetcher, self).__init__(aw, hook)
        self._registrant = hook._registrant
        self._conf = hook._conf
        self._detail = hook._detail

    def _makeFossil(self):
        iface = self.DETAIL_INTERFACES.get(self._detail)
        if iface is None:
            raise HTTPAPIError('Invalid detail level: %s' % self._detail, 400)

        return fossilize(self._registrant, iface)

    def registrant(self):
        result = self._makeFossil()
        if self._detail == 'basic':
            regForm = self._conf.getRegistrationForm()
            result["personal_data"] = regForm.getPersonalData().getRegistrantValues(self._registrant)
        return result


@HTTPAPIHook.register
class RegistrantsHook(EventBaseHook):
    RE = r'(?P<event>[\w\s]+)/registrants'
    NO_CACHE = True

    def _getParams(self):
        super(RegistrantsHook, self)._getParams()
        self._conf_id = self._pathParams['event']
        self._type = "registrants"
        self._conf = ConferenceHolder().getById(self._conf_id)

    def _hasAccess(self, aw):
        return self._conf.canManageRegistration(aw.getUser()) or self._conf.canModify(aw)

    def export_registrants(self, aw):
        registrants = self._conf.getRegistrantsList()
        registrant_list = []
        for registrant in registrants:
            reg = {
                "registrant_id": registrant.getId(),
                "checked_in": registrant.isCheckedIn(),
                "full_name": registrant.getFullName(title=True, firstNameFirst=True),
                "checkin_secret": registrant.getCheckInUUID(),
            }
            regForm = self._conf.getRegistrationForm()
            reg["personal_data"] = regForm.getPersonalData().getRegistrantValues(registrant)
            registrant_list.append(reg)
        return {"registrants": registrant_list}
