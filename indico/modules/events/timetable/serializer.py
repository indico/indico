# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict
from hashlib import md5

from flask import has_request_context, session
from sqlalchemy.orm import defaultload

from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.models.events import EventType
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.events.util import should_show_draft_warning
from indico.util.date_time import iterdays
from indico.web.flask.util import url_for


def _get_location_data(obj, *, management=False):
    data = {}
    data['location'] = obj.venue_name
    data['room'] = obj.room_name
    data['inheritLoc'] = obj.inherit_location
    data['inheritRoom'] = obj.inherit_location
    if management:
        data['address'] = obj.address
    return data


def _get_person_link_roles(person_link):
    roles = []

    if author_type := getattr(person_link, 'author_type', False):
        roles.append('primary' if author_type == AuthorType.primary else 'secondary')
    if getattr(person_link, 'is_speaker', False):
        roles.append('speaker')
    if getattr(person_link, 'is_submitter', False):
        roles.append('submitter')
    return roles


def _get_person_data(person_link, *, can_manage_event=False):
    person = person_link.person

    data = {'firstName': person_link.first_name,
            'familyName': person_link.last_name,
            'affiliation': person_link.affiliation,
            'emailHash': md5(person.email.encode()).hexdigest() if person.email else None,
            'name': person_link.get_full_name(last_name_first=False, last_name_upper=False,
                                              abbrev_first_name=False, show_title=person.event.show_titles),
            'displayOrderKey': person_link.display_order_key}
    if person.user:
        data['avatarURL'] = person.user.avatar_url

    if can_manage_event:
        data['email'] = person.email

    # TODO: (Ajob) Replace with proper schemas later
    if roles := _get_person_link_roles(person_link):
        data['roles'] = roles

    return data


class TimetableSerializer:
    def __init__(self, event, management=False, user=None, api=False):
        self.management = management
        self.user = user if user is not None or not has_request_context() else session.user
        self.event = event
        self.can_manage_event = self.event.can_manage(self.user)
        self.api = api

    def serialize_timetable(self, days=None, hide_weekends=False, strip_empty_days=False):
        tzinfo = self.event.tzinfo if self.management else self.event.display_tzinfo
        self.event.preload_all_acl_entries()
        timetable = {}
        for day in iterdays(self.event.start_dt.astimezone(tzinfo), self.event.end_dt.astimezone(tzinfo),
                            skip_weekends=hide_weekends, day_whitelist=days):
            date_str = day.strftime('%Y%m%d')
            timetable[date_str] = {}
        contributions_strategy = defaultload('contribution')
        contributions_strategy.subqueryload('person_links')
        contributions_strategy.subqueryload('references')
        query_options = (contributions_strategy,
                         defaultload('session_block').subqueryload('person_links'))
        query = (TimetableEntry.query.with_parent(self.event)
                 .options(*query_options)
                 .order_by(TimetableEntry.type != TimetableEntryType.SESSION_BLOCK))
        for entry in query:
            day = entry.start_dt.astimezone(tzinfo).date()
            date_str = day.strftime('%Y%m%d')
            if date_str not in timetable:
                continue
            if not entry.can_view(self.user):
                continue
            data = self.serialize_timetable_entry(entry, load_children=False)
            key = get_unique_key(entry)
            if entry.parent:
                parent_code = get_unique_key(entry.parent)
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
            raise TypeError('Unknown timetable entry type.')

    def serialize_session_block_entry(self, entry, load_children=True):
        block = entry.session_block
        data = {}
        if not load_children:
            entries = defaultdict(dict)
        else:
            entries = {get_unique_key(x): self.serialize_timetable_entry(x) for x in entry.children}
        data.update(self._get_entry_data(entry))
        data.update(self._get_color_data(block.session))
        data.update(self._get_location_data(block))
        data.update({'entryType': 'Session',
                     'sessionId': block.session_id,
                     'sessionCode': block.session.code,
                     'sessionTitle': block.session.title,
                     'title': block.title,
                     'attachments': self._get_attachment_data(block.session),
                     'code': block.session.code,
                     'contribDuration': block.session.default_contribution_duration.seconds / 60,
                     'personLinks': [self._get_person_data(x) for x in block.person_links],
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
                     'attachments': self._get_attachment_data(contribution),
                     'description': contribution.description,
                     'duration': contribution.duration_display.seconds / 60,
                     'pdf': url_for('contributions.export_pdf', entry.contribution),
                     'personLinks': [self._get_person_data(x) for x in contribution.person_links],
                     'code': contribution.code,
                     'sessionCode': block.session.code if block else None,
                     'sessionId': block.session_id if block else None,
                    #  'sessionSlotId': block.id if block else None,
                    #  'sessionSlotEntryId': entry.parent.id if entry.parent else None,
                     'title': contribution.title,
                     'url': url_for('contributions.display_contribution', contribution),
                     'friendlyId': contribution.friendly_id,
                     'references': list(map(SerializerBase.serialize_reference, contribution.references)),
                     'boardNumber': contribution.board_number})
        if self.api:
            data['authors'] = list(map(self._get_person_data,
                                       sorted((p for p in contribution.person_links if not p.is_speaker),
                                              key=lambda x: (x.author_type != AuthorType.primary,
                                                             x.author_type != AuthorType.secondary,
                                                             x.display_order_key))))
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
                    #  'sessionSlotId': block.id if block else None,
                    #  'sessionSlotEntryId': entry.parent.id if entry.parent else None,
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
                    'attachments': list(map(serialize_attachment, folder.attachments))}

        data = {'files': [], 'folders': []}
        items = obj.attached_items
        data['files'] = list(map(serialize_attachment, items.get('files', [])))
        data['folders'] = list(map(serialize_folder, items.get('folders', [])))

        return data

    def _get_color_data(self, obj):
        return {'color': '#' + obj.background_color,
                'textColor': '#' + obj.text_color}

    def _get_date_data(self, entry):
        if self.management:
            tzinfo = entry.event.tzinfo
        else:
            tzinfo = entry.event.display_tzinfo
        if entry.type == TimetableEntryType.CONTRIBUTION:
            start_dt = entry.contribution.start_dt_display
            end_dt = entry.contribution.end_dt_display
        else:
            start_dt = entry.start_dt
            end_dt = entry.end_dt
        return {'startDate': self._get_entry_date_dt(start_dt, tzinfo),
                'endDate': self._get_entry_date_dt(end_dt, tzinfo)}

    def _get_entry_data(self, entry):
        data = {}
        data.update(self._get_date_data(entry))
        data['id'] = get_unique_key(entry)
        data['objId'] = get_obj_id(entry)
        data['conferenceId'] = entry.event_id
        if self.management:
            data['isParallel'] = entry.is_parallel()
            data['isParallelInSession'] = entry.is_parallel(in_session=True)
            data['scheduleEntryId'] = entry.id
        return data

    def _get_entry_date_dt(self, dt, tzinfo):
        return {'date': dt.astimezone(tzinfo).strftime('%Y-%m-%d'),
                'time': dt.astimezone(tzinfo).strftime('%H:%M:%S'),
                'tz': str(tzinfo)}

    def _get_location_data(self, obj):
        return _get_location_data(obj, management=self.management)

    def _get_person_data(self, person_link):
        return _get_person_data(person_link, can_manage_event=self.can_manage_event)


