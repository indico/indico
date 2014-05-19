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

from flask import request
from indico.core.db import db

from indico.core.errors import IndicoError
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.controllers.admin import RHRoomBookingAdminBase


class RHRoomBookingDeleteBooking(RHRoomBookingAdminBase):
    def _checkParams(self):
        resv_id = request.view_args.get('resvID')
        self._reservation = Reservation.get(request.view_args['resvID'])
        if not self._reservation:
            raise IndicoError('No booking with id: {}'.format(resv_id))

    def _process(self):
        # Booking deletion is always possible - just delete
        db.session.delete(self._reservation)
        # TODO: flash message, redirect to <somewhere>
        # session['rbTitle'] = _("Booking has been deleted.")
        # session['rbDescription'] = _("You have successfully deleted the booking.")
        # url = urlHandlers.UHRoomBookingStatement.getURL()
        # self._redirect(url)  # Redirect to deletion confirmation
        return 'Deleted.'
