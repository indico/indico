# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.services.implementation.base import TextModificationBase, ParameterManager
from MaKaC.services.implementation.conference import ConferenceModifBase
from indico.util.date_time import format_datetime
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError


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
    "eticket.checkin": RegistrantModifCheckIn
}
