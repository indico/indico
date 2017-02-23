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

from collections import defaultdict
from itertools import chain

from flask import session
from sqlalchemy.orm import defaultload

from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.models.events import EventType
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.date_time import iterdays
from indico.web.flask.util import url_for


class TimetableSerializer(object):
    def __init__(self, management=False):
        self.management = management

    def serialize_timetable(self, event, days=None, hide_weekends=False, strip_empty_days=False):
        tzinfo = event.tzinfo if self.management else event.display_tzinfo
        event.preload_all_acl_entries()
        timetable = {}
        for day in iterdays(event.start_dt.astimezone(tzinfo), event.end_dt.astimezone(tzinfo),
                            skip_weekends=hide_weekends, day_whitelist=days):
            date_str = day.strftime('%Y%m%d')
            timetable[date_str] = {}
        contributions_strategy = defaultload('contribution')
        contributions_strategy.subqueryload('person_links')
        contributions_strategy.subqueryload('references')
        query_options = (contributions_strategy,
                         defaultload('session_block').subqueryload('person_links'))
        query = (TimetableEntry.query.with_parent(event)
                 .options(*query_options)
                 .order_by(TimetableEntry.type != TimetableEntryType.SESSION_BLOCK))
        for entry in query:
            day = entry.start_dt.astimezone(tzinfo).date()
            date_str = day.strftime('%Y%m%d')
            if date_str not in timetable:
                continue
            if not entry.can_view(session.user):
                continue
            data = self.serialize_timetable_entry(entry, load_children=False)
            key = self._get_entry_key(entry)
            if entry.parent:
                parent_code = 's{}'.format(entry.parent_id)
                timetable[date_str][parent_code]['entries'][key] = data
            else:
                if (entry.type == TimetableEntryType.SESSION_BLOCK and
                        entry.start_dt.astimezone(tzinfo).date() != entry.end_dt.astimezone(tzinfo).date()):
                    # If a session block lasts into another day we need to add it to that day, too
                    timetable[entry.end_dt.astimezone(tzinfo).date().strftime('%Y%m%d')][key] = data
                timetable[date_str][key] = data
        if strip_empty_days:
            timetable = self._strip_empty_days(timetable)
        return timetable

    def serialize_session_timetable(self, session_, without_blocks=False, strip_empty_days=False):
        event = session_.event_new
        event_tz = event.tzinfo
        timetable = {}
        if session_.blocks:
            start_dt = min(chain((b.start_dt for b in session_.blocks), (event.start_dt,))).astimezone(event_tz)
            end_dt = max(chain((b.end_dt for b in session_.blocks), (event.end_dt,))).astimezone(event_tz)
        else:
            start_dt = event.start_dt_local
            end_dt = event.end_dt_local

        for day in iterdays(start_dt, end_dt):
            timetable[day.strftime('%Y%m%d')] = {}
        for block in session_.blocks:
            block_entry = block.timetable_entry
            if not block_entry:
                continue
            date_key = block_entry.start_dt.astimezone(event_tz).strftime('%Y%m%d')
            entries = block_entry.children if without_blocks else [block_entry]
            for entry in entries:
                if not entry.can_view(session.user):
                    continue
                entry_key = self._get_entry_key(entry)
                timetable[date_key][entry_key] = self.serialize_timetable_entry(entry, load_children=True)
        if strip_empty_days:
            timetable = self._strip_empty_days(timetable)
        return timetable

    @staticmethod
    def _strip_empty_days(timetable):
        """Return the timetable without the leading and trailing empty days."""
        days = sorted(timetable)
        first_non_empty = next((day for day in days if timetable[day]), None)
        if first_non_empty is None:
            return {}
        last_non_empty = next((day for day in reversed(days) if timetable[day]), first_non_empty)
        return {day: timetable[day] for day in days if first_non_empty <= day <= last_non_empty}

    def serialize_timetable_entry(self, entry, **kwargs):
        if entry.type == TimetableEntryType.SESSION_BLOCK:
            return self.serialize_session_block_entry(entry, kwargs.pop('load_children', True))
        elif entry.type == TimetableEntryType.CONTRIBUTION:
            return self.serialize_contribution_entry(entry)
        elif entry.type == TimetableEntryType.BREAK:
            return self.serialize_break_entry(entry)
        else:
            raise TypeError("Unknown timetable entry type.")

    def serialize_session_block_entry(self, entry, load_children=True):
        block = entry.session_block
        data = {}
        if not load_children:
            entries = defaultdict(dict)
        else:
            entries = {self._get_entry_key(x): self.serialize_timetable_entry(x) for x in entry.children}
        data.update(self._get_entry_data(entry))
        data.update(self._get_color_data(block.session))
        data.update(self._get_location_data(block))
        data.update({'entryType': 'Session',
                     'sessionSlotId': block.id,
                     'sessionId': block.session_id,
                     'sessionCode': block.session.code,
                     'title': block.session.title,
                     'slotTitle': block.title,
                     'attachments': self._get_attachment_data(block.session),
                     'code': block.session.code,
                     'contribDuration': block.session.default_contribution_duration.seconds / 60,
                     'conveners': [self._get_person_data(x) for x in block.person_links],
                     'description': block.session.description,
                     'duration': block.duration.seconds / 60,
                     'isPoster': block.session.is_poster,
                     'entries': entries,
                     'pdf': url_for('sessions.export_session_timetable', block.session),
                     'url': url_for('sessions.display_session', block.session),
                     'friendlyId': block.session.friendly_id})
        return data

    def serialize_contribution_entry(self, entry):
        from indico.modules.events.api import SerializerBase
        block = entry.parent.session_block if entry.parent else None
        contribution = entry.contribution
        data = {}
        data.update(self._get_entry_data(entry))
        if contribution.session:
            data.update(self._get_color_data(contribution.session))
        data.update(self._get_location_data(contribution))
        data.update({'entryType': 'Contribution',
                     '_type': 'ContribSchEntry',
                     '_fossil': 'contribSchEntryDisplay',
                     'contributionId': contribution.id,
                     'attachments': self._get_attachment_data(contribution),
                     'description': contribution.description,
                     'duration': contribution.duration.seconds / 60,
                     'pdf': url_for('contributions.export_pdf', entry.contribution),
                     'presenters': map(self._get_person_data,
                                       sorted([p for p in contribution.person_links if p.is_speaker],
                                              key=lambda x: (x.author_type != AuthorType.primary,
                                                             x.author_type != AuthorType.secondary,
                                                             x.display_order_key))),
                     'sessionCode': block.session.code if block else None,
                     'sessionId': block.session_id if block else None,
                     'sessionSlotId': block.id if block else None,
                     'sessionSlotEntryId': entry.parent.id if entry.parent else None,
                     'title': contribution.title,
                     'url': url_for('contributions.display_contribution', contribution),
                     'friendlyId': contribution.friendly_id,
                     'references': map(SerializerBase.serialize_reference, contribution.references)})
        return data

    def serialize_break_entry(self, entry, management=False):
        block = entry.parent.session_block if entry.parent else None
        break_ = entry.break_
        data = {}
        data.update(self._get_entry_data(entry))
        data.update(self._get_color_data(break_))
        data.update(self._get_location_data(break_))
        data.update({'entryType': 'Break',
                     '_type': 'BreakTimeSchEntry',
                     '_fossil': 'breakTimeSchEntry',
                     'description': break_.description,
                     'duration': break_.duration.seconds / 60,
                     'sessionId': block.session_id if block else None,
                     'sessionCode': block.session.code if block else None,
                     'sessionSlotId': block.id if block else None,
                     'sessionSlotEntryId': entry.parent.id if entry.parent else None,
                     'title': break_.title})
        return data

    def _get_attachment_data(self, obj):
        def serialize_attachment(attachment):
            return {'id': attachment.id,
                    '_type': 'Attachment',
                    '_fossil': 'attachment',
                    'title': attachment.title,
                    'download_url': attachment.download_url}

        def serialize_folder(folder):
            return {'id': folder.id,
                    '_type': 'AttachmentFolder',
                    '_fossil': 'folder',
                    'title': folder.title,
                    'attachments': map(serialize_attachment, folder.attachments)}

        data = {'files': [], 'folders': []}
        items = obj.attached_items
        data['files'] = map(serialize_attachment, items.get('files', []))
        data['folders'] = map(serialize_folder, items.get('folders', []))
        if not data['files'] and not data['folders']:
            data['files'] = None
        return data

    def _get_color_data(self, obj):
        return {'color': '#' + obj.background_color,
                'textColor': '#' + obj.text_color}

    def _get_date_data(self, entry):
        if self.management:
            tzinfo = entry.event_new.tzinfo
        else:
            tzinfo = entry.event_new.display_tzinfo
        return {'startDate': self._get_entry_date_dt(entry.start_dt, tzinfo),
                'endDate': self._get_entry_date_dt(entry.end_dt, tzinfo)}

    def _get_entry_data(self, entry):
        from indico.modules.events.timetable.operations import can_swap_entry
        data = {}
        data.update(self._get_date_data(entry))
        data['id'] = self._get_entry_key(entry)
        data['uniqueId'] = data['id']
        data['conferenceId'] = entry.event_id
        if self.management:
            data['isParallel'] = entry.is_parallel()
            data['isParallelInSession'] = entry.is_parallel(in_session=True)
            data['scheduleEntryId'] = entry.id
            data['canSwapUp'] = can_swap_entry(entry, direction='up')
            data['canSwapDown'] = can_swap_entry(entry, direction='down')
        return data

    def _get_entry_key(self, entry):
        if entry.type == TimetableEntryType.SESSION_BLOCK:
            return 's{}'.format(entry.id)
        elif entry.type == TimetableEntryType.CONTRIBUTION:
            return 'c{}'.format(entry.id)
        elif entry.type == TimetableEntryType.BREAK:
            return 'b{}'.format(entry.id)
        else:
            raise ValueError()

    def _get_entry_date_dt(self, dt, tzinfo):
        return {'date': dt.astimezone(tzinfo).strftime('%Y-%m-%d'),
                'time': dt.astimezone(tzinfo).strftime('%H:%M:%S'),
                'tz': str(tzinfo)}

    def _get_location_data(self, obj):
        data = {}
        data['location'] = obj.venue_name
        data['room'] = obj.room_name
        data['inheritLoc'] = obj.inherit_location
        data['inheritRoom'] = obj.inherit_location
        if self.management:
            data['address'] = obj.address
        return data

    def _get_person_data(self, person_link):
        return {'firstName': person_link.first_name,
                'familyName': person_link.last_name,
                'affiliation': person_link.affiliation,
                'email': person_link.person.email,
                'name': person_link.get_full_name(last_name_first=False, last_name_upper=False,
                                                  abbrev_first_name=False, show_title=True),
                'displayOrderKey': person_link.display_order_key}


