# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


from MaKaC.common.utils import *
from MaKaC.conference import Conference

from indico.core.api import Component, IListener
from indico.core.api.events import IObjectLifeCycleListener, ITimeActionListener, \
     IMetadataChangeListener
from indico.core.api.location import ILocationActionListener

from MaKaC.common.logger import Logger
import zope.interface


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
    def titleChanged(cls, obj, oldTitle, newTitle):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyTitleChange(oldTitle, newTitle)
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the title parameters when changing an event title" + str(e))

    @classmethod
    def deleted(cls, obj, params={}):
        if obj.__class__ == Conference:
            obj = obj.getCSBookingManager()
            obj.notifyDeletion()

    # ILocationActionListener
    @classmethod
    def placeChanged(cls, obj):
        obj = obj.getCSBookingManager()
        obj.notifyLocationChange()
