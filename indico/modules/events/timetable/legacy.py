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

from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.date_time import iterdays


def serialize_timetable(event, days=None, hide_weekends=False, for_management=False):
    # TODO: Management mode
    timetable = {}
    start_dt = event.start_dt.astimezone(event.tzinfo)
    end_dt = event.end_dt.astimezone(event.tzinfo)
    for day in iterdays(start_dt, end_dt, skip_weekends=hide_weekends, day_whitelist=days):
        date_str = day.strftime('%Y%m%d')
        timetable[date_str] = {}
    for entry in event.timetable_entries.order_by(TimetableEntry.type != TimetableEntryType.SESSION_BLOCK):
        day = entry.start_dt.astimezone(event.tzinfo).date()
        date_str = day.strftime('%Y%m%d')
        if date_str not in timetable:
            continue
        if not entry.can_view(session.user):
            continue
        data = serialize_timetable_entry(entry)
        key = _get_entry_key(entry)
        if entry.parent:
            parent_code = 's{}'.format(entry.parent_id)
            timetable[date_str][parent_code]['entries'][key] = data
        else:
            timetable[date_str][key] = data
    return timetable


def serialize_timetable_entry(entry):
    if entry.type == TimetableEntryType.SESSION_BLOCK:
        return serialize_session_block_entry(entry)
    elif entry.type == TimetableEntryType.CONTRIBUTION:
        return serialize_contribution_entry(entry)
    elif entry.type == TimetableEntryType.BREAK:
        return serialize_break_entry(entry)
    else:
        raise TypeError("Unknown timetable entry type.")


def serialize_session_block_entry(entry):
    block = entry.session_block
    data = {}
    data.update(_get_date_data(entry))
    data.update(_get_color_data(block.session))
    data.update(_get_location_data(block))
    data.update({'id': _get_entry_key(entry),
                 'uniqueId': entry.id,
                 'sessionSlotId': block.id,
                 'sessionId': block.session_id,
                 'title': block.session.title,
                 'slotTitle': block.title,
                 'entryType': 'Session',
                 'attachments': _get_attachment_data(block.session),
                 'code': block.session.code,
                 'conferenceId': block.session.event_id,
                 'contribDuration': block.session.default_contribution_duration.seconds / 60,
                 'conveners': [_get_person_data(x) for x in block.person_links],
                 'description': block.session.description,
                 'duration': block.duration.seconds / 60,
                 'isPoster': block.session.is_poster,
                 'entries': defaultdict(dict),
                 'pdf': None,
                 'url': None})
    return data


def serialize_contribution_entry(entry):
    contribution = entry.contribution
    data = {}
    data.update(_get_date_data(entry))
    data.update(_get_location_data(contribution))
    data.update({'id': _get_entry_key(entry),
                 'uniqueId': entry.id,
                 'contributionId': contribution.id,
                 'entryType': 'Contribution',
                 'title': contribution.title,
                 'attachments': _get_attachment_data(contribution),
                 'conferenceId': contribution.event_id,
                 'description': contribution.description,
                 'duration': contribution.duration.seconds / 60,
                 'pdf': None,
                 'presenters': [_get_person_data(x) for x in contribution.person_links],
                 'url': None})
    if entry.parent:
        block = entry.parent.session_block
        data.update({'sessionCode': block.session.code,
                     'sessionId': block.session_id,
                     'sessionSlotId': block.id})
    return data


def serialize_break_entry(entry):
    break_ = entry.break_
    data = {}
    data.update(_get_date_data(entry))
    data.update(_get_color_data(break_))
    data.update(_get_location_data(break_))
    data.update({'id': break_.id,
                 'entryType': 'Break',
                 'title': break_.title,
                 'description': break_.description,
                 'duration': break_.duration.seconds / 60})
    return data


def _get_attachment_data(obj):
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


def _get_color_data(obj):
    return {'color': '#' + obj.background_color,
            'textColor': '#' + obj.text_color}


def _get_date_data(entry):
    tzinfo = entry.event_new.tzinfo
    return {'startDate': _get_entry_date_dt(entry.start_dt, tzinfo),
            'endDate': _get_entry_date_dt(entry.end_dt, tzinfo)}


def _get_entry_key(entry):
    if entry.type == TimetableEntryType.SESSION_BLOCK:
        return 's{}'.format(entry.id)
    elif entry.type == TimetableEntryType.CONTRIBUTION:
        return 'c{}'.format(entry.id)
    elif entry.type == TimetableEntryType.BREAK:
        return 'b{}'.format(entry.id)
    else:
        raise ValueError()


def _get_entry_date_dt(dt, tzinfo):
    return {'date': dt.astimezone(tzinfo).strftime('%Y-%m-%d'),
            'time': dt.astimezone(tzinfo).strftime('%H:%M:%S'),
            'tz': str(tzinfo)}


def _get_location_data(obj):
    return {'location': obj.venue_name,
            'room': obj.room_name,
            'inheritLoc': obj.inherit_location,
            'inheritRoom': obj.inherit_location}


def _get_person_data(person_link):
    return {'name': person_link.get_full_name(last_name_first=False, last_name_upper=False,
                                              abbrev_first_name=False, show_title=True),
            'firstName': person_link.first_name,
            'familyName': person_link.last_name,
            'affiliation': person_link.affiliation,
            'email': person_link.person.email}
