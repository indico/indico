# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


from flask import has_request_context, session
from sqlalchemy.orm import defaultload

from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.events.util import should_show_draft_warning
from indico.util.date_time import iterdays
from indico.util.locations import LocationDataSchema, LocationParentSchema
from indico.web.flask.util import url_for


def get_entry_type(entry_type):
    if entry_type == TimetableEntryType.SESSION_BLOCK:
        return 'block'
    elif entry_type == TimetableEntryType.CONTRIBUTION:
        return 'contrib'
    elif entry_type == TimetableEntryType.BREAK:
        return 'break'
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


def get_color_data(obj):
    return {
        'colors': {
            'background': f'#{obj.background_color}',
            'text': f'#{obj.text_color}',
        }
    }


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

    data = {'person_id': person.id,
            'first_name': person_link.first_name,
            'last_name': person_link.last_name,
            'affiliation': person_link.affiliation,
            'name': person_link.get_full_name(last_name_first=False, last_name_upper=False,
                                              abbrev_first_name=False, show_title=person.event.show_titles),
            'display_order_key': person_link.display_order_key}
    if person.user:
        data['avatar_url'] = person.user.avatar_url

    if can_manage_event:
        data['email'] = person.email

    # TODO: (Ajob) Replace with proper schemas later
    if roles := _get_person_link_roles(person_link):
        data['roles'] = roles

    return data


class TimetableSerializer:
    def __init__(self, event, user=None, api=False):
        self.user = user if user is not None or not has_request_context() else session.user
        self.event = event
        self.can_manage_event = self.event.can_manage(self.user)
        self.api = api

    def serialize_timetable(self, strip_empty_days=False):
        tzinfo = self.event.tzinfo
        self.event.preload_all_acl_entries()
        timetable = {}
        for day in iterdays(self.event.start_dt.astimezone(tzinfo), self.event.end_dt.astimezone(tzinfo)):
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
                data['session_block_id'] = entry.parent.session_block.id
                timetable[date_str][parent_code]['children'].append(data)
            else:
                if (entry.type == TimetableEntryType.SESSION_BLOCK and
                        entry.start_dt.astimezone(tzinfo).date() != entry.end_dt.astimezone(tzinfo).date()):
                    # (Ajob) TODO: Evaluate if comment below is actually something we want to do
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
            children = []
        else:
            children = [self.serialize_timetable_entry(x) for x in entry.children]
        data.update({'id': block.id,
                     'type': get_entry_type(TimetableEntryType.SESSION_BLOCK),
                     'start_dt': self._get_start_dt(entry),
                     'session_id': block.session_id,
                     'session_title': block.session.title,
                     'title': block.title,
                     'attachments': self._get_attachment_data(block.session),
                     'code': block.session.code,
                     'person_links': [self._get_person_data(x) for x in block.person_links],
                     'description': block.session.description,
                     'duration': block.duration.seconds,
                     'is_poster': block.session.is_poster,
                     'children': children,
                     'pdf': url_for('sessions.export_session_timetable', block.session),
                     'url': url_for('sessions.display_session', block.session),
                     'location_data': LocationDataSchema().dump(block),
                     'child_location_parent': LocationParentSchema().dump(block.child_location_parent)})
        return data

    def serialize_contribution_entry(self, entry):
        from indico.modules.events.api import SerializerBase

        block = entry.parent.session_block if entry.parent else None
        contribution = entry.contribution
        data = {}
        data.update({'id': contribution.id,
                     'type': get_entry_type(TimetableEntryType.CONTRIBUTION),
                     'start_dt': self._get_start_dt(entry),
                     'attachments': self._get_attachment_data(contribution),
                     'description': contribution.description,
                     'duration': contribution.duration_display.seconds,
                     'pdf': url_for('contributions.export_pdf', entry.contribution),
                     'person_links': [self._get_person_data(x) for x in contribution.person_links],
                     'code': contribution.code,
                     'session_id': block.session_id if block else None,
                     'location_data': LocationDataSchema().dump(contribution),
                     'title': contribution.title,
                     'url': url_for('contributions.display_contribution', contribution),
                     'references': list(map(SerializerBase.serialize_reference, contribution.references)),
                     'board_number': contribution.board_number})
        if self.api:
            data['authors'] = list(map(self._get_person_data,
                                       sorted((p for p in contribution.person_links if not p.is_speaker),
                                              key=lambda x: (x.author_type != AuthorType.primary,
                                                             x.author_type != AuthorType.secondary,
                                                             x.display_order_key))))
        return data

    def serialize_break_entry(self, entry):
        block = entry.parent.session_block if entry.parent else None
        break_ = entry.break_
        data = {}
        data.update({'id': break_.id,
                     'type': get_entry_type(TimetableEntryType.BREAK),
                     'start_dt': self._get_start_dt(entry),
                     'description': break_.description,
                     'duration': break_.duration.seconds,
                     'session_id': block.session_id if block else None,
                     'title': break_.title,
                     'location_data': LocationDataSchema().dump(break_),
                     **get_color_data(break_)})
        return data

    def _get_attachment_data(self, obj):
        def serialize_attachment(attachment):
            return {'id': attachment.id,
                    'type': 'attachment',
                    'title': attachment.title,
                    'download_url': attachment.download_url}

        def serialize_folder(folder):
            return {'id': folder.id,
                    'type': 'folder',
                    'title': folder.title,
                    'attachments': list(map(serialize_attachment, folder.attachments))}

        items = obj.attached_items
        files = list(map(serialize_attachment, items.get('files', [])))
        folders = list(map(serialize_folder, items.get('folders', [])))

        return files + folders

    def _get_start_dt(self, entry):
        tzinfo = entry.event.tzinfo

        if entry.type == TimetableEntryType.CONTRIBUTION:
            start_dt = entry.contribution.start_dt_display
        else:
            start_dt = entry.start_dt

        return self._get_entry_date_dt(start_dt, tzinfo)

    def _get_entry_date_dt(self, dt, tzinfo):
        return dt.astimezone(tzinfo).isoformat()

    def _get_person_data(self, person_link):
        return _get_person_data(person_link, can_manage_event=self.can_manage_event)


