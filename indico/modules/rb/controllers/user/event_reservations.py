# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
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

from indico.core.errors import NoReportError
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.user.reservations import (RHRoomBookingBookingDetails, RHRoomBookingModifyBooking,
                                                             RHRoomBookingCloneBooking)
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.views.user.event_reservations import (WPRoomBookingEventBookingList,
                                                             WPRoomBookingEventBookingDetails,
                                                             WPRoomBookingEventModifyBooking,
                                                             WPRoomBookingEventNewBookingSimple)
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHRoomBookingEventBase(RHConferenceModifBase, RHRoomBookingBase):
    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        RHRoomBookingBase._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf
        try:
            self.event_id = int(self.event.getId())
        except ValueError:
            raise NoReportError(_('Room booking tools are not available for legacy events.'))


class RHRoomBookingEventBookingList(RHRoomBookingEventBase):
    def _process(self):
        reservations = Reservation.find_all(event_id=self.event_id)
        return WPRoomBookingEventBookingList(self, self.event, reservations=reservations).display()


class RHRoomBookingEventBookingDetails(RHRoomBookingEventBase, RHRoomBookingBookingDetails):
    def __init__(self):
        RHRoomBookingBookingDetails.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingBookingDetails._checkParams(self)

    def _get_view(self):
        return WPRoomBookingEventBookingDetails(self, self.event)

    def _process(self):
        return RHRoomBookingBookingDetails._process(self)


class RHRoomBookingEventBookingModifyBooking(RHRoomBookingEventBase, RHRoomBookingModifyBooking):
    def __init__(self):
        RHRoomBookingModifyBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingModifyBooking._checkParams(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventModifyBooking(self, self.event, **kwargs)

    def _get_success_url(self):
        return url_for('event_mgmt.rooms_booking_details', self.event, self._reservation)

    def _process(self):
        return RHRoomBookingModifyBooking._process(self)


class RHRoomBookingEventBookingCloneBooking(RHRoomBookingEventBase, RHRoomBookingCloneBooking):
    def __init__(self):
        RHRoomBookingCloneBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingCloneBooking._checkParams(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventNewBookingSimple(self, self.event, **kwargs)

    def _get_success_url(self, booking):
        return url_for('event_mgmt.rooms_booking_details', self.event, booking)

    def _create_booking(self, form, room):
        booking = RHRoomBookingCloneBooking._create_booking(self, form, room)
        booking.event_id = self.event_id
        return booking

    def _process(self):
        return RHRoomBookingCloneBooking._process(self)
