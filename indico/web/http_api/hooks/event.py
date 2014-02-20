# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.


# python stdlib imports
import fnmatch
import itertools
import re
import pytz
from zope.index.text import parsetree
from datetime import datetime

# indico imports
from indico.util.fossilize import fossilize

from indico.web.http_api.fossils import IConferenceMetadataWithContribsFossil, IConferenceMetadataFossil, \
    IConferenceMetadataWithSubContribsFossil, IConferenceMetadataWithSessionsFossil, IPeriodFossil, \
    ICategoryMetadataFossil, ICategoryProtectedMetadataFossil, ISessionMetadataWithContributionsFossil, \
    ISessionMetadataWithSubContribsFossil, IContributionMetadataFossil, IContributionMetadataWithSubContribsFossil
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.hooks.base import HTTPAPIHook, IteratedDataFetcher

# indico legacy imports
from MaKaC.conference import CategoryManager
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import ConferenceHolder
from MaKaC.rb_tools import Period, datespan
from MaKaC.schedule import ScheduleToJson

utc = pytz.timezone('UTC')
MAX_DATETIME = utc.localize(datetime(2099, 12, 31, 23, 59, 0))
MIN_DATETIME = utc.localize(datetime(2000, 1, 1))


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
        self._query = ' AND '.join(map(lambda y: "*%s*" % y, filter(lambda x: len(x) > 0, search.split(' '))))

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
        idList = list(self._idList)
        if self._wantFavorites and aw.getUser():
            idList += [c.getId() for c in aw.getUser().getLinkTo('category', 'favorite')]
        return expInt.category(idList)

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
        for day in datespan(conf.getStartDate(), conf.getEndDate()):
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
        return fossilize(obj, iface, tz=self._tz, naiveTZ=self._serverTZ,
                         filters={'access': self._userAccessFilter},
                         canModify=obj.canModify(self._aw),
                         mapClassType={'AcceptedContribution': 'Contribution'})

    def category(self, idlist):
        idx = IndexesHolder().getById('categoryDateAll')

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

        iters = itertools.chain(*(idx.iterateObjectsIn(catId, self._fromDT, self._toDT) for catId in idlist))
        return self._process(iters, filter)

    def event(self, idlist):
        ch = ConferenceHolder()

        def _iterate_objs(objIds):
            for objId in objIds:
                obj = ch.getById(objId, True)
                if obj is not None:
                    yield obj

        return self._process(_iterate_objs(idlist))


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

    def _getParams(self):
        super(SessionHook, self)._getParams()
        self._type = 'session'


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

    def _getParams(self):
        super(ContributionHook, self)._getParams()
        self._type = 'contribution'


class ContributionFetcher(SessionContribFetcher):
    DETAIL_INTERFACES = {
        'contributions': IContributionMetadataFossil,
        'subcontributions': IContributionMetadataWithSubContribsFossil,
    }

    def contribution(self, idlist):
        ch = ConferenceHolder()
        event = ch.getById(self._eventId)

        def _iterate_objs(objIds):
            for objId in objIds:
                obj = event.getContributionById(objId)
                if obj is not None:
                    yield obj

        return self._process(_iterate_objs(idlist))


class EventSearchFetcher(IteratedDataFetcher):
    DETAIL_INTERFACES = {
        'events': IConferenceMetadataFossil,
    }

    def event(self, query):
        ch = ConferenceHolder()
        index = IndexesHolder().getById("conferenceTitle")

        def _iterate_objs(query):
            try:
                results = index.search(query)
            except parsetree.ParseError:
                results = []
            for id, _ in results:
                event = ch.getById(id)
                if event is not None and event.canAccess(self._aw):
                    yield event

        for event in sorted(itertools.islice(_iterate_objs(query), self._offset, self._offset + self._limit),
                            key=self._sortingKeys.get(self._orderBy), reverse=self._descending):
            yield {
                'id': event.getId(),
                'title': event.getTitle(),
                'startDate': event.getStartDate(),
                'hasAnyProtection': event.hasAnyProtection()
            }
