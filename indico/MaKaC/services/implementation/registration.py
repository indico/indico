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

"""
Asynchronous request handlers for registration-related data
"""

import base64
from qrcode import QRCode, constants
from cStringIO import StringIO

from indico.util.date_time import format_datetime, format_date
from indico.util import json
from indico.modules.oauth.db import ConsumerHolder

from MaKaC.common.Configuration import Config
from MaKaC.services.implementation.base import TextModificationBase, ParameterManager
from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.services.interface.rpc.common import NoReportError


class RegistrationModifBase(ConferenceModifBase):

    def _checkProtection(self):
        if not self._target.canManageRegistration(self.getAW().getUser()):
            ConferenceModifBase._checkProtection(self)


class ConferenceEticketToggleActivation(TextModificationBase, RegistrationModifBase):

    def _getAnswer(self):
        eticket = self._conf.getRegistrationForm().getETicket()
        eticket.setEnabled(not eticket.isEnabled())
        return eticket.isEnabled()


class ConferenceEticketSetAttachToEmail(TextModificationBase, RegistrationModifBase):

    def _handleSet(self):
        self._conf.getRegistrationForm().getETicket().setAttachedToEmail(self._value)

    def _handleGet(self):
        return self._conf.getRegistrationForm().getETicket().isAttachedToEmail()


class ConferenceEticketSetShowInConferenceMenu(TextModificationBase, RegistrationModifBase):

    def _handleSet(self):
        self._conf.getRegistrationForm().getETicket().setShowInConferenceMenu(self._value)

    def _handleGet(self):
        return self._conf.getRegistrationForm().getETicket().isShownInConferenceMenu()


class ConferenceEticketSetAfterRegistration(TextModificationBase, RegistrationModifBase):

    def _handleSet(self):
        self._conf.getRegistrationForm().getETicket().setShowAfterRegistration(self._value)

    def _handleGet(self):
        return self._conf.getRegistrationForm().getETicket().isShownAfterRegistration()


class ConferenceEticketQRCode(RegistrationModifBase):

    def _getAnswer(self):

        consumers = dict((consumer.getName(), consumer) for consumer in ConsumerHolder().getList())

        if "indico-checkin" not in consumers:
            raise NoReportError(_("There is no indico-checkin consumer key for OAuth"))

        # QRCode (Version 6 with error correction L can contain up to 106 bytes)
        qr = QRCode(
            version=6,
            error_correction=constants.ERROR_CORRECT_M,
            box_size=4,
            border=1
        )

        oauth_checkin = consumers["indico-checkin"]
        config = Config.getInstance()
        baseURL = config.getBaseSecureURL() if config.getBaseSecureURL() else config.getBaseURL()
        qr_data = {"event_id": self._conf.getId(),
                   "title": self._conf.getTitle(),
                   "date": format_date(self._conf.getAdjustedStartDate()),
                   "server": {"baseUrl": baseURL,
                              "consumerKey": oauth_checkin.getId(),
                              "consumerSecret": oauth_checkin.getSecret(),
                              }
                   }
        json_qr_data = json.dumps(qr_data)
        qr.add_data(json_qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image()

        output = StringIO()
        qr_img._img.save(output, format="png")
        im_data = output.getvalue()

        return 'data:image/png;base64,{0}'.format(base64.b64encode(im_data))


class RegistrantModifBase(RegistrationModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._registrant_ids = pm.extract("registrants", pType=list, allowEmpty=False)


class RegistrantModifCheckIn(RegistrantModifBase):

    def _getAnswer(self):
        if not self._registrant_ids:
            raise NoReportError(_("No registrants were selected to check-in"))
        dates_changed = {}
        for registrant_id in self._registrant_ids:
            registrant = self._conf.getRegistrantById(registrant_id)
            if not registrant.isCheckedIn():
                registrant.setCheckedIn(True)
                checkInDate = registrant.getAdjustedCheckInDate()
                dates_changed[registrant_id] = format_datetime(checkInDate)
        return {"dates": dates_changed}


methodMap = {

    "eticket.toggleActivation": ConferenceEticketToggleActivation,
    "eticket.setAttachToEmail": ConferenceEticketSetAttachToEmail,
    "eticket.setShowInConferenceMenu": ConferenceEticketSetShowInConferenceMenu,
    "eticket.setShowAfterRegistration": ConferenceEticketSetAfterRegistration,
    "eticket.getQRCode": ConferenceEticketQRCode,
    "eticket.checkin": RegistrantModifCheckIn
}
