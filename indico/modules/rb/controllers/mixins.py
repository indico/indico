# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.


class RoomBookingAvailabilityParamsMixin:
    def _checkParamsRepeatingPeriod( self, params ):
        """
        Extracts startDT, endDT and repeatability
        from the form, if present.

        Assigns these values to self, or Nones if values
        are not present.
        """

        sDay = params.get( "sDay" )
        eDay = params.get( "eDay" )
        sMonth = params.get( "sMonth" )
        eMonth = params.get( "eMonth" )
        sYear = params.get( "sYear" )
        eYear = params.get( "eYear" )

        if sDay and len( sDay.strip() ) > 0:
            sDay = int( sDay.strip() )

        if eDay and len( eDay.strip() ) > 0:
            eDay = int( eDay.strip() )

        if sMonth and len( sMonth.strip() ) > 0:
            sMonth = int( sMonth.strip() )

#        if sYear and sMonth and sDay:
#            # For format checking
#            try:
#                time.strptime(sDay.strip() + "/" + sMonth.strip() + "/" + sYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The Start Date must be of the form DD/MM/YYYY and must be a valid date."))

        if eMonth and len( eMonth.strip() ) > 0:
            eMonth = int( eMonth.strip() )

        if sYear and len( sYear.strip() ) > 0:
            sYear = int( sYear.strip() )

        if eYear and len( eYear.strip() ) > 0:
            eYear = int( eYear.strip() )

#        if eYear and eMonth and eDay:
#            # For format checking
#            try:
#                time.strptime(eDay.strip() + "/" + eMonth.strip() + "/" + eYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The End Date must be of the form DD/MM/YYYY and must be a valid date."))


        sTime = params.get( "sTime" )
        if sTime and len( sTime.strip() ) > 0:
            sTime = sTime.strip()
        eTime = params.get( "eTime" )
        if eTime and len( eTime.strip() ) > 0:
            eTime = eTime.strip()

        # process sTime and eTime
        if sTime and eTime:

            try:
                time.strptime(sTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The Start Time must be of the form HH:MM and must be a valid time."))

            t = sTime.split( ':' )
            sHour = int( t[0] )
            sMinute = int( t[1] )

            try:
                time.strptime(eTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The End Time must be of the form HH:MM and must be a valid time."))

            t = eTime.split( ':' )
            eHour = int( t[0] )
            eMinute = int( t[1] )

        repeatability = params.get( "repeatability" )
        if repeatability and len( repeatability.strip() ) > 0:
            if repeatability == "None":
                repeatability = None
            else:
                repeatability = int( repeatability.strip() )

        self._startDT = None
        self._endDT = None
        self._repeatability = repeatability

        if sYear and sMonth and sDay and sTime and eYear and eMonth and eDay and eTime:
            # Full period specified
            self._startDT = datetime( sYear, sMonth, sDay, sHour, sMinute )
            self._endDT = datetime( eYear, eMonth, eDay, eHour, eMinute )
        elif sYear and sMonth and sDay and eYear and eMonth and eDay:
            # There are no times
            self._startDT = datetime( sYear, sMonth, sDay, 0, 0, 0 )
            self._endDT = datetime( eYear, eMonth, eDay, 23, 59, 59 )
        elif sTime and eTime:
            # There are no dates
            self._startDT = datetime( 1990, 1, 1, sHour, sMinute )
            self._endDT = datetime( 2030, 12, 31, eHour, eMinute )
        self._today=False
        if params.get( "day", "" ) == "today":
            self._today=True
            self._startDT = datetime.today().replace(hour=0,minute=0,second=0)
            self._endDT = self._startDT.replace(hour=23,minute=59,second=59)


class AttributeSetterMixin():

    """ Utility class to make retrieval of parameters from requests """

    def setParam(self, attrName, params, paramName=None, default=None, callback=None):
        """ Sets the given attribute from params
            If there is no value to set, uses default
            Otherwise, auto strips and if callback given, pre-processes value and then sets
        """
        if not paramName:
            paramName = attrName
        val = params.get(paramName)
        if val and val.strip():
            val = val.strip()
            if callback:
                val = callback(val)
            setattr(self, attrName, val)
        else:
            setattr(self, attrName, default)
