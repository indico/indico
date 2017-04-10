# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from flask import flash, request, jsonify, session
from pytz import utc
from werkzeug.exceptions import BadRequest, NotFound

from indico.core.errors import UserValueError
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.operations import create_contribution, delete_contribution, update_contribution
from indico.modules.events.management.util import flash_if_unregistered
from indico.modules.events.sessions.controllers.management.sessions import RHCreateSession, RHSessionREST
from indico.modules.events.sessions.forms import SessionForm
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.operations import delete_session_block, update_session_block, update_session
from indico.modules.events.timetable.controllers import (RHManageTimetableBase, RHManageTimetableEntryBase,
                                                         SessionManagementLevel)
from indico.modules.events.timetable.controllers.manage import RHBreakREST
from indico.modules.events.timetable.forms import (BreakEntryForm, ContributionEntryForm, SessionBlockEntryForm,
                                                   BaseEntryForm)
from indico.modules.events.timetable.legacy import (serialize_contribution, serialize_entry_update, serialize_session,
                                                    serialize_day_update, TimetableSerializer)
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.operations import (create_break_entry, create_session_block_entry,
                                                        schedule_contribution, fit_session_block_entry,
                                                        update_break_entry, update_timetable_entry,
                                                        move_timetable_entry, update_timetable_entry_object,
                                                        delete_timetable_entry, swap_timetable_entry)
from indico.modules.events.timetable.reschedule import Rescheduler, RescheduleMode
from indico.modules.events.timetable.util import (find_next_start_dt, get_session_block_entries,
                                                  get_time_changes_notifications,
                                                  shift_following_entries)
from indico.modules.events.util import get_random_color, track_time_changes, get_field_values
from indico.util.date_time import iterdays, as_utc
from indico.util.i18n import _
from indico.util.string import handle_legacy_description
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
        location_parent = kwargs.pop('location_parent', None)
        inherited_location = location_parent.location_data if location_parent else self.event_new.location_data
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
        defaults = self._get_form_defaults(colors=colors, location_parent=self.session_block)
        form = BreakEntryForm(obj=defaults, **self._get_form_params())
        if form.validate_on_submit():
            with track_time_changes(auto_extend=True, user=session.user) as changes:
                entry = create_break_entry(self.event_new, form.data, session_block=self.session_block)
            notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=entry)
            return jsonify_data(update=serialize_entry_update(entry, session_=self.session),
                                notifications=notifications, flash=False)
        return jsonify_form(form, fields=form._display_fields)


class RHLegacyTimetableAddContribution(RHLegacyTimetableAddEntryBase):
    session_management_level = SessionManagementLevel.manage

    def _process(self):
        defaults = self._get_form_defaults(location_parent=self.session_block)
        form = ContributionEntryForm(obj=defaults, to_schedule=True, **self._get_form_params())
        if form.validate_on_submit():
            contrib = Contribution()
            with track_time_changes(auto_extend=True, user=session.user) as changes:
                with flash_if_unregistered(self.event_new, lambda: contrib.person_links):
                    contrib = create_contribution(self.event_new, form.data, session_block=self.session_block,
                                                  extend_parent=True)
            entry = contrib.timetable_entry
            notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=entry)
            return jsonify_data(entries=[serialize_entry_update(entry, session_=self.session)],
                                notifications=notifications)
        self.commit = False
        return jsonify_template('events/contributions/forms/contribution.html', form=form, fields=form._display_fields)


