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

#import syslog
from flask import session, request
import MaKaC.webinterface.rh.base as base
import MaKaC.common.info as info
from indico.core.config import Config

class RHResetTZ(base.RH):

    def _process(self):
        #syslog.syslog("In RHResetTZ id: " + str(sess.id))
        parms = self._getRequestParams()

        tz = None
        if not parms.has_key("activeTimezone") or parms["activeTimezone"] == "My":
            if self._aw.getUser():
                tz = self._aw.getUser().getTimezone()
            else:
                tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        else:
            tz = parms["activeTimezone"]

        try:
            if parms["saveToProfile"] == "on":
                user = session.user
                if tz == "LOCAL":
                    user.setDisplayTZMode("Event Timezone")
                else:
                    user.setTimezone(tz)
                    user.setDisplayTZMode("MyTimezone")
        except:
            pass

        session.timezone = tz
        # redirect to the calling URL with the new session tz.
        self._redirect(request.referrer or Config.getInstance().getBaseURL())
