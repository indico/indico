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
Asynchronous request handlers for registrant-related data
"""

from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.common.contextManager import ContextManager


class RegistrantModifBase(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        try:
            self._registrant_ids = self._params["registrants"]
        except KeyError:
            raise ServiceError("", _("No registrants selected"))

    def _checkProtection(self):
        user = ContextManager.get("currentUser")
        if not self._conf.canManageRegistration(user):
            raise ServiceAccessError("Access denied")


class RegistrantModifCheckIn(RegistrantModifBase):

    def _getAnswer(self):
        registrants_changed = []
        for registrant_id in self._registrant_ids:
            registrant = self._conf.getRegistrantById(registrant_id)
            if not registrant.isCheckedIn():
                registrants_changed.append(registrant_id)
                registrant.setCheckedIn(True)
        return {"registrants": registrants_changed}


methodMap = {
    "eticket.checkIn": RegistrantModifCheckIn
}
