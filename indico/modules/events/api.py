# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import fnmatch
import re
from datetime import datetime
from hashlib import md5
from operator import attrgetter

import pytz
from flask import request
from sqlalchemy import Date, cast
from sqlalchemy.orm import joinedload, subqueryload, undefer
from werkzeug.exceptions import ServiceUnavailable

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments.api.util import build_folders_api_data, build_material_legacy_api_data
from indico.modules.categories import Category, LegacyCategoryMapping
from indico.modules.categories.serialize import serialize_categories_ical
from indico.modules.events import Event
from indico.modules.events.models.persons import PersonLinkBase
from indico.modules.events.notes.util import build_note_api_data, build_note_legacy_api_data
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.legacy import TimetableSerializer
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.date_time import iterdays
from indico.util.fossilize import fossilize
from indico.util.fossilize.conversion import Conversion
from indico.util.string import to_unicode
from indico.web.flask.util import send_file, url_for
from indico.web.http_api.fossils import IPeriodFossil
from indico.web.http_api.hooks.base import HTTPAPIHook, IteratedDataFetcher
from indico.web.http_api.responses import HTTPAPIError
from indico.web.http_api.util import get_query_parameter


utc = pytz.timezone('UTC')
MAX_DATETIME = utc.localize(datetime(2099, 12, 31, 23, 59, 0))
MIN_DATETIME = utc.localize(datetime(2000, 1, 1))


class Period(object):
    def __init__(self, startDT, endDT):
        self.startDT = startDT
        self.endDT = endDT


def find_event_day_bounds(obj, day):
    if not (obj.start_dt_local.date() <= day <= obj.end_dt_local.date()):
        return None, None
    entries = obj.timetable_entries.filter(TimetableEntry.parent_id.is_(None),
                                           cast(TimetableEntry.start_dt.astimezone(obj.tzinfo), Date) == day).all()
    first = min(entries, key=attrgetter('start_dt')).start_dt if entries else None
    last = max(entries, key=attrgetter('end_dt')).end_dt if entries else None
    return first, last


@HTTPAPIHook.register
class EventTimeTableHook(HTTPAPIHook):
    TYPES = ('timetable',)
    RE = r'(?P<idlist>\w+(?:-\w+)*)'
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(EventTimeTableHook, self)._getParams()
        self._idList = self._pathParams['idlist'].split('-')

    def export_timetable(self, user):
        events = Event.find_all(Event.id.in_(map(int, self._idList)), ~Event.is_deleted)
        return {event.id: TimetableSerializer(event, management=False, user=user).serialize_timetable()
                for event in events}


@HTTPAPIHook.register
class EventSearchHook(HTTPAPIHook):
    TYPES = ('event',)
    RE = r'search/(?P<search_term>[^\/]+)'
    DEFAULT_DETAIL = 'events'

    def _getParams(self):
        super(EventSearchHook, self)._getParams()
        search = self._pathParams['search_term']
        self._query = search

    def export_event(self, user):
        expInt = EventSearchFetcher(user, self)
        return expInt.event(self._query)


@HTTPAPIHook.register
class CategoryEventHook(HTTPAPIHook):
    TYPES = ('event', 'categ')
    RE = r'(?P<idlist>\w+(?:-\w+)*)'
    DEFAULT_DETAIL = 'events'
    MAX_RECORDS = {
        'events': 1000,
        'contributions': 500,
        'subcontributions': 500,
        'sessions': 100,
    }

    def _getParams(self):
        super(CategoryEventHook, self)._getParams()
        self._idList = self._pathParams['idlist'].split('-')
        self._wantFavorites = False
        if 'favorites' in self._idList:
            self._idList.remove('favorites')
            self._wantFavorites = True
        self._eventType = get_query_parameter(self._queryParams, ['T', 'type'])
        if self._eventType == 'simple_event':
            self._eventType = 'lecture'
        self._occurrences = get_query_parameter(self._queryParams, ['occ', 'occurrences'], 'no') == 'yes'
        self._location = get_query_parameter(self._queryParams, ['l', 'location'])
        self._room = get_query_parameter(self._queryParams, ['r', 'room'])

    def export_categ(self, user):
        expInt = CategoryEventFetcher(user, self)
        id_list = set(self._idList)
        if self._wantFavorites and user:
            id_list.update(str(c.id) for c in user.favorite_categories)
        legacy_id_map = {m.legacy_category_id: m.category_id
                         for m in LegacyCategoryMapping.find(LegacyCategoryMapping.legacy_category_id.in_(id_list))}
        id_list = {str(legacy_id_map.get(id_, id_)) for id_ in id_list}
        return expInt.category(id_list, self._format)

    def export_categ_extra(self, user, resultList):
        expInt = CategoryEventFetcher(user, self)
        ids = set((event['categoryId'] for event in resultList))
        return expInt.category_extra(ids)

    def export_event(self, user):
        expInt = CategoryEventFetcher(user, self)
        return expInt.event(self._idList)


