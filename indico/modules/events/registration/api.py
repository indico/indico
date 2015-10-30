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

from flask import request, jsonify
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.modules.oauth import oauth
from indico.modules.payment import event_settings as payment_event_settings
from indico.modules.events.api import EventBaseHook
from indico.modules.payment.models.transactions import TransactionAction
from indico.modules.payment.util import register_transaction
from indico.modules.events.registration.util import build_registrations_api_data
from indico.util.fossilize import fossilize
from indico.web.http_api.hooks.base import HTTPAPIHook, DataFetcher
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.responses import HTTPAPIError

from MaKaC.conference import ConferenceHolder
from MaKaC.webinterface.rh.base import RH


class RHAPIRegistrant(RH):
    """RESTful registrant API"""

    @oauth.require_oauth('registrants')
    def _checkParams(self):
        event = ConferenceHolder().getById(request.view_args['event_id'], True)
        if event is None:
            raise NotFound("No such event")
        if not event.canManageRegistration(request.oauth.user):
            raise Forbidden()
        registrant = event.getRegistrantById(request.view_args['registrant_id'])
        if registrant is None:
            raise NotFound("No such registrant")
        self.event = event
        self.registrant = registrant

    def _get_result(self, **kwargs):
        checkin_date = None
        if self.registrant.isCheckedIn():
            checkin_date = self.registrant.getCheckInDate().isoformat()
        return jsonify(event_id=self.event.getId(),
                       registrant_id=self.registrant.getId(),
                       full_name=self.registrant.getFullName(title=True, firstNameFirst=True),
                       checked_in=self.registrant.isCheckedIn(),
                       checkin_secret=self.registrant.getCheckInUUID(),
                       checkin_date=checkin_date,
                       registration_date=self.registrant.getRegistrationDate().isoformat(),
                       **kwargs)

    def _process_GET(self):
        registration_form = self.event.getRegistrationForm()
        personal_data = registration_form.getPersonalData().getRegistrantValues(self.registrant)
        return self._get_result(personal_data=personal_data)

    def _process_PATCH(self):
        if request.json is None:
            raise BadRequest('Expected JSON payload')
        invalid_fields = request.json.viewkeys() - {'checked_in'}
        if invalid_fields:
            raise BadRequest("Invalid fields: {}".format(', '.join(invalid_fields)))
        if self.registrant is None:
            raise NotFound("No such registrant")
        if 'checked_in' in request.json:
            self.registrant.setCheckedIn(bool(request.json['checked_in']))
        return self._get_result()


class RHAPIRegistrants(RH):
    """RESTful registrants API"""

    @oauth.require_oauth('registrants')
    def _checkProtection(self):
        if not self.event.can_manage(request.oauth.user, role='registration'):
            raise Forbidden()

    def _checkParams(self):
        self.event = Event.find(id=request.view_args['event_id'], is_deleted=False).first_or_404()

    def _process_GET(self):
        return jsonify(registrants=build_registrations_api_data(self.event))


@HTTPAPIHook.register
class SetPaidHook(EventBaseHook):
    PREFIX = "api"
    RE = r'(?P<event>[\w\s]+)/registrant/(?P<registrant_id>[\w\s]+)/pay'
    METHOD_NAME = 'api_pay'
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
        if not payment_event_settings.get(self._conf, 'enabled'):
            raise HTTPAPIError('E-payment is not enabled')

    def _hasAccess(self, aw):
        return self._conf.canManageRegistration(aw.getUser()) or self._conf.canModify(aw)

    def api_pay(self, aw):
        action = TransactionAction.complete if self._isPayed == '1' else TransactionAction.cancel
        register_transaction(registrant=self._registrant,
                             amount=self._registrant.getTotal(),
                             currency=self._registrant.getCurrency(),
                             action=action)
        return {
            "paid": self._registrant.getPayed(),
            "amount_paid": self._registrant.getTotal()
        }


@HTTPAPIHook.register
class RegistrantHook(EventBaseHook):
    RE = r'(?P<event>[\w\s]+)/registrant/(?P<registrant_id>[\w\s]+)'
    METHOD_NAME = 'export_registrant'
    NO_CACHE = True
    DEFAULT_DETAIL = 'basic'

    def _getParams(self):
        super(RegistrantHook, self)._getParams()
        self.auth_key = get_query_parameter(self._queryParams, ["auth_key"])
        self._conf = ConferenceHolder().getById(self._pathParams['event'])
        registrant_id = self._pathParams["registrant_id"]
        self._registrant = self._conf.getRegistrantById(registrant_id)

    def _hasAccess(self, aw):
        return self._conf.canManageRegistration(aw.getUser()) or self._conf.canModify(aw)

    def export_registrant(self, aw):
        expInt = RegistrantFetcher(aw, self)
        return expInt.registrant()


class RegistrantFetcher(DataFetcher):
    # DETAIL_INTERFACES = {
    #     'basic': IRegFormRegistrantBasicFossil,
    #     'full': IRegFormRegistrantFullFossil
    # }

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
    METHOD_NAME = 'export_registrants'
    NO_CACHE = True

    def _getParams(self):
        super(RegistrantsHook, self)._getParams()
        self._event = Event.find_one(id=self._pathParams['event'], is_deleted=False)

    def _hasAccess(self, aw):
        return self._event.can_manage(aw.getUser(legacy=False), role='registration')

    def export_registrants(self, aw):
        return {"registrants": build_registrations_api_data(self._event)}
