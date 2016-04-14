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
from datetime import timedelta
from operator import attrgetter

import dateutil.parser
from flask import request, jsonify, session
from pytz import utc
from werkzeug.exceptions import BadRequest, NotFound

from indico.core.errors import UserValueError
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.controllers.management import _get_field_values
from indico.modules.events.contributions.operations import create_contribution, delete_contribution, update_contribution
from indico.modules.events.models.events import Event
from indico.modules.events.sessions.controllers.management.sessions import RHCreateSession
from indico.modules.events.sessions.forms import SessionForm
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.operations import delete_session_block, update_session_block, update_session
from indico.modules.events.timetable.controllers import (RHManageTimetableBase, RHManageTimetableEntryBase,
                                                         SessionManagementLevel)
from indico.modules.events.timetable.forms import (BreakEntryForm, ContributionEntryForm, SessionBlockEntryForm,
                                                   BaseEntryForm)
from indico.modules.events.timetable.legacy import (serialize_contribution, serialize_entry_update, serialize_session,
                                                    TimetableSerializer)
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.operations import (create_break_entry, create_session_block_entry,
                                                        schedule_contribution, fit_session_block_entry,
                                                        update_break_entry, update_timetable_entry,
                                                        move_timetable_entry, update_timetable_entry_object,
                                                        delete_timetable_entry)
from indico.modules.events.timetable.reschedule import Rescheduler, RescheduleMode
from indico.modules.events.timetable.util import (find_next_start_dt, get_session_block_entries,
                                                  shift_subsequent_entries)
from indico.modules.events.util import get_random_color, track_time_changes
from indico.util.date_time import format_time, iterdays, as_utc
from indico.util.i18n import _
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHLegacyTimetableAddEntryBase(RHManageTimetableBase):
    session_management_level = SessionManagementLevel.manage

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.day = dateutil.parser.parse(request.args['day']).date()
        self.session_block = None
        if 'session_block_id' in request.args:
            self.session_block = self.event_new.get_session_block(request.args['session_block_id'])
            if not self.session_block:
                raise BadRequest

    def _get_form_defaults(self, **kwargs):
        inherited_location = self.event_new.location_data
        inherited_location['inheriting'] = True
        return FormDefaults(location_data=inherited_location, **kwargs)

    def _get_form_params(self):
        return {'event': self.event_new,
                'session_block': self.session_block,
                'day': self.day}


class RHLegacyTimetableAddBreak(RHLegacyTimetableAddEntryBase):
    session_management_level = SessionManagementLevel.coordinate

    def _get_default_colors(self):
        breaks = Break.query.filter(Break.timetable_entry.has(event_new=self.event_new)).all()
        common_colors = Counter(b.colors for b in breaks)
        most_common = common_colors.most_common(1)
        colors = most_common[0][0] if most_common else get_random_color(self.event_new)
        return colors

    def _process(self):
        colors = self._get_default_colors()
        defaults = self._get_form_defaults(colors=colors)
        form = BreakEntryForm(obj=defaults, **self._get_form_params())
        if form.validate_on_submit():
            entry = create_break_entry(self.event_new, form.data, session_block=self.session_block)
            return jsonify_data(entry=serialize_entry_update(entry), flash=False)
        return jsonify_form(form, fields=form._display_fields)


class RHLegacyTimetableAddContribution(RHLegacyTimetableAddEntryBase):
    session_management_level = SessionManagementLevel.manage

    def _process(self):
        defaults = self._get_form_defaults()
        form = ContributionEntryForm(obj=defaults, to_schedule=True, **self._get_form_params())
        if form.validate_on_submit():
            contrib = create_contribution(self.event_new, form.data, session_block=self.session_block)
            return jsonify_data(entries=[serialize_entry_update(contrib.timetable_entry)], flash=False)
        self.commit = False
        return jsonify_template('events/contributions/forms/contribution.html', form=form, fields=form._display_fields)


