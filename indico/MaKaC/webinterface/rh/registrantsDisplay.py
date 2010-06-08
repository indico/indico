# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import MaKaC.webinterface.pages.registrants as registrants
import MaKaC.webinterface.rh.conferenceDisplay as conferenceDisplay
import MaKaC.webinterface.common.regFilters as regFilters
from MaKaC.errors import NoReportError
import MaKaC.webinterface.displayMgr as displayMgr


class RHRegistrantsDisplayBase( conferenceDisplay.RHConferenceBaseDisplay):

    def _checkProtection( self ):
        conferenceDisplay.RHConferenceBaseDisplay._checkProtection(self)
        if not self._conf.getEvaluation().isVisible() or not self._conf.hasEnabledSection("regForm") or not displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu().getLinkByName("registrants").isEnabled():
            raise NoReportError("The registrants list page was disabled by the conference managers")

class RHRegistrantsList( RHRegistrantsDisplayBase ):

    def _checkParams(self, params):
        RHRegistrantsDisplayBase._checkParams(self, params)
        regForm = self._conf.getRegistrationForm()

        # ---- FILTERING ----
        if params.has_key("firstChoice"):
            self._sessionFilterName="sessionfirstpriority"
        else:
            self._sessionFilterName="session"

        filterUsed=params.has_key("OK")
        filter = {}

        sessform =regForm.getSessionsForm()
        sesstypes = sessform.getSessionList()
        lsessions = []
        if not filterUsed:
            for sess in sesstypes:
                lsessions.append( sess.getId() )
        filter[self._sessionFilterName]=self._normaliseListParam(params.get("session",lsessions))

        self._filterCrit=regFilters.RegFilterCrit(self._conf,filter)
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
