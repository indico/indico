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

import fnmatch
import itertools
import re
import pytz
from datetime import datetime
from hashlib import md5

from flask import request
from sqlalchemy.orm import joinedload, subqueryload

from indico.modules.attachments.api.util import build_folders_api_data, build_material_legacy_api_data
from indico.modules.events import Event
from indico.modules.events.notes.util import build_note_api_data
from indico.modules.categories import LegacyCategoryMapping
from indico.util.date_time import iterdays
from indico.util.fossilize import fossilize
from indico.util.fossilize.conversion import Conversion
from indico.util.string import to_unicode

from indico.web.flask.util import url_for
from indico.web.http_api.fossils import (IConferenceMetadataWithContribsFossil, IConferenceMetadataFossil,
                                         IConferenceMetadataWithSubContribsFossil,
                                         IConferenceMetadataWithSessionsFossil, IPeriodFossil,
                                         ICategoryMetadataFossil, ICategoryProtectedMetadataFossil,
                                         ISessionMetadataWithContributionsFossil,
                                         ISessionMetadataWithSubContribsFossil, IContributionMetadataFossil,
                                         IContributionMetadataWithSubContribsFossil)
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.hooks.base import HTTPAPIHook, IteratedDataFetcher

from MaKaC.conference import CategoryManager
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import ConferenceHolder
from MaKaC.schedule import ScheduleToJson

utc = pytz.timezone('UTC')
MAX_DATETIME = utc.localize(datetime(2099, 12, 31, 23, 59, 0))
MIN_DATETIME = utc.localize(datetime(2000, 1, 1))


class Period(object):
    def __init__(self, startDT, endDT):
        self.startDT = startDT
        self.endDT = endDT


@HTTPAPIHook.register
class EventTimeTableHook(HTTPAPIHook):
    TYPES = ('timetable',)
    RE = r'(?P<idlist>\w+(?:-\w+)*)'

    def _getParams(self):
        super(EventTimeTableHook, self)._getParams()
        self._idList = self._pathParams['idlist'].split('-')

    def export_timetable(self, aw):
        ch = ConferenceHolder()
        d = {}
        for cid in self._idList:
            conf = ch.getById(cid)
            d[cid] = ScheduleToJson.process(conf.getSchedule(), self._tz.tzname(None),
                                            aw, days=None, mgmtMode=False)
        return d


@HTTPAPIHook.register
class EventSearchHook(HTTPAPIHook):
    TYPES = ('event',)
    RE = r'search/(?P<search_term>[^\/]+)'
    DEFAULT_DETAIL = 'events'

    def _getParams(self):
        super(EventSearchHook, self)._getParams()
        search = self._pathParams['search_term']
        self._query = search

    def export_event(self, aw):
        expInt = EventSearchFetcher(aw, self)
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
        if self._eventType == 'lecture':
            self._eventType = 'simple_event'
        self._occurrences = get_query_parameter(self._queryParams, ['occ', 'occurrences'], 'no') == 'yes'
        self._location = get_query_parameter(self._queryParams, ['l', 'location'])
        self._room = get_query_parameter(self._queryParams, ['r', 'room'])

    def export_categ(self, aw):
        expInt = CategoryEventFetcher(aw, self)
        id_list = set(self._idList)
        if self._wantFavorites and aw.getUser():
            id_list.update(c.getId() for c in aw.getUser().user.favorite_categories)
        legacy_id_map = {m.legacy_category_id: m.category_id
                         for m in LegacyCategoryMapping.find(LegacyCategoryMapping.legacy_category_id.in_(id_list))}
        id_list = {str(legacy_id_map.get(id_, id_)) for id_ in id_list}
        return expInt.category(id_list)

    def export_categ_extra(self, aw, resultList):
        ids = set((event['categoryId'] for event in resultList))
        return {
            'eventCategories': CategoryEventFetcher.getCategoryPath(ids, aw),
            "moreFutureEvents": False if not self._toDT else
                                True in [IndexesHolder().getById('categoryDateAll')
                                         .hasObjectsAfter(catId, self._toDT) for catId in self._idList]
        }

    def export_event(self, aw):
        expInt = CategoryEventFetcher(aw, self)
        return expInt.event(self._idList)