class RHLegacyTimetableAddSessionBlock(RHLegacyTimetableAddEntryBase):
    session_management_level = SessionManagementLevel.coordinate_with_blocks

    def _checkParams(self, params):
        RHLegacyTimetableAddEntryBase._checkParams(self, params)
        if not self.session:
            self.session = self.event_new.get_session(request.args['session_id'])
            if not self.session:
                raise NotFound

    def _process(self):
        defaults = self._get_form_defaults()
        form = SessionBlockEntryForm(obj=defaults, **self._get_form_params())
        if form.validate_on_submit():
            entry = create_session_block_entry(self.session, form.data)
            return jsonify_data(entry=serialize_entry_update(entry), flash=False)
        self.commit = False
        return jsonify_form(form, fields=form._display_fields, disabled_until_change=False)


class RHLegacyTimetableDeleteEntry(RHManageTimetableEntryBase):
    @property
    def session_management_level(self):
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            return SessionManagementLevel.coordinate_with_blocks
        elif self.entry.type == TimetableEntryType.CONTRIBUTION and self.event_new.type != 'conference':
            return SessionManagementLevel.coordinate_with_contribs
        else:
            return SessionManagementLevel.coordinate

    def _process(self):
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            delete_session_block(self.entry.session_block)
        elif self.entry.type == TimetableEntryType.CONTRIBUTION and self.event_new.type != 'conference':
            delete_contribution(self.entry.contribution)
        else:
            delete_timetable_entry(self.entry)
        return jsonify_data(flash=False)


class RHLegacyTimetableEditEntry(RHManageTimetableEntryBase):
    @property
    def session_management_level(self):
        if self.edit_session:
            return SessionManagementLevel.manage
        elif self.entry.type == TimetableEntryType.SESSION_BLOCK:
            return SessionManagementLevel.coordinate_with_blocks
        elif self.entry.type == TimetableEntryType.CONTRIBUTION:
            return SessionManagementLevel.coordinate_with_contribs
        else:
            return SessionManagementLevel.coordinate

    def _checkParams(self, params):
        RHManageTimetableEntryBase._checkParams(self, params)
        self.edit_session = request.args.get('edit_session') == '1'

    def _process(self):
        form = None
        if self.entry.contribution:
            contrib = self.entry.contribution
            tt_entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
            form = ContributionEntryForm(obj=FormDefaults(contrib, time=tt_entry_dt.time()),
                                         event=self.event_new, contrib=contrib, to_schedule=False,
                                         day=tt_entry_dt.date())
            if form.validate_on_submit():
                with track_time_changes():
                    update_contribution(contrib, *_get_field_values(form.data))
                return jsonify_data(entries=[serialize_entry_update(contrib.timetable_entry)], flash=False)
            return jsonify_template('events/contributions/forms/contribution.html', form=form,
                                    fields=form._display_fields)
        elif self.entry.break_:
            break_ = self.entry.break_
            tt_entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
            form = BreakEntryForm(event=self.event_new, day=tt_entry_dt.date(),
                                  obj=FormDefaults(break_, time=tt_entry_dt.time()))
            if form.validate_on_submit():
                with track_time_changes():
                    update_break_entry(break_, form.data)
                return jsonify_data(entries=[serialize_entry_update(break_.timetable_entry)], flash=False)
        elif self.entry.session_block:
            if self.edit_session:
                session_ = self.entry.session_block.session
                form = SessionForm(obj=FormDefaults(session_), event=self.event_new)
                if form.validate_on_submit():
                    update_session(session_, form.data)
                    return jsonify_data(entries=[serialize_entry_update(x.timetable_entry) for x in session_.blocks],
                                        flash=False)
            else:
                block = self.entry.session_block
                tt_entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
                form = SessionBlockEntryForm(obj=FormDefaults(block, time=tt_entry_dt.time()),
                                             event=self.event_new, session_block=block, to_schedule=False,
                                             day=tt_entry_dt.date())
                if form.validate_on_submit():
                    with track_time_changes():
                        update_session_block(block, form.data)
                    return jsonify_data(entries=[serialize_entry_update(block.timetable_entry)], flash=False)
        self.commit = False
        return jsonify_form(form, fields=getattr(form, '_display_fields', None))