class SerializerBase(object):
    """Common methods for different serializers"""

    def _serialize_access_list(self, obj):
        data = {'users': [], 'groups': []}
        for manager in obj.get_access_list():
            if manager.principal_type in (PrincipalType.user, PrincipalType.email):
                data['users'].append(manager.email)
            elif manager.principal_type == PrincipalType.multipass_group:
                data['groups'].append(manager.name)
        return data

    def _serialize_date(self, date):
        if date:
            date = date.astimezone(self._hook._tz)
            return {
                'date': str(date.date()),
                'time': str(date.time()),
                'tz': str(date.tzinfo)
            }

    def _serialize_person(self, person, person_type, can_manage=False):
        """Serialize an event associated person"""

        if person:
            data = {
                '_type': person_type,
                '_fossil': self.fossils_mapping['person'].get(person_type, None),
                'first_name': person.first_name,
                'last_name': person.last_name,
                'fullName': person.get_full_name(last_name_upper=False, abbrev_first_name=False),
                'id': unicode(person.id),
                'affiliation': person.affiliation,
                'emailHash': md5(person.email.encode('utf-8')).hexdigest() if person.email else None
            }
            if isinstance(person, PersonLinkBase):
                data['db_id'] = person.id
                data['person_id'] = person.person_id
            if can_manage:
                data['email'] = person.email or None
            if person_type == 'ConferenceChair':
                data['fullName'] = person.get_full_name(last_name_upper=False, abbrev_first_name=False,
                                                        show_title=True)
            return data

    def _serialize_persons(self, persons, person_type, can_manage=False):
        return [self._serialize_person(person, person_type, can_manage) for person in persons]

    def _serialize_convener(self, convener, can_manage=False):
        data = {
            'fax': '',
            'familyName': convener.last_name,
            'firstName': convener.first_name,
            'name': convener.get_full_name(last_name_upper=False, abbrev_first_name=False),
            'last_name': convener.last_name,
            'first_name': convener.first_name,
            'title': convener.title,
            '_type': 'SlotChair',
            'affiliation': convener.affiliation,
            '_fossil': 'conferenceParticipation',
            'fullName': convener.get_full_name(last_name_upper=False, abbrev_first_name=False),
            'id': convener.person_id,
            'db_id': convener.id,
            'person_id': convener.person_id,
            'emailHash': md5(convener.person.email.encode('utf-8')).hexdigest() if convener.person.email else None
        }
        if can_manage:
            data['address'] = convener.address,
            data['phone'] = convener.phone,
            data['email'] = convener.person.email,
        return data

    def _serialize_session(self, session_, can_manage=False):
        return {
            'folders': build_folders_api_data(session_),
            'startDate': self._serialize_date(session_.start_dt) if session_.blocks else None,
            'endDate': self._serialize_date(session_.end_dt) if session_.blocks else None,
            '_type': 'Session',
            'sessionConveners': [self._serialize_convener(c, can_manage) for c in session_.conveners],
            'title': session_.title,
            'color': '#{}'.format(session_.colors.background),
            'textColor': '#{}'.format(session_.colors.text),
            'description': session_.description,
            'material': build_material_legacy_api_data(session_),
            'isPoster': session_.is_poster,
            'type': session_.type.name if session_.type else None,
            'url': url_for('sessions.display_session', session_, _external=True),
            'roomFullname': session_.room_name,
            'location': session_.venue_name,
            'address': session_.address,
            '_fossil': 'sessionMinimal',
            'numSlots': len(session_.blocks),
            'id': (session_.legacy_mapping.legacy_session_id
                   if session_.legacy_mapping else unicode(session_.friendly_id)),
            'db_id': session_.id,
            'friendly_id': session_.friendly_id,
            'room': session_.get_room_name(full=False)
        }

    fossils_mapping = {
        'event': {
            'events': 'conferenceMetadata',
            'contributions': 'conferenceMetadataWithContribs',
            'subcontributions': 'conferenceMetadataWithSubContribs',
            'sessions': 'conferenceMetadataWithSessions'
        },
        'contribution': {
            'contributions': 'contributionMetadata',
            'subcontributions': 'contributionMetadataWithSubContribs',
            'sessions': 'contributionMetadataWithSubContribs'
        },
        'block': {
            'sessions': 'sessionMetadata',
            'contributions': 'sessionMetadataWithContributions'
        },
        'person': {
            'Avatar': 'conferenceChairMetadata',
            'ConferenceChair': 'conferenceChairMetadata',
            'ContributionParticipation': 'contributionParticipationMetadata',
            'SubContribParticipation': 'contributionParticipationMetadata'
        }
    }

    def _build_event_api_data_base(self, event):
        return {
            '_type': 'Conference',
            'id': unicode(event.id),
            'title': event.title,
            'description': event.description,
            'startDate': self._serialize_date(event.start_dt),
            'timezone': event.timezone,
            'endDate': self._serialize_date(event.end_dt),
            'room': event.get_room_name(full=False),
            'location': event.venue_name,
            'address': event.address,
            'type': event.type_.legacy_name,
            'references': map(self.serialize_reference, event.references)
        }

    def _build_session_event_api_data(self, event):
        data = self._build_event_api_data_base(event)
        data.update({
            '_fossil': 'conference',
            'adjustedStartDate': self._serialize_date(event.start_dt_local),
            'adjustedEndDate': self._serialize_date(event.end_dt_local),
            'bookedRooms': Conversion.reservationsList(event.reservations.all()),
            'supportInfo': {
                '_fossil': 'supportInfo',
                'caption': event.contact_title,
                '_type': 'SupportInfo',
                'email': ', '.join(event.contact_emails),
                'telephone': ', '.join(event.contact_phones)
            },
        })
        return data

    def _serialize_session_block(self, block, serialized_session, session_access_list, can_manage):
        block_data = {
            '_type': 'SessionSlot',
            '_fossil': self.fossils_mapping['block'].get(self._detail_level),
            'id': block.id,  # TODO: Need to check if breaking the `session_id-block_id` format is OK
            'conference': self._build_session_event_api_data(block.event),
            'startDate': self._serialize_date(block.timetable_entry.start_dt) if block.timetable_entry else None,
            'endDate': self._serialize_date(block.timetable_entry.end_dt) if block.timetable_entry else None,
            'description': '',  # Session blocks don't have a description
            'title': block.full_title,
            'url': url_for('sessions.display_session', block.session, _external=True),
            'contributions': map(self._serialize_contribution, block.contributions),
            'note': build_note_api_data(block.note),
            'session': serialized_session,
            'room': block.get_room_name(full=False),
            'roomFullname': block.room_name,
            'location': block.venue_name,
            'inheritLoc': block.inherit_location,
            'inheritRoom': block.own_room is None,
            'slotTitle': block.title,
            'address': block.address,
            'conveners': [self._serialize_convener(c, can_manage) for c in block.person_links]
        }
        if session_access_list:
            block_data['allowed'] = session_access_list
        return block_data

    def _build_session_api_data(self, session_):
        can_manage = self.user is not None and session_.can_manage(self.user)
        session_access_list = None
        serialized_session = self._serialize_session(session_, can_manage)
        if can_manage:
            session_access_list = self._serialize_access_list(session_)
        return [self._serialize_session_block(b, serialized_session, session_access_list, can_manage)
                for b in session_.blocks]

    @staticmethod
    def serialize_reference(reference):
        """Return the data for a reference"""
        return {
            'type': reference.reference_type.name,
            'value': reference.value,
            'url': reference.url,
            'urn': reference.urn
        }

    def _serialize_contribution(self, contrib, include_subcontribs=True):
        can_manage = self.user is not None and contrib.can_manage(self.user)
        data = {
            '_type': 'Contribution',
            '_fossil': self.fossils_mapping['contribution'].get(self._detail_level),
            'id': (contrib.legacy_mapping.legacy_contribution_id
                   if contrib.legacy_mapping else unicode(contrib.friendly_id)),
            'db_id': contrib.id,
            'friendly_id': contrib.friendly_id,
            'title': contrib.title,
            'startDate': self._serialize_date(contrib.start_dt) if contrib.start_dt else None,
            'endDate': self._serialize_date(contrib.start_dt + contrib.duration) if contrib.start_dt else None,
            'duration': contrib.duration.seconds // 60,
            'roomFullname': contrib.room_name,
            'room': contrib.get_room_name(full=False),
            'note': build_note_api_data(contrib.note),
            'location': contrib.venue_name,
            'type': contrib.type.name if contrib.type else None,
            'description': contrib.description,
            'folders': build_folders_api_data(contrib),
            'url': url_for('contributions.display_contribution', contrib, _external=True),
            'material': build_material_legacy_api_data(contrib),
            'speakers': self._serialize_persons(contrib.speakers, person_type='ContributionParticipation',
                                                can_manage=can_manage),
            'primaryauthors': self._serialize_persons(contrib.primary_authors, person_type='ContributionParticipation',
                                                      can_manage=can_manage),
            'coauthors': self._serialize_persons(contrib.secondary_authors, person_type='ContributionParticipation',
                                                 can_manage=can_manage),
            'keywords': contrib.keywords,
            'track': contrib.track.title if contrib.track else None,
            'session': contrib.session.title if contrib.session else None,
            'references': map(self.serialize_reference, contrib.references),
            'board_number': contrib.board_number
        }
        if include_subcontribs:
            data['subContributions'] = map(self._serialize_subcontribution, contrib.subcontributions)
        if can_manage:
            data['allowed'] = self._serialize_access_list(contrib)
        return data

    def _serialize_subcontribution(self, subcontrib):
        can_manage = self.user is not None and subcontrib.contribution.can_manage(self.user)
        data = {
            '_type': 'SubContribution',
            '_fossil': 'subContributionMetadata',
            'id': (subcontrib.legacy_mapping.legacy_subcontribution_id
                   if subcontrib.legacy_mapping else unicode(subcontrib.friendly_id)),
            'db_id': subcontrib.id,
            'friendly_id': subcontrib.friendly_id,
            'title': subcontrib.title,
            'duration': subcontrib.duration.seconds // 60,
            'note': build_note_api_data(subcontrib.note),
            'material': build_material_legacy_api_data(subcontrib),
            'folders': build_folders_api_data(subcontrib),
            'speakers': self._serialize_persons(subcontrib.speakers, person_type='SubContribParticipation',
                                                can_manage=can_manage),
            'references': map(self.serialize_reference, subcontrib.references)
        }
        return data


