# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import dateutil.parser
from flask import request, jsonify, render_template
from werkzeug.exceptions import BadRequest

from indico.modules.events.contributions import Contribution
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.legacy import TimetableSerializer
from indico.modules.events.timetable.controllers import RHManageTimetableBase
from indico.modules.events.timetable.operations import (create_timetable_entry, update_timetable_entry,
                                                        delete_timetable_entry)
from indico.modules.events.timetable.views import WPManageTimetable
from indico.modules.events.timetable.util import serialize_event_info
from indico.modules.events.util import track_time_changes


class RHManageTimetable(RHManageTimetableBase):
    """Display timetable management page"""

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.layout = request.args.get('layout', None)
        if not self.layout:
            self.layout = request.args.get('ttLyt', None)

    def _process(self):
        event_info = serialize_event_info(self.event_new)
        timetable_data = TimetableSerializer(management=True).serialize_timetable(self.event_new)
        return WPManageTimetable.render_template('management.html', self._conf, event_info=event_info,
                                                 timetable_data=timetable_data, timetable_layout=self.layout)


class RHTimetableREST(RHManageTimetableBase):
    """RESTful timetable actions"""

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.timetable_entry = None
        if 'timetable_entry_id' in request.view_args:
            self.timetable_entry = (self.event_new.timetable_entries
                                    .filter_by(id=request.view_args['timetable_entry_id'])
                                    .first_or_404())

    def _get_contribution_updates(self, data):
        updates = {'parent': None}
        contribution = Contribution.query.with_parent(self.event_new).filter_by(id=data['contribution_id']).first()
        if contribution is None:
            raise BadRequest('Invalid contribution id')
        elif contribution.timetable_entry is not None:
            raise BadRequest('The contribution is already scheduled')
        updates['object'] = contribution
        if data.get('session_block_id'):
            session_block = self.event_new.get_session_block(data['session_block_id'])
            if session_block is None:
                raise BadRequest('Invalid session block id')
            if session_block.timetable_entry is None:
                raise BadRequest('The session block is not scheduled')
            if contribution.session and session_block.session != contribution.session and not data.get('force'):
                raise BadRequest('Contribution is assigned to another session')
            updates['parent'] = session_block.timetable_entry
            contribution.session = session_block.session
        else:
            updates['object'].session = None

        return updates

    def _process_POST(self):
        """Create new timetable entry"""
        data = request.json
        required_keys = {'start_dt'}
        allowed_keys = {'start_dt', 'contribution_id', 'session_block_id', 'force'}
        if data.viewkeys() > allowed_keys:
            raise BadRequest('Invalid keys found')
        elif required_keys > data.viewkeys():
            raise BadRequest('Required keys missing')
        updates = {'start_dt': dateutil.parser.parse(data['start_dt'])}
        if 'contribution_id' in data:
            updates.update(self._get_contribution_updates(data))
        # TODO: breaks & session blocks
        else:
            raise BadRequest('No object specified')
        entry = create_timetable_entry(self.event_new, updates)
        return jsonify(start_dt=entry.start_dt.isoformat(), id=entry.id)

    def _process_PATCH(self):
        """Update a timetable entry"""
        data = request.json
        # TODO: support breaks
        if data.viewkeys() > {'start_dt'}:
            raise BadRequest('Invalid keys found')
        updates = {}
        if 'start_dt' in data:
            updates['start_dt'] = dateutil.parser.parse(data['start_dt'])
        if updates:
            with track_time_changes():
                update_timetable_entry(self.timetable_entry, updates)
        return jsonify()

    def _process_DELETE(self):
        """Delete a timetable entry"""
        delete_timetable_entry(self.timetable_entry)


class RHTimetableBalloon(RHManageTimetableBase):
    """Create the appropriate timetable entry balloon depending on the entry type."""
    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.timetable_entry = (self.event_new.timetable_entries
                                .filter_by(id=request.view_args['timetable_entry_id'])
                                .first_or_404())

    def _process(self):
        html = None
        if self.timetable_entry.contribution:
            html = render_template('events/timetable/display/balloons/contribution.html',
                                   contrib=self.timetable_entry.contribution)
        elif self.timetable_entry.break_:
            html = render_template('events/timetable/display/balloons/break.html',
                                   break_=self.timetable_entry.break_)
        elif self.timetable_entry.session_block:
            html = render_template('events/timetable/display/balloons/block.html',
                                   block=self.timetable_entry.session_block)
        return jsonify(html=html)
