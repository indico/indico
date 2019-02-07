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

import json

from flask import jsonify

from indico.modules.events.contributions import Contribution
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.rb.controllers.user.event import RHRoomBookingEventBase
from indico.modules.rb_new.event.forms import BookingListForm
from indico.modules.rb_new.views.base import WPEventBookingList
from indico.util.date_time import format_datetime, format_time
from indico.util.string import to_unicode


class RHEventBookingList(RHRoomBookingEventBase):
    def _process(self):
        form = BookingListForm(event=self.event)
        reservations = self.event.reservations
        has_unlinked_contribs = (Contribution.query.with_parent(self.event)
                                 .filter(Contribution.is_scheduled,
                                         Contribution.room_reservation_links == None)  # noqa
                                 .has_rows())
        has_unlinked_session_blocks = (SessionBlock.query
                                       .filter(SessionBlock.session.has(event=self.event),
                                               SessionBlock.room_reservation_links == None)  # noqa
                                       .has_rows())

        is_single_day = self.event.start_dt.date() == self.event.end_dt.date()
        event_rb_params = {'link_type': 'event',
                           'link_id': self.event.id,
                           'recurrence': 'single' if is_single_day else 'daily',
                           'number': 1,
                           'interval': 'week',
                           'sd': self.event.start_dt_local.date().isoformat(),
                           'ed': None if is_single_day else self.event.end_dt_local.date().isoformat(),
                           'st': format_time(self.event.start_dt_local.time()),
                           'et': format_time(self.event.end_dt_local.time()),
                           'text': self.event.room.name if self.event.room else None}

        return WPEventBookingList.render_template('booking_list.html', self.event,
                                                  form=form, reservations=reservations,
                                                  has_unlinked_contribs=has_unlinked_contribs,
                                                  has_unlinked_session_blocks=has_unlinked_session_blocks,
                                                  event_rb_params=event_rb_params)


class RHListLinkableContributions(RHManageEventBase):
    """AJAX endpoint that lists all contributions in the event."""

    def _process(self):
        query = (Contribution.query
                 .with_parent(self.event)
                 .filter(Contribution.is_scheduled, Contribution.room_reservation_links == None)  # noqa
                 .order_by(Contribution.friendly_id))

        result = [{'value': json.dumps({'id': contrib.id,
                                        'start_dt': contrib.start_dt.isoformat(),
                                        'end_dt': contrib.end_dt.isoformat()}),
                   'friendly_id': contrib.friendly_id, 'title': contrib.title,
                   'full_title': contrib.verbose_title}
                  for contrib in query]
        return jsonify(result)


class RHListLinkableSessionBlocks(RHManageEventBase):
    """AJAX endpoint that lists all session blocks in the event."""

    def _process(self):
        query = (SessionBlock.query
                 .filter(SessionBlock.session.has(event=self.event), SessionBlock.room_reservation_links == None)  # noqa
                 .join(Session)
                 .order_by(Session.friendly_id))

        result = [{'value': json.dumps({'id': session_block.id,
                                        'start_dt': session_block.start_dt.isoformat(),
                                        'end_dt': session_block.end_dt.isoformat()}),
                   'friendly_id': session_block.session.friendly_id, 'title': session_block.full_title,
                   'full_title': '#{}: {} ({})'.format(
                       session_block.session.friendly_id, session_block.full_title,
                       to_unicode(format_datetime(session_block.timetable_entry.start_dt))
                   )}
                  for session_block in query]
        return jsonify(result)
