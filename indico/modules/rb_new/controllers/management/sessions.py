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

from flask import jsonify, session

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.blocks import SessionBlock


class RHListOtherSessionBlocks(RHManageEventBase):
    """AJAX endpoint that lists all session blocks in the event (dict representation)."""

    def _process(self):

        query = (SessionBlock.query
                 .filter(SessionBlock.session.has(event=self.event))
                 .filter(SessionBlock.room_reservation_link == None)
                 .join(Session)
                 .order_by(Session.friendly_id))

        result = [{'id': session_block.id, 'friendly_id': session_block.session.friendly_id,
                   'title': session_block.full_title,
                   'full_title': '#{}: {}'.format(session_block.session.friendly_id, session_block.full_title)}
                  for session_block in query
                  if session_block.can_access(session.user)]
        return jsonify(result)
