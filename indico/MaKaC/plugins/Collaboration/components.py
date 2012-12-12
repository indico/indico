# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import zope.interface

from MaKaC.common.utils import *
from MaKaC.conference import Conference, Contribution
from MaKaC.rb_location import IIndexableByManagerIds
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.indexes import CSBookingInstanceWrapper
from MaKaC.common.logger import Logger
from MaKaC.common.indexes import IndexesHolder


from indico.util.event import uid_to_obj
from indico.core.index import OOIndex, Index
from indico.core.index.adapter import IIndexableByStartDateTime
from indico.core.extpoint import Component, IListener
from indico.core.extpoint.events import IObjectLifeCycleListener, ITimeActionListener, \
     IMetadataChangeListener
from indico.core.extpoint.location import ILocationActionListener
from indico.core.extpoint.index import ICatalogIndexProvider
from indico.core.index import Catalog


class CSBookingInstanceIndexCatalog(Index):

    def __init__(self):
        self._container = {}
        self.initialize(initialize=False)

    def __getitem__(self, key):
        return self._container[key]

    def __setitem__(self, key, value):
        self._container[key] = value

    def initialize(self, dbi=None, initialize=True):
        for index in ['WebcastRequest', 'RecordingRequest', 'All Requests']:
            idx = CSBookingInstanceIndex(index)
            if initialize:
                idx.initialize()
            self._container[index] = idx

    def getIndexes(self):
        return self._container.values()


class CSBookingInstanceIndex(OOIndex):

    def __init__(self, index_name):
        super(CSBookingInstanceIndex, self).__init__(IIndexableByStartDateTime)
        self.index_name = index_name

    def initialize(self, dbi=None):
        # empty tree
        self.clear()

        idx = IndexesHolder().getById('collaboration')

        for conf, bks in idx.getBookings(self.index_name, 'conferenceStartDate', None, None, None).getResults():
            for bk in bks:
                self.index_booking(bk)

    def index_booking(self, bk):
        conf = bk.getConference()
        contribs = bk.getTalkSelectionList()
        choose = bk.isChooseTalkSelected()

        # if contributions chosen individually
        if choose and contribs:
            for contrib_id in contribs:
                # check that contrib is in valid room
                if CollaborationTools.isAbleToBeWebcastOrRecorded(conf.getContributionById(contrib_id), bk.getType()):
                    self.index_obj(CSBookingInstanceWrapper(bk, conf.getContributionById(contrib_id)))
        # We need to check if it is a lecture with a correct room
        elif CollaborationTools.isAbleToBeWebcastOrRecorded(conf, bk.getType()) or conf.getType() !="simple_event":
            for day in daysBetween(conf.getStartDate(), conf.getEndDate()):
                bkw = CSBookingInstanceWrapper(bk, conf,
                                               day.replace(hour=0, minute=0, second=0),
                                               day.replace(hour=23, minute=59, second=59))
                self.index_obj(bkw)

    def iter_bookings(self, fromDT, toDT):

        added_whole_events = set()

        for dt, bkw in self.iteritems(fromDT, toDT):
            evt = bkw.getOriginalBooking().getConference()
            entries = evt.getSchedule().getEntriesOnDay(dt)

            if bkw.getObject() == evt:
                # this means the booking relates to an event
                if evt in added_whole_events:
                    continue

                if not evt.getSchedule().getEntries():
                    yield dt, CSBookingInstanceWrapper(bkw.getOriginalBooking(),
                                                       evt)
                    # mark whole event as "added"
                    added_whole_events.add(evt)

                if entries:
                    # what a mess...
                    if self.index_name == 'All Requests':
                        talks = set(CollaborationTools.getCommonTalkInformation(evt, 'RecordingRequest', 'recordingCapableRooms')[3]) | \
                            set(CollaborationTools.getCommonTalkInformation(evt, 'WebcastRequest', 'webcastCapableRooms')[3])
                    else:
                        var = 'recordingCapableRooms' if self.index_name == 'RecordingRequest' else 'webcastCapableRooms'
                        talks = CollaborationTools.getCommonTalkInformation(evt, self.index_name, var)[3]

                    # add contribs that concern this day
                    for contrib in talks:
                        if contrib.isScheduled() and contrib.getStartDate().date() == dt.date():
                            yield dt, CSBookingInstanceWrapper(bkw.getOriginalBooking(),
                                                               contrib)
            else:
                yield dt, bkw

    def unindex_booking(self, bk, fromDT=None, toDT=None):
        to_unindex = set()
        # go over possible wrappers
        conf = bk.getConference()

        for dt, bkw in self.iteritems((fromDT or conf.getStartDate()).replace(hour=0, minute=0, second=0),
                                      (toDT or conf.getEndDate()).replace(hour=23, minute=59, second=59)):
            if bkw.getOriginalBooking() == bk:
                to_unindex.add(bkw)

        for bkw in to_unindex:
            self.unindex_obj(bkw)

    def unindex_talk(self, bk, talk):
        to_unindex = set()
        bookingList = self.get(talk.getStartDate(), [])
        for bkw in bookingList:
            if bkw.getObject() == talk:
                to_unindex.add(bkw)
        for bkw in to_unindex:
            self.unindex_obj(bkw)

    def index_talk(self, bk, talk):
        self.index_obj(CSBookingInstanceWrapper(bk, talk))


