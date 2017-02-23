# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.errors import FormValuesError
from MaKaC.webinterface.pages import conferences
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase


class RHConferenceModifBase(RHConferenceBase, RHModificationBaseProtected):

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)

    def _displayCustomPage(self, wf):
        return None

    def _displayDefaultPage(self):
        return None

    def _process(self):
        wf = self.getWebFactory()
        if wf is not None:
            res = self._displayCustomPage(wf)
            if res is not None:
                return res
        return self._displayDefaultPage()


#######################################################################################

class RHConfClone( RHConferenceModifBase ):
    _allowClosed = True

    def _process( self ):
        p = conferences.WPConfClone( self, self._conf )
        wf=self.getWebFactory()
        if wf is not None:
            p = wf.getConfClone(self, self._conf)
        return p.display()


class RHConfPerformCloning(RHConferenceModifBase, object):
    """
    New version of clone functionality -
    fully replace the old one, based on three different actions,
    adds mechanism of selective cloning of materials and access
    privileges attached to an event
    """
    _cloneType = "none"
    _allowClosed = True

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._date = datetime.today()
        self._cloneType = params.get("cloneType", None)
        if self._cloneType is None:
            raise FormValuesError( _("""Please choose a cloning interval for this event"""))
        elif self._cloneType == "once" :
            self._date = datetime( int(params["stdyo"]),
                                int(params["stdmo"]),
                                int(params["stddo"]),
                                int(self.event_new.start_dt_local.hour),
                                int(self.event_new.start_dt_local.minute))
        elif self._cloneType == "intervals" :
            self._date = datetime( int(params["indyi"]),
                                int(params["indmi"]),
                                int(params["inddi"]),
                                int(self.event_new.start_dt_local.hour),
                                int(self.event_new.start_dt_local.minute))
        elif self._cloneType == "days" :
            self._date = datetime( int(params["indyd"]),
                                int(params["indmd"]),
                                int(params["inddd"]),
                                int(self.event_new.start_dt_local.hour),
                                int(self.event_new.start_dt_local.minute))
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        params = self._getRequestParams()
        paramNames = params.keys()
        #we notify the event in case any plugin wants to add their options
        if self._cancel:
            self._redirect(url_for('event_mgmt.confModifTools-clone', self.event_new))
        elif self._confirm:
            if self._cloneType == "once" :
                newConf = self._conf.clone(self._date)
                self._redirect(url_for('event_management.settings', newConf.as_event))
            elif self._cloneType == "intervals" :
                self._withIntervals()
            elif self._cloneType == "days" :
                self._days()
            else :
                self._redirect(url_for('event_mgmt.confModifTools-clone', self.event_new))
        else:
            if self._cloneType == "once" :
                nbClones = 1
            elif self._cloneType == "intervals" :
                nbClones = self._withIntervals(0)
            elif self._cloneType == "days" :
                nbClones = self._days(0)
            return conferences.WPConfCloneConfirm( self, self._conf, nbClones ).display()

    def _withIntervals(self, confirmed=1):
        nbClones = 0
        params = self._getRequestParams()
        if params["freq"] == "day":
            inter = timedelta(int(params["period"]))
        elif params["freq"] == "week":
            inter = timedelta( 7*int(params["period"]))

        if params["intEndDateChoice"] == "until":
            date=self._date
            endDate = datetime(int(params["stdyi"]), int(params["stdmi"]), int(params["stddi"]),
                               self.event_new.end_dt.hour, self.event_new.end_dt.minute)
            while date <= endDate:
                if confirmed:
                    self._conf.clone(date)
                nbClones += 1
                if params["freq"] == "day" or params["freq"] == "week":
                    date = date + inter
                elif params["freq"] == "month":
                    month = int(date.month) + int(params["period"])
                    year = int(date.year)
                    while month > 12:
                        month = month - 12
                        year = year + 1
                    date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
                elif params["freq"] == "year":
                    date = datetime(int(date.year)+int(params["period"]),int(date.month),int(date.day), int(date.hour), int(date.minute))

        elif params["intEndDateChoice"] == "ntimes":
            date = self._date
            i=0
            stop = int(params["numi"])
            while i < stop:
                i = i + 1
                if confirmed:
                    self._conf.clone(date)
                nbClones += 1
                if params["freq"] == "day" or params["freq"] == "week":
                    date = date + inter
                elif params["freq"] == "month":
                    month = int(date.month) + int(params["period"])
                    year = int(date.year)
                    while month > 12:
                        month = month - 12
                        year = year + 1
                    date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
                elif params["freq"] == "year":
                    date = datetime(int(date.year)+int(params["period"]),int(date.month),int(date.day), int(date.hour), int(date.minute))
        if confirmed:
            self._redirect(self._conf.as_event.category.url)
            return "done"
        else:
            return nbClones

    def _getFirstDay(self, date, day):
        """
        return the first day 'day' for the month of 'date'
        """
        td = datetime(int(date.year), int(date.month), 1, int(date.hour), int(date.minute))

        oneDay = timedelta(1)
        while 1:
            if td.weekday() == day:
                return td
            td = td + oneDay

    def _getOpenDay(self, date, day):
        """
        return the first open day for the month of 'date'
        """
        if day!="last": # last open day of the month
            td = datetime(int(date.year), int(date.month), int(date.day), int(date.hour), int(date.minute))
            if td.weekday() > 4:
                td = td + timedelta(7 - td.weekday())
            td += timedelta(int(day)-1)
        else:
            td = self._getLastDay(date, -1)
            if td.weekday() > 4:
                td = td - timedelta(td.weekday() - 4)
        return td

    def _getLastDay(self, date, day):
        """
        return the last day 'day' for the month of 'date'
        """
        td = datetime(int(date.year), int(date.month), 28, int(date.hour), int(date.minute))
        month=td.month
        while td.month == month:
            td += timedelta(1)
        td -= timedelta(1)
        if day==-1:
            return td
        else:
            while 1:
                if td.weekday() == day:
                    return td
                td = td - timedelta(1)

    def _days(self, confirmed=1):
        nbClones = 0
        params = self._getRequestParams()
        #search the first day of the month

        if params["day"] == "NOVAL":
            self.redirect(url_for('event_mgmt.confModifTools-clone', self.event_new))

        if params["daysEndDateChoice"] == "until":
            date = self._date

            endDate = datetime(int(params["stdyd"]), int(params["stdmd"]), int(params["stddd"]),
                               self.event_new.end_dt.hour, self.event_new.end_dt.minute)

            if params["day"] == "OpenDay":
                rd = self._getOpenDay(date, params["order"])
            else:
                if params["order"] == "last":
                    rd = self._getLastDay(date, int(params["day"]))
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
            while date <= endDate:
                if params["day"] == "OpenDay":
                    od=self._getOpenDay(date,params["order"])
                    if od <= endDate:
                        if confirmed:
                            self._conf.clone(od)
                        nbClones += 1
                else:
                    if params["order"] == "last":
                        if self._getLastDay(date,int(params["day"])) <= endDate:
                            if confirmed:
                                self._conf.clone(self._getLastDay(date, int(params["day"])))
                            nbClones += 1
                    else:
                        new_date = (self._getFirstDay(date, int(params["day"])) +
                                    timedelta((int(params["order"]) - 1) * 7))
                        if new_date <= endDate:
                            if confirmed:
                                self._conf.clone(new_date)
                            nbClones += 1
                month = int(date.month) + int(params["monthPeriod"])
                year = int(date.year)
                while month > 12:
                    month = month - 12
                    year = year + 1
                date = datetime(year,month,1, int(date.hour), int(date.minute))

        elif params["daysEndDateChoice"] == "ntimes":

            date = self._date
            if params["day"] == "OpenDay":
                rd = self._getOpenDay(date,params["order"])
            else:
                if params["order"] == "last":
                    rd = self._getLastDay(date, int(params["day"]))
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)

            i=0
            stop = int(params["numd"])
            while i < stop:
                i = i + 1
                if params["day"] == "OpenDay":
                    if confirmed:
                        self._conf.clone(self._getOpenDay(date, params["order"]))
                    nbClones += 1
                else:
                    if params["order"] == "last":
                        if confirmed:
                            self._conf.clone(self._getLastDay(date, int(params["day"])))
                        nbClones += 1
                    else:
                        if confirmed:
                            new_date = (self._getFirstDay(date, int(params["day"])) +
                                        timedelta((int(params["order"]) - 1) * 7))
                            self._conf.clone(new_date)
                        nbClones += 1
                month = int(date.month) + int(params["monthPeriod"])
                year = int(date.year)
                while month > 12:
                    month = month - 12
                    year = year + 1
                date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
        if confirmed:
            self._redirect(self._conf.as_event.category.url)
        else:
            return nbClones
