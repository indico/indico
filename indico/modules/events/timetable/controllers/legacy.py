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

from collections import Counter

import dateutil.parser
from flask import request, jsonify
from werkzeug.exceptions import BadRequest

from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.operations import create_contribution
from indico.modules.events.sessions.controllers.management.sessions import RHCreateSession
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.controllers import RHManageTimetableBase
from indico.modules.events.timetable.forms import BreakEntryForm, ContributionEntryForm, SessionBlockEntryForm
from indico.modules.events.timetable.legacy import serialize_contribution, serialize_entry_update, serialize_session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.operations import (create_break_entry, create_session_block_entry,
                                                        schedule_contribution)
from indico.modules.events.timetable.util import find_earliest_gap
from indico.modules.events.util import get_random_color
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


class RHLegacyTimetableAddBreak(RHManageTimetableBase):
    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.day = dateutil.parser.parse(request.args['day']).date()

    def _process(self):
        inherited_location = self.event_new.location_data
        inherited_location['inheriting'] = True
        breaks = Break.query.filter(Break.timetable_entry.has(event_new=self.event_new)).all()
        common_colors = Counter(b.colors for b in breaks)
        most_common = common_colors.most_common(1)
        colors = most_common[0][0] if most_common else get_random_color(self.event_new)
        defaults = FormDefaults(colors=colors, location_data=inherited_location)
        form = BreakEntryForm(event=self.event_new, day=self.day, obj=defaults)
        if form.validate_on_submit():
            entry = create_break_entry(self.event_new, form.data)
            return jsonify_data(entry=serialize_entry_update(entry), flash=False)
        return jsonify_form(form, fields=form._display_fields)


class RHLegacyTimetableAddContribution(RHManageTimetableBase):
    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.day = dateutil.parser.parse(request.args['day']).date()

    def _process(self):
        inherited_location = self.event_new.location_data
        inherited_location['inheriting'] = True
        defaults = FormDefaults(location_data=inherited_location)
        form = ContributionEntryForm(event=self.event_new, day=self.day, to_schedule=True, obj=defaults)
        if form.validate_on_submit():
            contrib = create_contribution(self.event_new, form.data)
            return jsonify_data(entries=[serialize_entry_update(contrib.timetable_entry)], flash=False)
        self.commit = False
        return jsonify_form(form, fields=form._display_fields)


class RHLegacyTimetableAddSessionBlock(RHManageTimetableBase):
    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.day = dateutil.parser.parse(request.args['day']).date()
        self.session = Session.find_one(id=request.args['session'], event_new=self.event_new, is_deleted=False)

    def _process(self):
        inherited_location = self.event_new.location_data
        inherited_location['inheriting'] = True
        defaults = FormDefaults(location_data=inherited_location)
        form = SessionBlockEntryForm(event=self.event_new, day=self.day, obj=defaults)
        if form.validate_on_submit():
            entry = create_session_block_entry(self.session, form.data)
            return jsonify_data(entry=serialize_entry_update(entry), flash=False)
        self.commit = False
        return jsonify_form(form, fields=form._display_fields)


class RHLegacyTimetableAddSession(RHCreateSession):
    def _get_response(self, new_session):
        return jsonify_data(session=serialize_session(new_session))


class RHLegacyTimetableGetUnscheduledContributions(RHManageTimetableBase):
    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        try:
            # no need to validate whether it's in the event; we just
            # use it to filter the event's contribution list
            self.session_id = int(request.args['session_id'])
        except KeyError:
            self.session_id = None

    def _process(self):
        contributions = Contribution.query.with_parent(self.event_new).filter_by(is_scheduled=False)
        contributions = [c for c in contributions if c.session_id == self.session_id]
        return jsonify(contributions=[serialize_contribution(x) for x in contributions])


class RHLegacyTimetableScheduleContribution(RHManageTimetableBase):
    def _process(self):
        data = request.json
        required_keys = {'contribution_ids', 'day'}
        allowed_keys = required_keys
        if data.viewkeys() > allowed_keys:
            raise BadRequest('Invalid keys found')
        elif required_keys > data.viewkeys():
            raise BadRequest('Required keys missing')
        entries = []
        day = dateutil.parser.parse(data['day']).date()
        query = Contribution.query.with_parent(self.event_new).filter(Contribution.id.in_(data['contribution_ids']))
        for contribution in query:
            start_dt = find_earliest_gap(self.event_new, day, contribution.duration)
            # TODO: handle scheduling not-fitting contributions
            if start_dt:
                entries.append(schedule_contribution(contribution, start_dt=start_dt))
        return jsonify(entries=[serialize_entry_update(x) for x in entries])