class CatalogIndexProvider(Component):
    zope.interface.implements(ICatalogIndexProvider)

    def catalogIndexProvider(self, obj):
        return [('cs_booking_instance', CSBookingInstanceIndexCatalog)]


class EventCollaborationListener(Component):

    zope.interface.implements(IObjectLifeCycleListener,
                              ITimeActionListener,
                              ILocationActionListener,
                              IMetadataChangeListener)

    """In this case, obj is a conference object. Since all we
       need is already programmed in CSBookingManager, we get the
       object of this class and we call the appropiate method"""
    @classmethod
    def dateChanged(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyEventDateChanges(params['oldStartDate'], params['newStartDate'], params['oldEndDate'], params['newEndDate'])
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the date parameters when changing an event date" + str(e))

    @classmethod
    def startDateChanged(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyEventDateChanges(params['oldDate'], params['newDate'], None, None)
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the date parameters when changing an event date" + str(e))

    @classmethod
    def startTimeChanged(self, obj, sdate):
        """ No one is calling this method in the class Conference. Probably this is completely unnecessary"""
        bookingManager = obj.getCSBookingManager()
        bookingManager.notifyEventDateChanges(sdate, obj.startDate, None, None)

    @classmethod
    def endTimeChanged(self, obj, edate):
        """ No one is calling this method in the class Conference. Probably this is completely unnecessary"""
        bookingManager = obj.getCSBookingManager()
        bookingManager.notifyEventDateChanges(None, None, edate, obj.endDate)

    @classmethod
    def timezoneChanged(self, obj, oldTimezone):
        bookingManager = obj.getCSBookingManager()
        #ATTENTION! At this moment this method notifyTimezoneChange in the class CSBookingManager
        #just returns [], so if you're expecting it to do something just implement whatever you
        #want to do with it
        bookingManager.notifyTimezoneChange(oldTimezone, obj.timezone)

    @classmethod
    def endDateChanged(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyEventDateChanges(None, None, params['oldDate'], params['newDate'])
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the date parameters when changing an event date" + str(e))

    @classmethod
    def eventDatesChanged(cls, obj, oldStartDate, oldEndDate,
                          newStartDate, newEndDate):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyEventDateChanges(oldStartDate, newStartDate,
                                       oldEndDate, newEndDate)
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the date parameters when changing an event date" + str(e))

    @classmethod
    def contributionUnscheduled(self, contrib):
        if contrib.getStartDate() is not None:
            csBookingManager = contrib.getCSBookingManager()
            for booking in csBookingManager.getBookingList():
                booking.unindex_talk(contrib)

    @classmethod
    def contributionScheduled(self, contrib):
        csBookingManager = contrib.getCSBookingManager()
        for booking in csBookingManager.getBookingList():
            booking.index_talk(contrib)

    @classmethod
    def eventTitleChanged(cls, obj, oldTitle, newTitle):

        obj = obj.getCSBookingManager()
        try:
            obj.notifyTitleChange(oldTitle, newTitle)
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the title parameters when changing an event title" + str(e))

    @classmethod
    def infoChanged(cls, obj):
        #Update Speaker Wrapper only if obj is a Conference
        if isinstance(obj, Conference) or isinstance(obj, Contribution):
            bookingManager = obj.getCSBookingManager()

            try:
                bookingManager.notifyInfoChange()
            except Exception, e:
                Logger.get('PluginNotifier').error("Exception while trying to access the info changes " + str(e))


    @classmethod
    def deleted(cls, obj, params={}):
        if obj.__class__ == Conference:
            obj = obj.getCSBookingManager()
            obj.notifyDeletion()
        elif obj.__class__ == Contribution and obj.getStartDate() is not None:
            csBookingManager = obj.getCSBookingManager()
            for booking in csBookingManager.getBookingList():
                booking.unindex_talk(obj)

    # ILocationActionListener
    @classmethod
    def placeChanged(cls, obj):
        obj = obj.getCSBookingManager()
        obj.notifyLocationChange()

    @classmethod
    def locationChanged(cls, obj, oldLocation, newLocation):
        csBookingManager = obj.getCSBookingManager()
        for booking in csBookingManager.getBookingList():
            booking.unindex_talk(obj)
            booking.index_talk(obj)

    @classmethod
    def roomChanged(cls, obj, oldLocation, newLocation):
        csBookingManager = obj.getCSBookingManager()
        for booking in csBookingManager.getBookingList():
            booking.unindex_talk(obj)
            booking.index_talk(obj)