class RHLegacyTimetableEditEntryTime(RHManageTimetableEntryBase):
    @property
    def session_management_level(self):
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            return SessionManagementLevel.coordinate_with_blocks
        else:
            return SessionManagementLevel.coordinate

    def _process(self):
        item = self.entry.object
        tt_entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
        form = BaseEntryForm(obj=FormDefaults(item, time=tt_entry_dt.time()), day=tt_entry_dt.date(),
                             event=self.event_new, entry=self.entry)
        data = form.data
        shift_later = data.pop('shift_later')
        updated_entries = []

        if form.validate_on_submit():
            with track_time_changes():
                if shift_later:
                    updated_entries += shift_subsequent_entries(self.event_new, self.entry, form.start_dt.data)
                if self.entry.contribution:
                    update_timetable_entry(self.entry, {'start_dt': form.start_dt.data})
                    update_contribution(item, {'duration': form.duration.data})
                elif self.entry.break_:
                    update_break_entry(item, data)
                elif self.entry.session_block:
                    update_session_block(item, data)

            updated_entries.append(item.timetable_entry)
            return jsonify_data(entries=[serialize_entry_update(entry) for entry in updated_entries], flash=False,
                                shift_later=shift_later)
        self.commit = False
        return jsonify_form(form, back_button=False, disabled_until_change=True)


class RHLegacyTimetableAddSession(RHCreateSession):
    def _get_response(self, new_session):
        return jsonify_data(session=serialize_session(new_session))


class RHLegacyTimetableGetUnscheduledContributions(RHManageTimetableBase):
    session_management_level = SessionManagementLevel.coordinate

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.session_id = None
        if 'session_block_id' in request.args:
            self.session_id = SessionBlock.get_one(request.args['session_block_id']).session_id
            if self.session and self.session.id != self.session_id:
                raise BadRequest

    def _process(self):
        contributions = Contribution.query.with_parent(self.event_new).filter_by(is_scheduled=False)
        contributions = [c for c in contributions if c.session_id == self.session_id]
        return jsonify(contributions=[serialize_contribution(x) for x in contributions])


class RHLegacyTimetableScheduleContribution(RHManageTimetableBase):
    session_management_level = SessionManagementLevel.coordinate

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.session_block = None
        if 'block_id' in request.view_args:
            self.session_block = self.event_new.get_session_block(request.view_args['block_id'])
            if self.session_block is None:
                raise NotFound

    def _process(self):
        data = request.json
        required_keys = {'contribution_ids', 'day'}
        allowed_keys = required_keys | {'session_block_id'}
        if data.viewkeys() > allowed_keys:
            raise BadRequest('Invalid keys found')
        elif required_keys > data.viewkeys():
            raise BadRequest('Required keys missing')
        entries = []
        day = dateutil.parser.parse(data['day']).date()
        query = Contribution.query.with_parent(self.event_new).filter(Contribution.id.in_(data['contribution_ids']))
        for contribution in query:
            start_dt = find_next_start_dt(contribution.duration,
                                          obj=self.session_block or self.event_new,
                                          day=None if self.session_block else day)
            # TODO: handle scheduling not-fitting contributions
            #       can only happen within session blocks that are shorter than contribution's duration
            if start_dt:
                entries.append(self._schedule(contribution, start_dt))
        return jsonify(entries=[serialize_entry_update(x) for x in entries])

    def _schedule(self, contrib, start_dt):
        return schedule_contribution(contrib, start_dt, session_block=self.session_block)