class CategoryEventFetcher(IteratedDataFetcher, SerializerBase):
    def __init__(self, user, hook):
        super(CategoryEventFetcher, self).__init__(user, hook)
        self._eventType = hook._eventType
        self._occurrences = hook._occurrences
        self._location = hook._location
        self._room = hook._room
        self.user = user
        self._detail_level = get_query_parameter(request.args.to_dict(), ['d', 'detail'], 'events')
        if self._detail_level not in ('events', 'contributions', 'subcontributions', 'sessions'):
            raise HTTPAPIError('Invalid detail level: {}'.format(self._detail_level), 400)

    def _calculate_occurrences(self, event, from_dt, to_dt, tz):
        start_dt = max(from_dt, event.start_dt) if from_dt else event.start_dt
        end_dt = min(to_dt, event.end_dt) if to_dt else event.end_dt
        for day in iterdays(start_dt, end_dt):
            first_start, last_end = find_event_day_bounds(event, day.date())
            if first_start is not None:
                yield Period(first_start, last_end)

    def _get_query_options(self, detail_level):
        acl_user_strategy = joinedload('acl_entries').joinedload('user')
        # remote group membership checks will trigger a load on _all_emails
        # but not all events use this so there's no need to eager-load them
        # acl_user_strategy.noload('_primary_email')
        # acl_user_strategy.noload('_affiliation')
        creator_strategy = joinedload('creator')
        contributions_strategy = subqueryload('contributions')
        contributions_strategy.subqueryload('references')
        if detail_level in {'subcontributions', 'sessions'}:
            contributions_strategy.subqueryload('subcontributions').subqueryload('references')
        sessions_strategy = subqueryload('sessions')
        options = [acl_user_strategy, creator_strategy]
        if detail_level in {'contributions', 'subcontributions', 'sessions'}:
            options.append(contributions_strategy)
        if detail_level == 'sessions':
            options.append(sessions_strategy)
        options.append(undefer('effective_protection_mode'))
        return options

    def category(self, idlist, format):
        try:
            idlist = map(int, idlist)
        except ValueError:
            raise HTTPAPIError('Category IDs must be numeric', 400)
        if format == 'ics':
            buf = serialize_categories_ical(idlist, self.user,
                                            event_filter=Event.happens_between(self._fromDT, self._toDT),
                                            event_filter_fn=self._filter_event,
                                            update_query=self._update_query)
            return send_file('events.ics', buf, 'text/calendar')
        else:
            query = (Event.query
                     .filter(~Event.is_deleted,
                             Event.category_chain_overlaps(idlist),
                             Event.happens_between(self._fromDT, self._toDT))
                     .options(*self._get_query_options(self._detail_level)))
        query = self._update_query(query)
        return self.serialize_events(x for x in query if self._filter_event(x) and x.can_access(self.user))

    def category_extra(self, ids):
        if self._toDT is None:
            has_future_events = False
        else:
            query = Event.find(Event.category_id.in_(ids), ~Event.is_deleted, Event.start_dt > self._toDT)
            has_future_events = query.has_rows()
        return {
            'eventCategories': self._build_category_path_data(ids),
            'moreFutureEvents': has_future_events
        }

    def event(self, idlist):
        query = (Event.find(Event.id.in_(idlist),
                            ~Event.is_deleted,
                            Event.happens_between(self._fromDT, self._toDT))
                 .options(*self._get_query_options(self._detail_level)))
        query = self._update_query(query)
        return self.serialize_events(x for x in query if self._filter_event(x) and x.can_access(self.user))

    def _filter_event(self, event):
        if self._room or self._location or self._eventType:
            if self._eventType and event.type_.name != self._eventType:
                return False
            if self._location:
                name = event.venue_name
                if not name or not fnmatch.fnmatch(name.lower(), self._location.lower()):
                    return False
            if self._room:
                name = event.room_name
                if not name or not fnmatch.fnmatch(name.lower(), self._room.lower()):
                    return False
        return True

    def _update_query(self, query):
        order = get_query_parameter(request.args.to_dict(), ['o', 'order'])
        desc = get_query_parameter(request.args.to_dict(), ['c', 'descending']) == 'yes'
        limit = get_query_parameter(request.args.to_dict(), ['n', 'limit'])
        offset = get_query_parameter(request.args.to_dict(), ['O', 'offset'])

        col = {
            'start': Event.start_dt,
            'end': Event.end_dt,
            'id': Event.id,
            'title': Event.title
        }.get(order)
        if col:
            query = query.order_by(col.desc() if desc else col)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        return query

    def serialize_events(self, events):
        return map(self._build_event_api_data, events)

    def _serialize_category_path(self, category):
        visibility = {'id': None, 'name': 'Everywhere'}
        path = [self._serialize_path_entry(category_data) for category_data in category.chain]
        if category.visibility is not None:
            try:
                path_segment = path[-category.visibility]
            except IndexError:
                pass
            else:
                visibility['id'] = path_segment['id']
                visibility['name'] = path_segment['name']
        path.append({'visibility': visibility})
        return path

    def _serialize_path_entry(self, category_data):
        return {
            '_fossil': 'categoryMetadata',
            'type': 'Category',
            'name': category_data['title'],
            'id': category_data['id'],
            'url': url_for('categories.display', category_id=category_data['id'], _external=True)
        }

    def _build_category_path_data(self, ids):
        return [{'_type': 'CategoryPath', 'categoryId': category.id, 'path': self._serialize_category_path(category)}
                for category in Category.query.filter(Category.id.in_(ids)).options(undefer('chain'))]

    def _build_event_api_data(self, event):
        can_manage = self.user is not None and event.can_manage(self.user)
        data = self._build_event_api_data_base(event)
        data.update({
            '_fossil': self.fossils_mapping['event'].get(self._detail_level),
            'categoryId': event.category_id,
            'category': event.category.title,
            'note': build_note_api_data(event.note),
            'roomFullname': event.room_name,
            'url': event.external_url,
            'creationDate': self._serialize_date(event.created_dt),
            'creator': self._serialize_person(event.creator, person_type='Avatar', can_manage=can_manage),
            'hasAnyProtection': event.effective_protection_mode != ProtectionMode.public,
            'roomMapURL': event.room.map_url if event.room else None,
            'folders': build_folders_api_data(event),
            'chairs': self._serialize_persons(event.person_links, person_type='ConferenceChair', can_manage=can_manage),
            'material': build_material_legacy_api_data(event) + filter(None, [build_note_legacy_api_data(event.note)])
        })

        event_category_path = event.category.chain
        visibility = {'id': '', 'name': 'Everywhere'}
        if event.visibility is None:
            pass  # keep default
        elif event.visibility == 0:
            visibility['name'] = 'Nowhere'
        elif event.visibility:
            try:
                path_segment = event_category_path[-event.visibility]
            except IndexError:
                pass
            else:
                visibility['id'] = path_segment['id']
                visibility['name'] = path_segment['title']
        data['visibility'] = visibility

        if can_manage:
            data['allowed'] = self._serialize_access_list(event)
        if self._detail_level in {'contributions', 'subcontributions'}:
            data['contributions'] = []
            for contribution in event.contributions:
                include_subcontribs = self._detail_level == 'subcontributions'
                serialized_contrib = self._serialize_contribution(contribution, include_subcontribs)
                data['contributions'].append(serialized_contrib)
        elif self._detail_level == 'sessions':
            # Contributions without a session
            data['contributions'] = []
            for contribution in event.contributions:
                if not contribution.session:
                    serialized_contrib = self._serialize_contribution(contribution)
                    data['contributions'].append(serialized_contrib)

            data['sessions'] = []
            for session_ in event.sessions:
                data['sessions'].extend(self._build_session_api_data(session_))
        if self._occurrences:
            data['occurrences'] = fossilize(self._calculate_occurrences(event, self._fromDT, self._toDT,
                                            pytz.timezone(config.DEFAULT_TIMEZONE)),
                                            {Period: IPeriodFossil}, tz=self._tz, naiveTZ=config.DEFAULT_TIMEZONE)
        return data


