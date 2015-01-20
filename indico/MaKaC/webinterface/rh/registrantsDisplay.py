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

import MaKaC.webinterface.pages.registrants as registrants
import MaKaC.webinterface.rh.conferenceDisplay as conferenceDisplay
import MaKaC.webinterface.common.regFilters as regFilters
from MaKaC.errors import NoReportError
import MaKaC.webinterface.displayMgr as displayMgr


class RHRegistrantsDisplayBase( conferenceDisplay.RHConferenceBaseDisplay):

    def _checkProtection( self ):
        conferenceDisplay.RHConferenceBaseDisplay._checkProtection(self)
        if not self._conf.getRegistrationForm().isActivated() or not self._conf.hasEnabledSection("regForm") or not displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu().getLinkByName("registrants").isEnabled():
            raise NoReportError("The registrants list page was disabled by the conference managers")

class RHRegistrantsList( RHRegistrantsDisplayBase ):

    @staticmethod
    def create_filter(conf, params, filterUsed=False, sessionFilterName="session"):
        regForm = conf.getRegistrationForm()
        newFilter = {}
        sessform =regForm.getSessionsForm()
        sesstypes = sessform.getSessionList()
        lsessions = []
        if not filterUsed:
            for sess in sesstypes:
                lsessions.append( sess.getId() )
        newFilter[sessionFilterName]=params.get("session",lsessions)
        return regFilters.RegFilterCrit(conf,newFilter)

    def _checkParams(self, params):
        RHRegistrantsDisplayBase._checkParams(self, params)

        # ---- FILTERING ----
        if params.has_key("firstChoice"):
            self._sessionFilterName="sessionfirstpriority"
        else:
            self._sessionFilterName="session"

        filterUsed=params.has_key("OK")
        self._filterCrit=self.create_filter(self._conf, params, filterUsed, self._sessionFilterName)

        sessionShowNoValue=True
        if filterUsed:
            sessionShowNoValue =  params.has_key("sessionShowNoValue")
        self._filterCrit.getField(self._sessionFilterName).setShowNoValue( sessionShowNoValue )

        # ---- SORTING ----
        self._sortingCrit = regFilters.SortingCriteria( [params.get( "sortBy", "Name" ).strip()] )
        self._order = params.get("order","down")

    def _process( self ):
        p = registrants.WPConfRegistrantsList( self, self._conf )
        return p.display(filterCrit=self._filterCrit, sortingCrit=self._sortingCrit, order=self._order, sessionFilterName=self._sessionFilterName)
