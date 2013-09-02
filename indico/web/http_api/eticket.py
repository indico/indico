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

from MaKaC.conference import ConferenceHolder

from indico.web.http_api.api import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError
from indico.web.http_api.util import get_query_parameter

from indico.util.date_time import format_datetime


class RegistrantBaseHook(HTTPAPIHook):
    def _getParams(self):
        self._registrant_id = self._pathParams["registrant_id"]
        self._conf_id = get_query_parameter(self._queryParams, ["target"])
        self._secret = get_query_parameter(self._queryParams, ["secret"])
        ch = ConferenceHolder()
        self._conf = ch.getById(self._conf_id)
        self._registrant = self._conf.getRegistrantById(self._registrant_id)

    def _checkProtection(self, aw):
        user = aw.getUser()
        if not self._conf.canManageRegistration(user)\
            or self._secret != self._registrant.getCheckInUUID():
            raise HTTPAPIError("Access denied", 403)


@HTTPAPIHook.register
class CheckInHook(RegistrantBaseHook):
    TYPES = ("checkin",)
    RE = r"(?P<registrant_id>[\d]+)"
    NO_CACHE = True
    COMMIT = True

    def _getParams(self):
        super(CheckInHook, self)._getParams()
        self._check_in = get_query_parameter(self._queryParams, ["checked_in"])

    def export_checkin(self, aw):
        self._checkProtection(aw)
        if self._check_in == "true":
            self._registrant.setCheckedIn(True)
        else:
            self._registrant.setCheckedIn(False)
        return {"success": True}


@HTTPAPIHook.register
class RegistrantHook(RegistrantBaseHook):
    TYPES = ("registrant",)
    RE = r"(?P<registrant_id>[\d]+)"
    NO_CACHE = True

    def export_registrant(self, aw):
        self._checkProtection(aw)

        registration_date = format_datetime(self._registrant.getAdjustedRegistrationDate())
        checkin_date = format_datetime(self._registrant.getAdjustedCheckInDate())
        regForm = self._conf.getRegistrationForm()
        if regForm.getReasonParticipationForm().isEnabled():
            participation_reason = self._registrant.getReasonParticipation()
        else:
            participation_reason = None
        return {
            "registrant_id": self._registrant_id,
            "registrant_full_name": self._registrant.getFullName(),
            "registrant_position": self._registrant.getPosition(),
            "registrant_institution": self._registrant.getInstitution(),
            "registrant_adress": self._registrant.getAddress(),
            "registrant_city": self._registrant.getCity(),
            "registrant_country": self._registrant.getCountry(),
            "registrant_phone": self._registrant.getPhone(),
            "registrant_fax": self._registrant.getFax(),
            "registrant_email": self._registrant.getEmail(),
            "registrant_home_page": self._registrant.getPersonalHomepage(),
            "registrant_payed": self._registrant.getPayed(),
            "registrant_checked_in": self._registrant.isCheckedIn(),
            "registrant_check_in_date": checkin_date,
            "registration_date": registration_date,
            "participation_reason": participation_reason
        }


@HTTPAPIHook.register
class RegistrantsHook(HTTPAPIHook):
    TYPES = ("registrants",)
    RE = r"(?P<conf_id>[\d]+)"
    NO_CACHE = True

    def _getParams(self):
        self._conf_id = self._pathParams["conf_id"]
        ch = ConferenceHolder()
        self._conf = ch.getById(self._conf_id)

    def _checkProtection(self, aw):
        user = aw.getUser()
        if not self._conf.canManageRegistration(user):
            raise HTTPAPIError("Access denied", 403)

    def export_registrants(self, aw):
        self._checkProtection(aw)
        registrants = self._conf.getRegistrantsList()
        registrant_list = []
        for registrant in registrants:
            reg = {
                "id": registrant.getId(),
                "full_name": registrant.getFullName(),
                "checked_in": registrant.isCheckedIn(),
                "secret": registrant.getCheckInUUID()
            }
            registrant_list.append(reg)
        return {"registrants": registrant_list}


@HTTPAPIHook.register
class EventsHook(HTTPAPIHook):
    TYPES = ("events",)
    RE = r"(?P<user_id>[\d]+)"
    NO_CACHE = True

    def export_events(self, aw):
        user = aw.getUser()
        managed_conferences = user.getLinkTo('conference', 'creator')
        managed_conferences.update(user.getLinkTo('conference', 'manager'))
        events = []
        for conf in managed_conferences:
            if conf.getRegistrationForm().getETicket().isEnabled():
                event = {
                    "id": conf.getId(),
                    "title": conf.getTitle(),
                    "date": conf.getAdjustedStartDate(),
                    "registrants": len(conf.getRegistrants())
                }
                events.append(event)
        return {"events": events}