class EventBaseHook(HTTPAPIHook):
    @classmethod
    def _matchPath(cls, path):
        if not hasattr(cls, '_RE'):
            cls._RE = re.compile(r'/' + cls.PREFIX + '/event/' + cls.RE + r'\.(\w+)$')
        return cls._RE.match(path)


class SessionContribHook(EventBaseHook):
    DEFAULT_DETAIL = 'contributions'
    MAX_RECORDS = {
        'contributions': 500,
        'subcontributions': 500,
    }

    def _getParams(self):
        super(SessionContribHook, self)._getParams()
        self._idList = self._pathParams['idlist'].split('-')
        self._eventId = self._pathParams['event']

    def export_session(self, user):
        expInt = SessionFetcher(user, self)
        return expInt.session(self._idList)

    def export_contribution(self, user):
        expInt = ContributionFetcher(user, self)
        return expInt.contribution(self._idList)


class SessionContribFetcher(IteratedDataFetcher):
    def __init__(self, user, hook):
        super(SessionContribFetcher, self).__init__(user, hook)
        self._eventId = hook._eventId


@HTTPAPIHook.register
class SessionHook(SessionContribHook):
    RE = r'(?P<event>[\w\s]+)/session/(?P<idlist>\w+(?:-\w+)*)'
    METHOD_NAME = 'export_session'