class RHLegacyTimetableReschedule(RHManageTimetableBase):
    _json_schema = {
        'type': 'object',
        'properties': {
            'mode': {'type': 'string', 'enum': ['none', 'time', 'duration']},
            'day': {'type': 'string', 'format': 'date'},
            'gap': {'type': 'integer', 'minimum': 0},
            'fit_blocks': {'type': 'boolean'},
            'session_block_id': {'type': 'integer'},
            'session_id': {'type': 'integer'}
        },
        'required': ['mode', 'day', 'gap', 'fit_blocks']
    }

    @property
    def session_management_level(self):
        if self.session_block:
            return SessionManagementLevel.coordinate
        elif self.session:
            return SessionManagementLevel.coordinate_with_blocks
        else:
            return SessionManagementLevel.none

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.validate_json(self._json_schema)
        self.day = dateutil.parser.parse(request.json['day']).date()
        self.session_block = None
        if request.json.get('session_block_id') is not None:
            self.session_block = self.event_new.get_session_block(request.json['session_block_id'], scheduled_only=True)
            if self.session_block is None:
                raise NotFound
            if self.session and self.session != self.session_block.session:
                raise BadRequest
        elif request.json.get('session_id') is not None:
            if self.session.id != request.json['session_id']:
                raise BadRequest

    def _process(self):
        sess = self.session if not self.session_block else None
        rescheduler = Rescheduler(self.event_new, RescheduleMode[request.json['mode']], self.day,
                                  session=sess, session_block=self.session_block, fit_blocks=request.json['fit_blocks'],
                                  gap=timedelta(minutes=request.json['gap']))
        with track_time_changes():
            rescheduler.run()
        return jsonify_data(flash=False)


class RHLegacyTimetableFitBlock(RHManageTimetableBase):
    session_management_level = SessionManagementLevel.coordinate_with_blocks

    def _checkParams(self, params):
        RHManageTimetableBase._checkParams(self, params)
        self.session_block = self.event_new.get_session_block(request.view_args['block_id'], scheduled_only=True)
        if self.session_block is None:
            raise NotFound
        if self.session and self.session != self.session_block.session:
            raise BadRequest

    def _process(self):
        with track_time_changes():
            fit_session_block_entry(self.session_block.timetable_entry)
        return jsonify_data(flash=False)


class RHLegacyTimetableMoveEntry(RHManageTimetableEntryBase):
    """Moves a TimetableEntry into a Session or top-level timetable"""

    def _process_GET(self):
        current_day = dateutil.parser.parse(request.args.get('day')).date()
        return jsonify_template('events/timetable/move_entry.html', event=self.event_new,
                                top_level_entries=self._get_session_timetable_entries(),
                                current_day=current_day, timetable_entry=self.entry,
                                parent_entry=self.entry.parent)

    def _process_POST(self):
        self.serializer = TimetableSerializer(True)
        with track_time_changes():
            entry_data = self._move_entry(request.json)
        rv = dict(serialize_entry_update(self.entry), **entry_data)
        return jsonify_data(flash=False, entry=rv)

    def _move_entry(self, data):
        rv = {}
        if data.get('parent_id'):
            rv['old'] = self.serializer.serialize_timetable_entry(self.entry)
            parent_timetable_entry = self.event_new.timetable_entries.filter_by(id=data['parent_id']).one()
            move_timetable_entry(self.entry, parent=parent_timetable_entry)
            rv['session'] = rv['slotEntry'] = self.serializer.serialize_session_block_entry(parent_timetable_entry)
        elif data.get('day'):
            rv['old'] = self.serializer.serialize_timetable_entry(self.entry)
            new_date = as_utc(dateutil.parser.parse(data['day']))
            move_timetable_entry(self.entry, day=new_date)
        return rv

    def _get_session_timetable_entries(self):
        entries = {}
        for day in iterdays(self.event_new.start_dt, self.event_new.end_dt):
            entries[day.date()] = get_session_block_entries(self.event_new, day)
        return entries


class RHLegacyShiftTimetableEntries(RHManageTimetableEntryBase):
    @property
    def session_management_level(self):
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            return SessionManagementLevel.coordinate_with_blocks
        else:
            return SessionManagementLevel.coordinate

    def _process(self):
        new_start_dt = (self.event_new.tzinfo.localize(dateutil.parser.parse(request.form.get('startDate')))
                        .astimezone(utc))
        if new_start_dt < self.event_new.start_dt:
            raise UserValueError(_('You cannot move the block before event start date.'))
        is_session_block = self.entry.type == TimetableEntryType.SESSION_BLOCK
        with track_time_changes():
            shift_subsequent_entries(self.event_new, self.entry, new_start_dt)
            if is_session_block:
                self.entry.move(new_start_dt)
            else:
                update_timetable_entry(self.entry, {'start_dt': new_start_dt})
        return jsonify_data(flash=False, entry=serialize_entry_update(self.entry),
                            timetable=TimetableSerializer(True).serialize_timetable(self.event_new))