class RHLegacyTimetableAddSessionBlock(RHLegacyTimetableAddEntryBase):
    session_management_level = SessionManagementLevel.coordinate_with_blocks

    def _checkParams(self, params):
        RHLegacyTimetableAddEntryBase._checkParams(self, params)
        self.parent_session = self.session or self.event_new.get_session(request.args['parent_session_id'])
        if not self.parent_session:
            raise NotFound

    def _process(self):
        defaults = self._get_form_defaults(location_parent=self.parent_session)
        form = SessionBlockEntryForm(obj=defaults, **self._get_form_params())
        if form.validate_on_submit():
            with track_time_changes(auto_extend=True, user=session.user) as changes:
                entry = create_session_block_entry(self.parent_session, form.data)
            notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=entry)
            return jsonify_data(update=serialize_entry_update(entry, session_=self.session),
                                notifications=notifications, flash=False)
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
        day = self.entry.start_dt.astimezone(self.entry.event_new.tzinfo).date()
        block = self.entry.parent
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            delete_session_block(self.entry.session_block)
        elif self.entry.type == TimetableEntryType.CONTRIBUTION and self.event_new.type != 'conference':
            delete_contribution(self.entry.contribution)
        else:
            delete_timetable_entry(self.entry)
        return jsonify_data(update=serialize_day_update(self.event_new, day, block=block, session_=self.session),
                            flash=False)


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
        parent_session_block = self.entry.parent.object if self.entry.parent else None
        if self.entry.contribution:
            contrib = self.entry.contribution
            tt_entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
            form = ContributionEntryForm(obj=FormDefaults(contrib, time=tt_entry_dt.time()),
                                         event=self.event_new, contrib=contrib, to_schedule=False,
                                         day=tt_entry_dt.date(), session_block=parent_session_block)
            if form.validate_on_submit():
                with track_time_changes(auto_extend=True, user=session.user) as changes:
                    with flash_if_unregistered(self.event_new, lambda: contrib.person_links):
                        update_contribution(contrib, *get_field_values(form.data))
                notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=self.entry)
                return jsonify_data(update=serialize_entry_update(self.entry, session_=self.session),
                                    notifications=notifications)
            elif not form.is_submitted():
                handle_legacy_description(form.description, contrib)
            return jsonify_template('events/contributions/forms/contribution.html', form=form,
                                    fields=form._display_fields)
        elif self.entry.break_:
            break_ = self.entry.break_
            tt_entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
            form = BreakEntryForm(obj=FormDefaults(break_, time=tt_entry_dt.time()), event=self.event_new,
                                  day=tt_entry_dt.date(), session_block=parent_session_block)
            if form.validate_on_submit():
                with track_time_changes(auto_extend=True, user=session.user) as changes:
                    update_break_entry(break_, form.data)
                notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=self.entry)
                return jsonify_data(update=serialize_entry_update(self.entry, session_=self.session),
                                    notifications=notifications, flash=False)
        elif self.entry.session_block:
            if self.edit_session:
                session_ = self.entry.session_block.session
                form = SessionForm(obj=FormDefaults(session_), event=self.event_new)
                if form.validate_on_submit():
                    update_session(session_, form.data)
                    return jsonify_data(update=serialize_entry_update(self.entry, session_=self.session), flash=False)
            else:
                block = self.entry.session_block
                tt_entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
                form = SessionBlockEntryForm(obj=FormDefaults(block, time=tt_entry_dt.time()),
                                             event=self.event_new, session_block=block, to_schedule=False,
                                             day=tt_entry_dt.date())
                if form.validate_on_submit():
                    with track_time_changes(auto_extend=True, user=session.user) as changes:
                        update_session_block(block, form.data)
                    notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo,
                                                                   entry=self.entry)
                    return jsonify_data(update=serialize_entry_update(self.entry, session_=self.session),
                                        notifications=notifications, flash=False)
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
        entry_dt = self.entry.start_dt.astimezone(self.event_new.tzinfo)
        form = BaseEntryForm(obj=FormDefaults(item, time=entry_dt.time()), day=entry_dt.date(),
                             event=self.event_new, entry=self.entry,
                             session_block=self.entry.parent.object if self.entry.parent else None)
        data = form.data
        shift_later = data.pop('shift_later')

        if form.validate_on_submit():
            with track_time_changes(auto_extend=True, user=session.user) as changes:
                if shift_later:
                    new_end_dt = form.start_dt.data + form.duration.data
                    shift = new_end_dt - self.entry.end_dt
                    shift_following_entries(self.entry, shift, session_=self.session)
                if self.entry.contribution:
                    update_timetable_entry(self.entry, {'start_dt': form.start_dt.data})
                    update_contribution(item, {'duration': form.duration.data})
                elif self.entry.break_:
                    update_break_entry(item, data)
                elif self.entry.session_block:
                    update_session_block(item, data)
            notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=self.entry)
            return jsonify_data(update=serialize_entry_update(self.entry, session_=self.session),
                                notifications=notifications, flash=False)
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
        if set(data.viewkeys()) > allowed_keys:
            raise BadRequest('Invalid keys found')
        elif required_keys > set(data.viewkeys()):
            raise BadRequest('Required keys missing')
        entries = []
        day = dateutil.parser.parse(data['day']).date()
        query = Contribution.query.with_parent(self.event_new).filter(Contribution.id.in_(data['contribution_ids']))
        with track_time_changes(auto_extend='end', user=session.user) as changes:
            for contribution in query:
                start_dt = find_next_start_dt(contribution.duration,
                                              obj=self.session_block or self.event_new,
                                              day=None if self.session_block else day,
                                              force=True)
                entry = self._schedule(contribution, start_dt)
                if entry.end_dt.astimezone(entry.event_new.tzinfo).date() > day:
                    raise UserValueError(_("Contribution '{}' could not be scheduled since it doesn't fit on this day.")
                                         .format(contribution.title))
                entries.append(entry)
        notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo)
        return jsonify_data(update=serialize_entry_update(entries[0], session_=self.session) if entries else None,
                            notifications=notifications, flash=False)

    def _schedule(self, contrib, start_dt):
        return schedule_contribution(contrib, start_dt, session_block=self.session_block, extend_parent=True)


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
        with track_time_changes(auto_extend='end', user=session.user) as changes:
            rescheduler.run()
        notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo)
        for notification in notifications:
            flash(notification, 'highlight')
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
        with track_time_changes(auto_extend=True, user=session.user) as changes:
            entry_data = self._move_entry(request.json)
        rv = dict(serialize_entry_update(self.entry), **entry_data)
        notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=self.entry)
        return jsonify_data(flash=False, entry=rv, notifications=notifications)

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


