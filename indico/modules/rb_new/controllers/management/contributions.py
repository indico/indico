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

from indico.modules.events.contributions import Contribution
from indico.modules.events.management.controllers import RHManageEventBase


class RHListOtherContributions(RHManageEventBase):
    """AJAX endpoint that lists all contributions in the event (dict representation)."""

    def _process(self):

        query = (Contribution.query
                 .with_parent(self.event)
                 .filter(Contribution.is_scheduled)
                 .filter(Contribution.room_reservation_link == None)
                 .order_by(Contribution.friendly_id))

        result = [{'id': contrib.id, 'friendly_id': contrib.friendly_id, 'title': contrib.title,
                   'full_title': '#{}: {}'.format(contrib.friendly_id, contrib.title)}
                  for contrib in query
                  if contrib.can_access(session.user)]
        return jsonify(result)