def serialize_contribution(contribution):
    return {'id': contribution.id,
            'friendly_id': contribution.friendly_id,
            'title': contribution.title}


def get_obj_id(entry):
    if entry.type == TimetableEntryType.SESSION_BLOCK:
        return entry.session_block.id
    elif entry.type == TimetableEntryType.CONTRIBUTION:
        return entry.contribution.id
    elif entry.type == TimetableEntryType.BREAK:
        return entry.break_.id
    else:
        raise ValueError


def get_unique_key(entry):
    if entry.type == TimetableEntryType.SESSION_BLOCK:
        return f's{entry.session_block.id}'
    elif entry.type == TimetableEntryType.CONTRIBUTION:
        return f'c{entry.contribution.id}'
    elif entry.type == TimetableEntryType.BREAK:
        return f'b{entry.break_.id}'
    else:
        raise ValueError


# Event related functions:

# TODO: This is only temporary to get unscheduled contributions working
# before we rewrite the timetable serializer
def serialize_unscheduled_contribution(contribution, *, management=False, can_manage_event=False):
    data = {
        'id': f'c{contribution.id}',
        'objId': contribution.id
    }
    if contribution.session:
        data.update({'color': '#' + contribution.session.background_color,
                     'textColor': '#' + contribution.session.text_color})
    data.update({'entryType': 'Contribution',
                 '_type': 'ContribSchEntry',
                 '_fossil': 'contribSchEntryDisplay',
                 'contributionId': contribution.id,
                 'attachments': [],
                 'description': contribution.description,
                 'duration': contribution.duration_display.seconds / 60,
                 'pdf': url_for('contributions.export_pdf', contribution),
                 'presenters': [],
                 'personLinks': [_get_person_data(x, can_manage_event=can_manage_event)
                                 for x in contribution.person_links],
                 'code': contribution.code,
                 'sessionCode': None,
                 'sessionId': contribution.session.id if contribution.session else None,
                 'sessionSlotId': None,
                 'sessionSlotEntryId': None,
                 'title': contribution.title,
                 'url': url_for('contributions.display_contribution', contribution),
                 'friendlyId': contribution.friendly_id,
                 'references': [],
                 'board_number': contribution.board_number})
    data.update(**_get_location_data(contribution, management=management))
    return data


def serialize_event_info(event, *, management=False, user=None):
    from indico.modules.events.contributions import Contribution, contribution_settings
    can_manage_event = event.can_manage(user)
    return {'_type': 'Conference',
            'id': str(event.id),
            'title': event.title,
            'startDate': event.start_dt_local,
            'endDate': event.end_dt_local,
            'isConference': event.type_ == EventType.conference,
            'isDraft': should_show_draft_warning(event),
            'sessions': {sess.id: serialize_session(sess) for sess in event.sessions},
            'defaultContribDurationMinutes': contribution_settings.get(event, 'default_duration').total_seconds() / 60,
            'contributions': [serialize_unscheduled_contribution(c, management=management,
                                                                 can_manage_event=can_manage_event)
                              for c in Contribution.query.with_parent(event).filter_by(is_scheduled=False)]}


def serialize_session(sess):
    """Return data for a single session."""
    return {
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