class SessionFetcher(SessionContribFetcher, SerializerBase):
    def __init__(self, user, hook):
        super(SessionFetcher, self).__init__(user, hook)
        self.user = user

    def session(self, idlist):
        event = Event.get(self._eventId, is_deleted=False)
        if not event:
            return []
        idlist = set(map(int, idlist))
        sessions = (Session.query.with_parent(event)
                    .filter(Session.id.in_(idlist),
                            ~Session.is_deleted)
                    .all())
        # Fallback for friendly_id
        sessions += (Session.query
                     .with_parent(event)
                     .filter(Session.friendly_id.in_(idlist - {s.id for s in sessions}),
                             ~Session.is_deleted)
                     .all())
        self._detail_level = 'contributions'
        return self._build_sessions_api_data(sessions)

    def _build_sessions_api_data(self, sessions):
        """Returns an aggregated list of session blocks given the sessions."""

        session_blocks = []
        for session_ in sessions:
            can_manage = self.user is not None and session_.can_manage(self.user)
            session_access_list = None
            serialized_session = self._serialize_session(session_)
            if self.user and session_.can_manage(self.user):
                session_access_list = self._serialize_access_list(session_)
            session_blocks.extend(self._serialize_session_block(b, serialized_session, session_access_list, can_manage)
                                  for b in session_.blocks)
        return session_blocks


