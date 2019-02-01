# This file is part of Indico.
# Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from indico.modules.events.contributions import Contribution
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.rb.controllers.user.event import RHRoomBookingEventBase
from indico.modules.rb_new.forms.bookings import BookingListForm
from indico.modules.rb_new.views.base import WPEventBookingList


class RHEventBookingList(RHRoomBookingEventBase):
    def _process(self):
        form = BookingListForm(event=self.event)
        reservations = self.event.reservations
        has_unlinked_contribs = (Contribution.query.with_parent(self.event)
                                 .filter(Contribution.is_scheduled)
                                 .filter(Contribution.room_reservation_link == None).has_rows())
        has_unlinked_session_blocks = (SessionBlock.query
                                       .filter(SessionBlock.session.has(event=self.event))
                                       .filter(SessionBlock.room_reservation_link == None)).has_rows()
        return WPEventBookingList.render_template('booking_list.html', self.event, form=form, reservations=reservations,
                                                  has_unlinked_contribs=has_unlinked_contribs,
                                                  has_unlinked_session_blocks=has_unlinked_session_blocks)