class CategoryEventFetcher(IteratedDataFetcher):
    DETAIL_INTERFACES = {
        'events': IConferenceMetadataFossil,
        'contributions': IConferenceMetadataWithContribsFossil,
        'subcontributions': IConferenceMetadataWithSubContribsFossil,
        'sessions': IConferenceMetadataWithSessionsFossil
    }

    def __init__(self, aw, hook):
        super(CategoryEventFetcher, self).__init__(aw, hook)
        self._eventType = hook._eventType
        self._occurrences = hook._occurrences
        self._location = hook._location
        self._room = hook._room

    def _postprocess(self, obj, fossil, iface):
        return self._addOccurrences(fossil, obj, self._fromDT, self._toDT)

    @classmethod
    def getCategoryPath(cls, idList, aw):
        res = []
        for id in idList:
            res.append({
                '_type': 'CategoryPath',
                'categoryId': id,
                'path': cls._getCategoryPath(id, aw)
            })
        return res

    @staticmethod
    def _getCategoryPath(id, aw):
        path = []
        firstCat = cat = CategoryManager().getById(id)
        visibility = cat.getVisibility()
        while cat:
            # the first category (containing the event) is always shown, others only with access
            iface = ICategoryMetadataFossil if firstCat or cat.canAccess(aw) else ICategoryProtectedMetadataFossil
            path.append(fossilize(cat, iface))
            cat = cat.getOwner()
        if visibility > len(path):
            visibilityName = "Everywhere"
        elif visibility == 0:
            visibilityName = "Nowhere"
        else:
            categId = path[visibility-1]["id"]
            visibilityName = CategoryManager().getById(categId).getName()
        path.reverse()
        path.append({"visibility": {"name": visibilityName}})
        return path

    @staticmethod
    def _eventDaysIterator(conf):
        """
        Iterates over the daily times of an event
        """
        sched = conf.getSchedule()
        for day in iterdays(conf.getStartDate(), conf.getEndDate()):
            # ignore days that have no occurrences
            if sched.getEntriesOnDay(day):
                startDT = sched.calculateDayStartDate(day)
                endDT = sched.calculateDayEndDate(day)
                if startDT != endDT:
                    yield Period(startDT, endDT)

    def _addOccurrences(self, fossil, obj, startDT, endDT):
        if self._occurrences:
            (startDT, endDT) = (startDT or MIN_DATETIME,
                                endDT or MAX_DATETIME)
            # get occurrences in the date interval
            fossil['occurrences'] = fossilize(itertools.ifilter(
                lambda x: x.startDT >= startDT and x.endDT <= endDT, self._eventDaysIterator(obj)),
                {Period: IPeriodFossil}, tz=self._tz, naiveTZ=self._serverTZ)
        return fossil

    def _makeFossil(self, obj, iface):
        legacy_obj = obj.as_legacy if isinstance(obj, Event) else obj
        return fossilize(obj, iface, tz=self._tz, naiveTZ=self._serverTZ,
                         filters={'access': self._userAccessFilter},
                         canModify=legacy_obj.canModify(self._aw),
                         mapClassType={'AcceptedContribution': 'Contribution'})

    def _get_query_options(self, include_contribs=False):
        acl_user_strategy = joinedload('acl_entries').joinedload('user')
        # remote group membership checks will trigger a load on _all_emails
        # but not all events use this so there's no need to eager-load them
        # acl_user_strategy.noload('_primary_email')
        # acl_user_strategy.noload('_affiliation')
        creator_strategy = joinedload('creator')
        contributions_strategy = subqueryload('contributions')
        if include_contribs:
            return acl_user_strategy, creator_strategy, contributions_strategy
        return acl_user_strategy, creator_strategy

    def category(self, idlist):
        filter = None
        if self._room or self._location or self._eventType:
            def filter(obj):
                if self._eventType and obj.getType() != self._eventType:
                    return False
                if self._location:
                    name = obj.getLocation() and obj.getLocation().getName()
                    if not name or not fnmatch.fnmatch(name.lower(), self._location.lower()):
                        return False
                if self._room:
                    name = obj.getRoom() and obj.getRoom().getName()
                    if not name or not fnmatch.fnmatch(name.lower(), self._room.lower()):
                        return False
                return True

        query = (Event.query
                 .filter(~Event.is_deleted,
                         Event.category_chain.overlap(map(int, idlist)),
                         Event.happens_between(self._fromDT, self._toDT))
                 .options(*self._get_query_options()))
        return self._process((x.as_legacy for x in query), filter)

    def event(self, idlist):
        events = (Event.find(Event.id.in_(idlist), ~Event.is_deleted)
                  .options(*self._get_query_options(include_contribs=True))
                  .all())

        ch = ConferenceHolder()

        def _iterate_objs(objIds):
            for objId in objIds:
                obj = ch.getById(objId, True)
                if obj is not None:
                    yield obj
        return self.serialize_events(events)

    def serialize_events(self, events):
        return map(self._build_event_api_data, events)

    def _serialize_date(self, date):
        if date:
            return {
                'date': str(date.date()),
                'time': str(date.time()),
                'tz': str(date.tzinfo)
            }

    def _serialize_persons(self, persons):
        return [self._serialize_person(person) for person in persons]

    def _serialize_person(self, person):
        if person:
            return {
                'fullName': person.get_full_name(last_name_upper=False, abbrev_first_name=False),
                'id': person.id if getattr(person, 'id', None) else person.person_id,
                'affiliation': person.affiliation,
                'emailHash': md5(person.email).hexdigest() if person.email else None,
            }

    def _build_event_api_data(self, event):
        data = {
            'id': event.id,
            'categoryId': event.category_id,
            'category': event.category.getTitle(),
            'title': event.title,
            'type': event.type,
            'description': event.description,
            'note': build_note_api_data(event.note),
            'roomFullname': event.room_name,
            'room': event.room_name,
            'location': event.venue_name,
            'address': event.address,
            'url': url_for('event.conferenceDisplay', confId=event.id, _external=True),
            'startDate': self._serialize_date(event.start_dt),
            'endDate': self._serialize_date(event.end_dt),
            'modificationDate': self._serialize_date(event.as_legacy.getModificationDate()),
            'creationDate': self._serialize_date(event.as_legacy.getCreationDate()),
            'creator': self._serialize_person(event.creator),
            'hasAnyProtection': event.as_legacy.hasAnyProtection(),
            'timezone': event.timezone,
            'roomMapURL': event.room.map_url if event.room else None,
            'visibility': Conversion.visibility(event.as_legacy),
            'folders': build_folders_api_data(event)
            # TODO: what about '_type'?
            # TODO: what about 'material'? It doesn't return the material of the event ('folders' does that)
            # TODO: what about 'chairs'. It doesn't return the Chairpersons

        }
        detail = get_query_parameter(request.args.to_dict(), ['d', 'detail'])
        if detail == 'contributions':
            data['contributions'] = []
            for contribution in event.contributions:
                data['contributions'].append(self._build_contribution_api_data(contribution))
        return data

    def _build_contribution_api_data(self, contrib):
        data = {
            'id': contrib.id,
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
            'url': url_for('event.contributionDisplay', confId=contrib.event_id, contribId=contrib.friendly_id,
                           _external=True),
            'material': build_material_legacy_api_data(contrib),
            'speakers': self._serialize_persons([x.person for x in contrib.speakers]),
            'primaryauthors': self._serialize_persons([x.person for x in contrib.primary_authors]),
            'coauthors': self._serialize_persons([x.person for x in contrib.secondary_authors]),
            'keywords': contrib.keywords,
            'track': contrib.track.title if contrib.track else None,
            'session': contrib.session.title if contrib.session else None,
            # TODO: what about '_type'?
        }
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

    def export_session(self, aw):
        expInt = SessionFetcher(aw, self)
        return expInt.session(self._idList)

    def export_contribution(self, aw):
        expInt = ContributionFetcher(aw, self)
        return expInt.contribution(self._idList)


