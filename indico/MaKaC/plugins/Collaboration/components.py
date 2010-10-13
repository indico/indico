'''
Created on Apr 22, 2010

@author: cesar
'''
from MaKaC.common.utils import *
from MaKaC.plugins.notificationComponents import Component
from MaKaC.plugins.notificationComponents import IListener
from MaKaC.plugins.notificationComponents import IManagementEventsListener
from MaKaC.common.logger import Logger
import zope.interface


class EventCollaborationListener(Component):

    zope.interface.implements(IListener, IManagementEventsListener)

    """In this case, obj is a conference object. Since all we
       need is already programmed in CSBookingManager, we get the
       object of this class and we call the appropiate method"""
    @classmethod
    def notifyDateChange(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyEventDateChanges(params['oldStartDate'], params['newStartDate'], params['oldEndDate'], params['newEndDate'])
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the date parameters when changing an event date" + str(e))

    @classmethod
    def notifyStartDateChange(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyEventDateChanges(params['oldDate'], params['newDate'], None, None)
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the date parameters when changing an event date" + str(e))

    @classmethod
    def notifyStartTimeChange(self, obj, sdate):
        """ No one is calling this method in the class Conference. Probably this is completely unnecessary"""
        bookingManager = obj.getCSBookingManager()
        bookingManager.notifyEventDateChanges(sdate, obj.startDate, None, None)

    @classmethod
    def notifyEndTimeChange(self, obj, edate):
        """ No one is calling this method in the class Conference. Probably this is completely unnecessary"""
        bookingManager = obj.getCSBookingManager()
        bookingManager.notifyEventDateChanges(None, None, edate, obj.endDate)

    @classmethod
    def notifySetTimezone(self, obj, oldTimezone):
        bookingManager = obj.getCSBookingManager()
        #ATTENTION! At this moment this method notifyTimezoneChange in the class CSBookingManager
        #just returns [], so if you're expecting it to do something just implement whatever you
        #want to do with it
        bookingManager.notifyTimezoneChange(oldTimezone, obj.timezone)

    @classmethod
    def notifyEndDateChange(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyEventDateChanges(None, None, params['oldDate'], params['newDate'])
        except Exception, e:
            Logger.get('PluginNotifier').error("Exception while trying to access to the date parameters when changing an event date" + str(e))

    @classmethod
    def notifyTitleChange(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        try:
            obj.notifyTitleChange(params['oldTitle'], params['newTitle'])
        except Exception, e:
           Logger.get('PluginNotifier').error("Exception while trying to access to the title parameters when changing an event title" + str(e))


    @classmethod
    def notifyDelete(cls, obj, params={}):
        obj = obj.getCSBookingManager()
        obj.notifyDeletion()
