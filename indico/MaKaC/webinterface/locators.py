# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import MaKaC.conference as conference
import MaKaC.errors as errors
from MaKaC.i18n import _


class WebLocator:
    def __init__(self):
        self.__confId = None

    def setConference( self, params ):
        if not ("confId" in params.keys()) and "confid" in params.keys():
            params["confId"] = params["confid"]
        if not ("confId" in params.keys()) and "conference" in params.keys():
            params["confId"] = params["conference"]
        if isinstance(params.get("confId", ""), list):
            params["confId"] = params["confId"][0]
        if not ("confId" in params.keys()) or \
           params["confId"] == None or \
               params["confId"].strip()=="":
            raise errors.MaKaCError( _("conference id not set"))
        self.__confId = params["confId"]

    def getConference( self ):
        return conference.ConferenceHolder().getById( self.__confId )

    def getObject(self):
        if not self.__confId:
            return None
        obj = conference.ConferenceHolder().getById(self.__confId)
        if obj is None:
            raise errors.NoReportError("The event you are trying to access does not exist or has been deleted")
        return obj
