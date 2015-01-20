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

from MaKaC.webinterface.pages import registrationForm
from MaKaC.webinterface import wcomponents
from indico.web.flask.util import url_for
from indico.core.config import Config


class WPConfModifETicketBase(registrationForm.WPConfModifRegFormBase):

    def _setActiveTab(self):
        self._tabETicket.setActive()


class WPConfModifETicket(WPConfModifETicketBase):

    def _getTabContent(self, params):
        wc = WConfModifETicket(self._conf, self._getAW())
        return wc.getHTML()


class WConfModifETicket(wcomponents.WTemplated):

    def __init__(self, conference, aw):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        modETicket = self._conf.getRegistrationForm().getETicket()
        vars["conf"] = self._conf
        vars["isEnabled"] = modETicket.isEnabled()
        vars["downloadURL"] = Config.getInstance().getCheckinURL()
        return vars