def serialize_contribution(contribution):
    return {'id': contribution.id,
            'friendly_id': contribution.friendly_id,
            'title': contribution.title}


def serialize_day_update(event, day, block=None, session_=None):
    serializer = TimetableSerializer(management=True)
    timetable = serializer.serialize_session_timetable(session_) if session_ else serializer.serialize_timetable(event)
    block_id = serializer._get_entry_key(block) if block else None
    day = day.strftime('%Y%m%d')
    return {'day': day,
            'entries': timetable[day] if not block else timetable[day][block_id]['entries'],
            'slotEntry': serializer.serialize_session_block_entry(block) if block else None}


def serialize_entry_update(entry, with_timetable=False, session_=None):
    serializer = TimetableSerializer(management=True)
    day = entry.start_dt.astimezone(entry.event_new.tzinfo)
    day_update = serialize_day_update(entry.event_new, day, block=entry.parent, session_=session_)
    return dict({'id': serializer._get_entry_key(entry),
                 'entry': serializer.serialize_timetable_entry(entry),
                 'autoOps': None},
                **day_update)


def serialize_event_info(event):
    return {'_type': 'Conference',
            'id': unicode(event.id),
            'title': event.title,
            'startDate': event.start_dt_local,
            'endDate': event.end_dt_local,
            'isConference': event.type_ == EventType.conference,
            'sessions': {sess.id: serialize_session(sess) for sess in event.sessions}}


def serialize_session(sess):
    """Return data for a single session"""
    data = {
        '_type': 'Session',
        'address': sess.address,
        'color': '#' + sess.colors.background,
        'description': sess.description,
        'id': sess.id,
        'isPoster': sess.is_poster,
        'location': sess.venue_name,
        'room': sess.room_name,
        'roomFullname': sess.room_name,
        'textColor': '#' + sess.colors.text,
        'title': sess.title,
        'url': url_for('sessions.display_session', sess)
    }
    return data