class RHLegacyTimetableEditEntryDateTime(RHManageTimetableEntryBase):
    """Changes the start_dt of a `TimetableEntry`"""

    @property
    def session_management_level(self):
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            return SessionManagementLevel.coordinate_with_blocks
        else:
            return SessionManagementLevel.coordinate

    def _process(self):
        new_start_dt = self.event_new.tzinfo.localize(
            dateutil.parser.parse(request.form.get('startDate'))).astimezone(utc)
        new_end_dt = self.event_new.tzinfo.localize(dateutil.parser.parse(request.form.get('endDate'))).astimezone(utc)
        new_duration = new_end_dt - new_start_dt
        is_session_block = self.entry.type == TimetableEntryType.SESSION_BLOCK
        tzinfo = self.event_new.tzinfo
        if is_session_block and new_end_dt.astimezone(tzinfo).date() != self.entry.start_dt.astimezone(tzinfo).date():
            raise UserValueError(_('Session block cannot span more than one day'))
        if new_start_dt < self.event_new.start_dt:
            raise UserValueError(_('You cannot move the block before event start date.'))
        with track_time_changes(auto_extend=True) as changes:
            parent = self.entry.parent
            update_timetable_entry_object(self.entry, {'duration': new_duration})
            if parent and new_start_dt < parent.start_dt:
                update_timetable_entry_object(parent, {'duration': parent.end_dt - new_start_dt})
                update_timetable_entry(parent, {'start_dt': new_start_dt})
            elif parent and (new_start_dt > parent.end_dt or new_end_dt > parent.end_dt):
                update_timetable_entry_object(parent, {'duration': new_end_dt - parent.start_dt})
            if is_session_block:
                self.entry.move(new_start_dt)
            if not is_session_block:
                update_timetable_entry(self.entry, {'start_dt': new_start_dt})
        if is_session_block and self.entry.children:
            if new_end_dt < max(self.entry.children, key=attrgetter('end_dt')).end_dt:
                raise UserValueError(_("Session block cannot be shortened this much because contributions contained "
                                       "wouldn't fit."))
        if self.event_new in changes and not self.event_new.can_manage(session.user):
            raise UserValueError(_("Your action requires modification of event boundaries, but you are not authorized "
                                   "to manage the event."))
        if (self.entry.parent and self.entry.parent.session_block in changes
                and self.session and not self.session.can_manage_blocks(session.user)):
            raise UserValueError(_("Your action requires modification of event boundaries, but you are not authorized "
                                   "to manage the event."))
        notifications = []
        for obj, change in changes.iteritems():
            if self.entry.object == obj:
                continue
            if not isinstance(obj, Event) and obj.timetable_entry in self.entry.children:
                continue
            msg = None
            if isinstance(obj, Event):
                if 'start_dt' in change:
                    new_time = change['start_dt'][1]
                    msg = _("Event start time changed to {}")
                elif 'end_dt' in change:
                    new_time = change['end_dt'][1]
                    msg = _("Event end time changed to {}")
                else:
                    raise ValueError("Invalid change in event.")
            elif isinstance(obj, SessionBlock):
                if 'start_dt' in change:
                    new_time = change['start_dt'][1]
                    msg = _("Session block start time changed to {}")
                elif 'end_dt' in change:
                    new_time = change['end_dt'][1]
                    msg = _("Session block end time changed to {}")
                else:
                    raise ValueError("Invalid change in session block.")
            if msg:
                notifications.append(msg.format(format_time(new_time, timezone=self.event_new.tzinfo)))
        return jsonify_data(flash=False, entry=serialize_entry_update(self.entry), notifications=notifications)
