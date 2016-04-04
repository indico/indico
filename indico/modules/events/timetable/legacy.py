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

from collections import defaultdict

from flask import session
from sqlalchemy.orm import defaultload

from indico.modules.events.contributions.models.persons import ContributionPersonLink
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.date_time import iterdays
from indico.web.flask.util import url_for
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import IConferenceEventInfoFossil


class TimetableSerializer(object):
    def __init__(self, management=False):
        self.management = management

    def serialize_timetable(self, event, days=None, hide_weekends=False):
        timetable = {}
        for day in iterdays(event.start_dt_local, event.end_dt_local, skip_weekends=hide_weekends, day_whitelist=days):
            date_str = day.strftime('%Y%m%d')
            timetable[date_str] = {}
        query_options = (defaultload('contribution').subqueryload('person_links'),
                         defaultload('session_block').subqueryload('person_links'))
        query = (event.timetable_entries
                 .options(*query_options)
                 .order_by(TimetableEntry.type != TimetableEntryType.SESSION_BLOCK))
        for entry in query:
            day = entry.start_dt.astimezone(event.tzinfo).date()
            date_str = day.strftime('%Y%m%d')
            if date_str not in timetable:
                continue
            if not entry.can_view(session.user):
                continue
            data = self.serialize_timetable_entry(entry)
            key = self._get_entry_key(entry)
            if entry.parent:
                parent_code = 's{}'.format(entry.parent_id)
                timetable[date_str][parent_code]['entries'][key] = data
            else:
                timetable[date_str][key] = data
        return timetable

    def serialize_session_timetable(self, session_):
        data = {}
        if session_.is_poster:
            return data
        tzinfo = session_.event_new.tzinfo
        start_dt = session_.start_dt.astimezone(tzinfo)
        end_dt = session_.end_dt.astimezone(tzinfo)
        for day in iterdays(start_dt, end_dt):
            data[day.strftime('%Y%m%d')] = {}
        for block in session_.blocks:
            tt_entry = block.timetable_entry
            if not tt_entry:
                continue
            for child_entry in tt_entry.children:
                if not child_entry.can_view(session.user):
                    continue
                date_key = child_entry.start_dt.astimezone(tzinfo).strftime('%Y%m%d')
                entry_key = self._get_entry_key(tt_entry) + 'l{}'.format(child_entry.id)
                data[date_key][entry_key] = self.serialize_timetable_entry(child_entry)
        return data

    def serialize_timetable_entry(self, entry):
        if entry.type == TimetableEntryType.SESSION_BLOCK:
            return self.serialize_session_block_entry(entry)
        elif entry.type == TimetableEntryType.CONTRIBUTION:
            return self.serialize_contribution_entry(entry)
        elif entry.type == TimetableEntryType.BREAK:
            return self.serialize_break_entry(entry)
        else:
            raise TypeError("Unknown timetable entry type.")

    def serialize_session_block_entry(self, entry):
        block = entry.session_block
        data = {}
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
                     'entries': defaultdict(dict),
                     'pdf': None,
                     'url': url_for('sessions.display_session', block.session)})
        return data

    def serialize_contribution_entry(self, entry):
        block = entry.parent.session_block if entry.parent else None
        contribution = entry.contribution
        data = {}
        data.update(self._get_entry_data(entry))
        if contribution.session:
            data.update(self._get_color_data(contribution.session))
        data.update(self._get_location_data(contribution))
        data.update({'entryType': 'Contribution',
                     'contributionId': contribution.id,
                     'attachments': self._get_attachment_data(contribution),
                     'description': contribution.description,
                     'duration': contribution.duration.seconds / 60,
                     'pdf': None,
                     'presenters': [self._get_person_data(x) for x in contribution.person_links],
                     'sessionCode': block.session.code if block else None,
                     'sessionId': block.session_id if block else None,
                     'sessionSlotId': block.id if block else None,
                     'title': contribution.title,
                     'url': url_for('contributions.display_contribution', contribution)})
        return data

    def serialize_break_entry(self, entry, management=False):
        block = entry.parent.session_block if entry.parent else None
        break_ = entry.break_
        data = {}
        data.update(self._get_entry_data(entry))
        data.update(self._get_color_data(break_))
        data.update(self._get_location_data(break_))
        data.update({'entryType': 'Break',
                     'description': break_.description,
                     'duration': break_.duration.seconds / 60,
                     'sessionId': block.session_id if block else None,
                     'sessionCode': block.session.code if block else None,
                     'sessionSlotId': block.id if block else None,
                     'title': break_.title})
        return data

    def _get_attachment_data(self, obj):
        def serialize_attachment(attachment):
            return {'title': attachment.title, 'download_url': attachment.download_url}

        def serialize_folder(folder):
            return {'title': folder.title,
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
        tzinfo = entry.event_new.tzinfo
        return {'startDate': self._get_entry_date_dt(entry.start_dt, tzinfo),
                'endDate': self._get_entry_date_dt(entry.end_dt, tzinfo)}

    def _get_entry_data(self, entry):
        data = {}
        data.update(self._get_date_data(entry))
        data['id'] = self._get_entry_key(entry)
        data['uniqueId'] = data['id']
        data['conferenceId'] = entry.event_id,
        if self.management:
            data['scheduleEntryId'] = entry.id
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
        data = {}
        data['firstName'] = person_link.first_name
        data['familyName'] = person_link.last_name
        data['affiliation'] = person_link.affiliation
        data['email'] = person_link.person.email
        data['name'] = person_link.get_full_name(last_name_first=False, last_name_upper=False,
                                                 abbrev_first_name=False, show_title=True),
        if self.management:
            data['id'] = person_link.person_id
            data['address'] = person_link.person.address
            data['phone'] = person_link.person.phone
            data['title'] = person_link.person.title
            if isinstance(person_link, ContributionPersonLink):
                data['isSubmitter'] = person_link.is_submitter
                # TODO: URL to person page
                data['url'] = None
            if isinstance(person_link, SessionBlockPersonLink):
                data['fullName'] = data['name']
        return data


def serialize_contribution(contribution):
    return {'id': contribution.id,
            'title': contribution.title}


def serialize_entry_update(entry):
    serializer = TimetableSerializer(management=True)
    serialization = {TimetableEntryType.BREAK: serializer.serialize_break_entry,
                     TimetableEntryType.CONTRIBUTION: serializer.serialize_contribution_entry,
                     TimetableEntryType.SESSION_BLOCK: serializer.serialize_session_block_entry}
    tzinfo = entry.event_new.tzinfo
    return {'id': serializer._get_entry_key(entry),
            'day': entry.start_dt.astimezone(tzinfo).strftime('%Y%m%d'),
            'entry': serialization[entry.type](entry),
            'slotEntry': serializer.serialize_session_block_entry(entry.parent) if entry.parent else None,
            'autoOps': None}


def serialize_event_info(event):
    conf = event.as_legacy
    event_info = fossilize(conf, IConferenceEventInfoFossil, tz=conf.tz)
    event_info['isCFAEnabled'] = conf.getAbstractMgr().isActive()
    event_info['sessions'] = {sess.id: serialize_session(sess) for sess in event.sessions}
    return event_info


def serialize_session(sess):
    """Return data for a single session"""
    from indico.modules.events.util import serialize_person_link

    def _serialize_date(dt):
        tzinfo = sess.event_new.tzinfo
        return {'date': dt.astimezone(tzinfo).strftime('%Y-%m-%d'),
                'time': dt.astimezone(tzinfo).strftime('%H:%M:%S'),
                'tz': str(tzinfo)}

    data = {
        '_type': 'Session',
        'address': sess.address,
        'color': '#' + sess.colors.background,
        'description': sess.description,
        'endDate': _serialize_date(sess.end_dt) if sess.end_dt else '',
        'id': sess.id,
        'isPoster': sess.is_poster,
        'location': sess.venue_name,
        'numSlots': len(sess.blocks),
        'protectionURL': '',
        'room': sess.room_name,
        'roomFullname': sess.room_name,
        'sessionConveners': [],
        'startDate': _serialize_date(sess.start_dt) if sess.start_dt else '',
        'textColor': '#' + sess.colors.text,
        'title': sess.title,
        'url': url_for('sessions.display_session', sess)
    }
    for convener in sess.all_conveners:
        convener_data = serialize_person_link(convener)
        data['sessionConveners'].append(convener_data)
    return data