class SessionContribFetcher(IteratedDataFetcher):
    def __init__(self, aw, hook):
        super(SessionContribFetcher, self).__init__(aw, hook)
        self._eventId = hook._eventId


@HTTPAPIHook.register
class SessionHook(SessionContribHook):
    RE = r'(?P<event>[\w\s]+)/session/(?P<idlist>\w+(?:-\w+)*)'
    METHOD_NAME = 'export_session'


class SessionFetcher(SessionContribFetcher):
    DETAIL_INTERFACES = {
        'contributions': ISessionMetadataWithContributionsFossil,
        'subcontributions': ISessionMetadataWithSubContribsFossil,
    }

    def session(self, idlist):
        ch = ConferenceHolder()
        event = ch.getById(self._eventId)

        def _iterate_objs(objIds):
            for objId in objIds:
                session = event.getSessionById(objId)
                for obj in session.getSlotList():
                    if obj is not None:
                        yield obj

        return self._process(_iterate_objs(idlist))


@HTTPAPIHook.register
class ContributionHook(SessionContribHook):
    RE = r'(?P<event>[\w\s]+)/contribution/(?P<idlist>\w+(?:-\w+)*)'
    METHOD_NAME = 'export_contribution'


class ContributionFetcher(SessionContribFetcher):
    DETAIL_INTERFACES = {
        'contributions': IContributionMetadataFossil,
        'subcontributions': IContributionMetadataWithSubContribsFossil,
    }

    def contribution(self, idlist):
        event = Event.find(id=self._eventId, is_deleted=False).first()

        def _iterate_objs(objIds):
            for objId in objIds:
                obj = event.contributions.filter_by(id=objId).one()
                if obj is not None:
                    yield obj

        return self._process(_iterate_objs(idlist))


class EventSearchFetcher(IteratedDataFetcher):
    DETAIL_INTERFACES = {
        'events': IConferenceMetadataFossil,
    }

    def event(self, query):
        def _iterate_objs(query_string):
            query = Event.find(Event.title_matches(to_unicode(query_string)), ~Event.is_deleted)
            if self._orderBy == 'start':
                query = query.order_by(Event.start_dt)
            elif self._orderBy == 'id':
                query = query.order_by(Event.id)

            counter = 0
            # Query the DB in chunks of 1000 records per query until the limit is satisfied
            for event in query.yield_per(1000):
                if event.can_access(self._aw.getUser().user if self._aw.getUser() else None):
                    counter += 1
                    # Start yielding only when the counter reaches the given offset
                    if (self._offset is None) or (counter > self._offset):
                        yield event
                        # Stop querying the DB when the limit is satisfied
                        if (self._limit is not None) and (counter == self._offset + self._limit):
                            break

        if self._orderBy in ['start', 'id', None]:
            obj_list = _iterate_objs(query)
        else:
            obj_list = sorted(_iterate_objs(query), key=self._sortingKeys.get(self._orderBy), reverse=self._descending)
        for event in obj_list:
            yield {
                'id': event.id,
                'title': event.title,
                'startDate': event.start_dt,
                'hasAnyProtection': event.as_legacy.hasAnyProtection()
            }