class RHLegacyTimetableShiftEntries(RHManageTimetableEntryBase):
    @property
    def session_management_level(self):
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            return SessionManagementLevel.coordinate_with_blocks
        else:
            return SessionManagementLevel.coordinate

    def _process(self):
        new_start_dt = (self.event_new.tzinfo.localize(dateutil.parser.parse(request.form.get('startDate')))
                        .astimezone(utc))
        shift = new_start_dt - self.entry.start_dt
        with track_time_changes(auto_extend=True, user=session.user) as changes:
            shift_following_entries(self.entry, shift, session_=self.session)
            self.entry.move(new_start_dt)
        notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=self.entry)
        return jsonify_data(flash=False, update=serialize_entry_update(self.entry, session_=self.session),
                            notifications=notifications)


class RHLegacyTimetableSwapEntries(RHManageTimetableEntryBase):
    @property
    def session_management_level(self):
        if self.entry.type == TimetableEntryType.SESSION_BLOCK:
            return SessionManagementLevel.coordinate_with_blocks
        else:
            return SessionManagementLevel.coordinate

    def _checkParams(self, params):
        RHManageTimetableEntryBase._checkParams(self, params)
        if self.entry.is_parallel(in_session=self.session is not None):
            raise BadRequest

    def _process(self):
        direction = request.form['direction']
        with track_time_changes():
            swap_timetable_entry(self.entry, direction, session_=self.session)
        return jsonify_data(flash=False, update=serialize_entry_update(self.entry, session_=self.session))


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
        with track_time_changes(auto_extend=True, user=session.user) as changes:
            update_timetable_entry_object(self.entry, {'duration': new_duration})
            if is_session_block:
                self.entry.move(new_start_dt)
            if not is_session_block:
                update_timetable_entry(self.entry, {'start_dt': new_start_dt})
        if is_session_block and self.entry.children:
            if new_end_dt < max(self.entry.children, key=attrgetter('end_dt')).end_dt:
                raise UserValueError(_("Session block cannot be shortened this much because contributions contained "
                                       "wouldn't fit."))
        notifications = get_time_changes_notifications(changes, tzinfo=self.event_new.tzinfo, entry=self.entry)
        return jsonify_data(flash=False, update=serialize_entry_update(self.entry, session_=self.session),
                            notifications=notifications)


class RHLegacyTimetableEditSession(RHSessionREST):
    def _process_PATCH(self):
        RHSessionREST._process_PATCH(self)
        return jsonify_data(entries=[serialize_entry_update(block.timetable_entry) for block in self.session.blocks],
                            flash=False)


class RHLegacyTimetableBreakREST(RHBreakREST):
    def _process_PATCH(self):
        RHBreakREST._process_PATCH(self)
        return jsonify_data(entries=[serialize_entry_update(self.entry)], flash=False)