@HTTPAPIHook.register
class ContributionHook(SessionContribHook):
    RE = r'(?P<event>[\w\s]+)/contribution/(?P<idlist>\w+(?:-\w+)*)'
    METHOD_NAME = 'export_contribution'


class ContributionFetcher(SessionContribFetcher):
    def contribution(self, idlist):
        raise ServiceUnavailable


class EventSearchFetcher(IteratedDataFetcher):
    def event(self, query):
        def _iterate_objs(query_string):
            query = (Event.query
                     .filter(Event.title_matches(to_unicode(query_string)),
                             ~Event.is_deleted)
                     .options(undefer('effective_protection_mode')))
            sort_dir = db.desc if self._descending else db.asc
            if self._orderBy == 'start':
                query = query.order_by(sort_dir(Event.start_dt))
            elif self._orderBy == 'end':
                query = query.order_by(sort_dir(Event.end_dt))
            elif self._orderBy == 'id':
                query = query.order_by(sort_dir(Event.id))
            elif self._orderBy == 'title':
                query = query.order_by(sort_dir(db.func.lower(Event.title)))

            counter = 0
            # Query the DB in chunks of 1000 records per query until the limit is satisfied
            for event in query.yield_per(1000):
                if event.can_access(self._user):
                    counter += 1
                    # Start yielding only when the counter reaches the given offset
                    if (self._offset is None) or (counter > self._offset):
                        yield event
                        # Stop querying the DB when the limit is satisfied
                        if (self._limit is not None) and (counter == self._offset + self._limit):
                            break

        for event in _iterate_objs(query):
            yield {
                'id': event.id,
                'title': event.title,
                'startDate': event.start_dt,
                'hasAnyProtection': event.effective_protection_mode == ProtectionMode.protected
            }
