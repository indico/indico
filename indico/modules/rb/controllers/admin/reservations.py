# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import flash, redirect, request, url_for

from indico.core.db import db
from indico.modules.rb.controllers.admin import RHRoomBookingAdminBase
from indico.modules.rb.models.reservations import Reservation
from indico.util.i18n import _


class RHRoomBookingDeleteBooking(RHRoomBookingAdminBase):
    def _process_args(self):
        self._reservation = Reservation.get_one(request.view_args['resvID'])

    def _process(self):
        db.session.delete(self._reservation)
        flash(_(u'Booking deleted'), 'success')
        return redirect(url_for('rooms.roomBooking-search4Bookings'))
