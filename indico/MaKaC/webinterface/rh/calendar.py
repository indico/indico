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


import MaKaC.webinterface.rh.base as base
import MaKaC.conference as conference
import MaKaC.webinterface.wcalendar as wcalendar
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.conf_calendar as calendar
from MaKaC.common.timezoneUtils import nowutc, DisplayTZ
from datetime import datetime
from pytz import timezone
from MaKaC.errors import AccessError

from dateutil.relativedelta import relativedelta


class RHCalendar(base.RHProtected):
    _uh = urlHandlers.UHCalendar

    def _checkProtection(self):
        if self._getUser() == None:
            self._checkSessionUser()
        categNoAccess = []

        for item in self._categList[:]:
            if not item.canAccess(self.getAW()):
                categNoAccess.append(item)
                self._categList.remove(item)
        if len(self._categList) > 0:
            self._target = self._categList
            self._categ = self._categList[0]
        else:
            # 'categNoAccess' is necessary in order to be able to retrieve the
            # 'Contact Info' from all categs the user has no access (see WAccessError)
            self._target = categNoAccess
            raise AccessError()

    def _checkParams(self, params):
        categIdList = self._normaliseListParam(params.get("selCateg", []))
        self._categList = []
        cm = conference.CategoryManager()
        for id in categIdList:
            try:
                self._categList.append(cm.getById(id))
            except KeyError:
                continue
        self._target = self._categList
        if not self._categList:
            cm = conference.CategoryManager()
            self._categList.append(cm.getRoot())
        tz = DisplayTZ(self._aw).getDisplayTZ()
        months = params.get("months", 3)
        columns = params.get("columns", 3)
        startDate = nowutc() - relativedelta(months=1)
        month = int(params.get("month", startDate.astimezone(timezone(tz)).month))
        year = int(params.get("year", startDate.astimezone(timezone(tz)).year))
        sdate = timezone(tz).localize(datetime(year, month, 1))
        self._cal = wcalendar.MonthCalendar(self._aw,
                                            sdate,
                                            months,
                                            columns,
                                            self._categList)
        self._categ = self._categList[0]

    def _process( self ):
        p = calendar.WPCalendar( self, self._cal, self._categ )
        return p.display()


class RHCalendarSelectCategories( base.RH ):
    _uh = urlHandlers.UHCalendarSelectCategories

    def _checkParams( self, params ):
        categIdList = self._normaliseListParam( params.get("selCateg", []) )
        self._categList = []
        cm = conference.CategoryManager()
        for id in categIdList:
            self._categList.append( cm.getById(id) )
        tz = DisplayTZ(self._aw).getDisplayTZ()
        sdate = timezone(tz).localize(datetime(int(params.get("sDate", "")[0:4]),\
                                    int(params.get("sDate", "")[5:7]),\
                                    int(params.get("sDate", "")[8:])))
        months = params.get("months", 6)
        self._cal = wcalendar.MonthCalendar( self._aw, \
                                                sdate, \
                                                months, \
                                                3, \
                                                self._categList )
        xs = self._normaliseListParam( params.get("xs", []) )
        self._expanded = []
        for id in xs:
            self._expanded.append( cm.getById( id ) )

    def _process( self ):
        p = calendar.WPCalendarSelectCategories( self, self._cal )
        return p.display( expanded=self._expanded )