# Event related functions:
def serialize_unscheduled_contribution(contribution, *, can_manage_event=False):
    return {'id': contribution.id,
            'type': get_entry_type(TimetableEntryType.CONTRIBUTION),
            'contribution_id': contribution.id,
            'attachments': [],
            'description': contribution.description,
            'duration': contribution.duration_display.seconds,
            'pdf': url_for('contributions.export_pdf', contribution),
            'presenters': [],
            'person_links': [_get_person_data(x, can_manage_event=can_manage_event)
                            for x in contribution.person_links],
            'code': contribution.code,
            'session_id': contribution.session.id if contribution.session else None,
            'title': contribution.title,
            'url': url_for('contributions.display_contribution', contribution),
            'references': [],
            'location_data': LocationDataSchema().dump(contribution),
            'board_number': contribution.board_number}


def serialize_event_info(event, *, user=None):
    from indico.modules.events.contributions import Contribution, contribution_settings
    can_manage_event = event.can_manage(user)

    return {'id': str(event.id),
            'title': event.title,
            'start_dt_local': event.start_dt_local.isoformat(),
            'end_dt_local': event.end_dt_local.isoformat(),
            'type': event.type,
            'is_draft': should_show_draft_warning(event),
            'sessions': {sess.id: serialize_session(sess) for sess in event.sessions},
            'default_contribution_duration': contribution_settings.get(event, 'default_duration').total_seconds(),
            'location_parent': LocationParentSchema().dump(event),
            'contributions': [serialize_unscheduled_contribution(c, can_manage_event=can_manage_event)
                              for c in Contribution.query.with_parent(event).filter_by(is_scheduled=False)]}


def serialize_session(sess):
    """Return data for a single session."""
    return {
        'description': sess.description,
        'id': sess.id,
        'is_poster': sess.is_poster,
        'title': sess.title,
        'url': url_for('sessions.display_session', sess),
        'default_contribution_duration': sess.default_contribution_duration.total_seconds(),
        **get_color_data(sess)
    }
