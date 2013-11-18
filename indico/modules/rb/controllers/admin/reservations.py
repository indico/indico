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

from indico.modules.rb.controllers.admin import RHRoomBookingAdminBase


class RHRoomBookingDeleteBooking( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _process( self ):
        # Booking deletion is always possible - just delete
        self._resv.remove()
        session['rbTitle'] = _("Booking has been deleted.")
        session['rbDescription'] = _("You have successfully deleted the booking.")
        url = urlHandlers.UHRoomBookingStatement.getURL()
        self._redirect( url ) # Redirect to deletion confirmation
