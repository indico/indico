# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

from persistent import Persistent
from MaKaC.common.Counter import Counter
from MaKaC.common.utils import formatDateTime, parseDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate, setAdjustedDate,\
    datetimeToUnixTimeInt
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.plugins.base import PluginsHolder
from MaKaC.errors import MaKaCError
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.logger import Logger
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools,\
    MailTools
from MaKaC.conference import Observer
from MaKaC.common.contextManager import ContextManager
from MaKaC.webinterface.common.tools import hasTags
from MaKaC.plugins.Collaboration import mail
from MaKaC.common.mail import GenericMailer
import os, inspect
import MaKaC.plugins.Collaboration as Collaboration
from MaKaC.i18n import _
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.plugins.Collaboration.fossils import ICSErrorBaseFossil, ICSSanitizationErrorFossil,\
    ICSBookingBaseConfModifFossil, ICSBookingBaseIndexingFossil


class CSBookingManager(Persistent, Observer):
    """ Class for managing the bookins of a meeting.
        It will store the list of bookings. Adding / removing / editing bookings should be through this class.
    """

    _shouldBeTitleNotified = True
    _shouldBeDateChangeNotified = True
    _shouldBeDeletionNotified = True

    def __init__(self, conf):
        """ Constructor for the CSBookingManager class.
            conf: a Conference object. The meeting that owns this CSBookingManager.
        """
        self._conf = conf
        self._counter = Counter(1)
        # a dict where the bookings will be stored. The key will be the booking id, the value a CSBookingBase object.
        self._bookings = {}

        # an index of bookings by type. The key will be a booking type (string), the value a list of booking id
        self._bookingsByType = {}

        # a list of ids with hidden bookings
        self._hiddenBookings = set()

        # an index of video services managers for each plugin. key: plugin name, value: list of users
        self._managers = {}

        #we register as an observer of the conference
        self._conf.addObserver(self)

    def getOwner(self):
        """ Returns the Conference (the meeting) that owns this CSBookingManager object.
        """
        return self._conf

    def restoreAsObserver(self):
        if not self in self._conf.getObservers():
            self._conf.addObserver(self)

    def isCSAllowed(self, user = None):
        """ Returns if the associated event should display a Video Services tab
            This can depend on the kind of event (meeting, lecture, conference), on the equipment of the room...
            If a user is provided, we will take into account if the user can manage the plugin (for example,
            an event manager cannot manage an admin-only plugin)
        """
        pluginsPerEventType = CollaborationTools.getCollaborationPluginType().getOption("pluginsPerEventType").getValue()
        if pluginsPerEventType:
            for plugin in pluginsPerEventType[self._conf.getType()]:
                if plugin.isActive() and (user is None or CollaborationTools.canUserManagePlugin(self._conf, plugin, user)):
                    return True
        return False

    def getAllowedPlugins(self):
        """ Returns a list of allowed plugins (Plugin objects) for this event.
            Only active plugins are returned.
            This can depend on the kind of event (meeting, lecture, conference), on the equipment of the room...
        """
        pluginsPerEventType = CollaborationTools.getCollaborationPluginType().getOption("pluginsPerEventType").getValue()
        if pluginsPerEventType is not None:
            allowedForThisEvent = pluginsPerEventType[self._conf.getType()]
            return [plugin for plugin in allowedForThisEvent if plugin.isActive()]


    def getBookingList(self, sorted = False, filterByType = None, notify = False, onlyPublic = False):
        """ Returns a list of all the bookings.
            If sorted = True, the list of bookings will be sorted by id.
            If filterByType = None, all bookings are returned.
            Otherwise, just those of the type "filterByType" if filterByType is a string,
            or if it is a list of strings, those who have a type included in filterByType.
        """
        if not hasattr(self, "_bookingsByType"): #TODO: remove when safe
            self._bookingsByType = {}

        if filterByType is not None:
            if type(filterByType) == str:
                keys = self._bookingsByType.get(filterByType, [])
            if type(filterByType) == list:
                keys = []
                for pluginName in filterByType:
                    keys.extend(self._bookingsByType.get(pluginName, []))
        else:
            keys = self._bookings.keys()

        if onlyPublic and self.getHiddenBookings():
            keys = set(keys)
            keys = keys.difference(self.getHiddenBookings())
            keys = list(keys)

        if sorted:
            keys.sort(key = lambda k: int(k))

        bookingList = [self._bookings[k] for k in keys]

        #we notify all the bookings that they have been viewed. If a booking doesn't need to be viewed, nothing will happen
        if notify:
            for booking in bookingList:
                if booking.needsToBeNotifiedOnView():
                    try:
                        booking._notifyOnView()
                    except Exception, e:
                        Logger.get('VideoServ').error("Exception while notifying to a booking that it is being viewed. Exception: " + str(e))

        return bookingList

    def getBooking(self, id):
        """ Returns a booking given its id.
        """
        return self._bookings[id]

    def getSingleBooking(self, type, notify = False):
        """ Returns the single booking of a plugin who only allows one booking.
            type: a string with the name of the plugin
            If the plugin actually allows multiple bookings, an exception will be thrown
            If the plugin has no booking, None will be returned.
            Otherwise the booking will be returned
        """
        if CollaborationTools.getCSBookingClass(type)._allowMultiple:
            raise CollaborationException("Plugin type " + str(type) + " is not a single-booking plugin")
        blist = self._bookingsByType.get(type,[])
        if blist:
            booking = self._bookings[blist[0]]
            if notify:
                try:
                    booking._notifyOnView()
                except Exception, e:
                    Logger.get('VideoServ').error("Exception while notifying to a booking that it is being viewed. Exception: " + str(e))
            return booking
        else:
            return None

    def getHiddenBookings(self):
        if not hasattr(self, '_hiddenBookings'):
            self._hiddenBookings = set()
        return self._hiddenBookings

    def hasBookings(self):
        return len(self._bookings) > 0

    def canCreateBooking(self, type):
        """ Returns if it's possible to create a booking of this given type
        """
        if not CollaborationTools.getCSBookingClass(type)._allowMultiple:
            return len(self.getBookingList(filterByType = type)) == 0
        return True

    def createBooking(self, bookingType, bookingParams = {}):
        """ Adds a new booking to the list of bookings.
            The id of the new booking is auto-generated incrementally.
            After generating the booking, its "performBooking" method will be called.

            bookingType: a String with the booking's plugin. Example: "DummyPlugin", "EVO"
            bookingParams: a dictionary with the parameters necessary to create the booking.
                           "create the booking" usually means Indico deciding if the booking can take place.
                           if "startDate" and "endDate" are among the keys, they will be taken out of the dictionary.
        """
        if self.canCreateBooking(bookingType):
            newBooking = CollaborationTools.getCSBookingClass(bookingType)(bookingType, self._conf)

            error = newBooking.setBookingParams(bookingParams)

            if isinstance(error, CSSanitizationError):
                return error
            elif error:
                raise CollaborationServiceException("Problem while creating a booking of type " + bookingType)
            else:
                newId = self._getNewBookingId()
                newBooking.setId(newId)
                createResult = newBooking._create()
                if isinstance(createResult, CSErrorBase):
                    return createResult
                else:
                    self._bookings[newId] = newBooking
                    self._bookingsByType.setdefault(bookingType,[]).append(newId)
                    if newBooking.isHidden():
                        self.getHiddenBookings().add(newId)
                    self._indexBooking(newBooking)
                    self._notifyModification()
                    self._sendMail(newBooking, 'new')
                    return newBooking
        else:
            #we raise an exception because the web interface should take care of this never actually happening
            raise CollaborationServiceException(bookingType + " only allows to create 1 booking per event")

    def _indexBooking(self, booking):
        if booking.shouldBeIndexed():
            indexes = self._getIndexList(booking)
            for index in indexes:
                index.indexBooking(booking)

    def changeBooking(self, bookingId, bookingParams):
        """
        Changes the bookingParams of a CSBookingBase object.
        After updating the booking, its 'performBooking' method will be called.
        bookingId: the id of the CSBookingBase object to change
        bookingParams: a dictionary with the new parameters that will modify the booking
        'modify the booking' can mean that maybe the booking will be rejected with the new parameters.
        if 'startDate' and 'endDate' are among the keys, they will be taken out of the dictionary.
        """

        booking = self.getBooking(bookingId)


        oldStartDate = booking.getStartDate()
        oldModificationDate = booking.getModificationDate()
        oldBookingParams = booking.getBookingParams() #this is a copy so it's ok

        error = booking.setBookingParams(bookingParams)
        if isinstance(error, CSSanitizationError):
            return error
        elif error:
            CSBookingManager._rollbackChanges(booking, oldBookingParams, oldModificationDate)
            raise CollaborationServiceException("Problem while modifying a booking of type " + booking.getType())
        else:
            modifyResult = booking._modify(oldBookingParams)
            if isinstance(modifyResult, CSErrorBase):
                CSBookingManager._rollbackChanges(booking, oldBookingParams, oldModificationDate)
                return modifyResult
            else:
                modificationDate = nowutc()
                booking.setModificationDate(modificationDate)

                if booking.isHidden():
                    self.getHiddenBookings().add(booking.getId())
                elif booking.getId() in self.getHiddenBookings():
                    self.getHiddenBookings().remove(booking.getId())

                self._changeStartDateInIndex(booking, oldStartDate, booking.getStartDate())
                self._changeModificationDateInIndex(booking, oldModificationDate, modificationDate)

                if booking.hasAcceptReject():
                    if booking.getAcceptRejectStatus() is not None:
                        booking.clearAcceptRejectStatus()
                        self._addToPendingIndex(booking)

                self._notifyModification()

                self._sendMail(booking, 'modify')
                return booking

    @classmethod
    def _rollbackChanges(cls, booking, oldBookingParams, oldModificationDate):
        booking.setBookingParams(oldBookingParams)
        booking.setModificationDate(oldModificationDate)

    def _changeConfTitleInIndex(self, booking, oldTitle, newTitle):
        if booking.shouldBeIndexed():
            indexes = self._getIndexList(booking)
            for index in indexes:
                index.changeEventTitle(booking, oldTitle, newTitle)

    def _changeStartDateInIndex(self, booking, oldStartDate, newStartDate):
        if booking.shouldBeIndexed() and booking.hasStartDate():
            indexes = self._getIndexList(booking)
            for index in indexes:
                index.changeStartDate(booking, oldStartDate, newStartDate)

    def _changeModificationDateInIndex(self, booking, oldModificationDate, newModificationDate):
        if booking.shouldBeIndexed():
            indexes = self._getIndexList(booking)
            for index in indexes:
                index.changeModificationDate(booking, oldModificationDate, newModificationDate)

    def _changeConfStartDateInIndex(self, booking, oldConfStartDate, newConfStartDate):
        if booking.shouldBeIndexed():
            indexes = self._getIndexList(booking)
            for index in indexes:
                index.changeConfStartDate(booking, oldConfStartDate, newConfStartDate)

    def removeBooking(self, id):
        """ Removes a booking given its id.
        """
        booking = self.getBooking(id)
        bookingType = booking.getType()

        removeResult = booking._delete()
        if isinstance(removeResult, CSErrorBase):
            return removeResult
        else:
            del self._bookings[id]
            self._bookingsByType[bookingType].remove(id)
            if not self._bookingsByType[bookingType]:
                del self._bookingsByType[bookingType]
            if id in self.getHiddenBookings():
                self.getHiddenBookings().remove(id)

            self._unindexBooking(booking)

            self._notifyModification()

            self._sendMail(booking, 'remove')

            return booking

    def _unindexBooking(self, booking):
        if booking.shouldBeIndexed():
            indexes = self._getIndexList(booking)
            for index in indexes:
                index.unindexBooking(booking)

    def startBooking(self, id):
        booking = self._bookings[id]
        if booking.canBeStarted():
            booking._start()
            return booking
        else:
            raise CollaborationException(_("Tried to start booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking cannot be started."))

    def stopBooking(self, id):
        booking = self._bookings[id]
        if booking.canBeStopped():
            booking._stop()
            return booking
        else:
            raise CollaborationException(_("Tried to stop booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking cannot be stopped."))

    def checkBookingStatus(self, id):
        booking = self._bookings[id]
        if booking.hasCheckStatus():
            booking._checkStatus()
            return booking
        else:
            raise ServiceError(_("Tried to check status of booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking does not support the check status service."))

    def acceptBooking(self, id):
        booking = self._bookings[id]
        if booking.hasAcceptReject():
            if booking.getAcceptRejectStatus() is None:
                self._removeFromPendingIndex(booking)
            booking.accept()
            return booking
        else:
            raise ServiceError(_("Tried to accept booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking cannot be accepted."))

    def rejectBooking(self, id, reason):
        booking = self._bookings[id]
        if booking.hasAcceptReject():
            if booking.getAcceptRejectStatus() is None:
                self._removeFromPendingIndex(booking)
            booking.reject(reason)
            return booking
        else:
            raise ServiceError("ERR-COLL10", _("Tried to reject booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking cannot be rejected."))

    def _addToPendingIndex(self, booking):
        if booking.shouldBeIndexed():
            indexes = self._getPendingIndexList(booking)
            for index in indexes:
                index.indexBooking(booking)

    def _removeFromPendingIndex(self, booking):
        if booking.shouldBeIndexed():
            indexes = self._getPendingIndexList(booking)
            for index in indexes:
                index.unindexBooking(booking)

    def _getNewBookingId(self):
        return self._counter.newCount()

    def _getIndexList(self, booking):
        """ Returns a list of BookingsIndex objects where the booking should be indexed.
            This list includes:
            -an index of all bookings
            -an index of bookings of the given type
            -an index of all bookings in the category of the event
            -an index of booking of the given type, in the category of the event
            If the booking type declared common indexes:
            -the common indexes
            -the common indexes for the category of the event
            If the booking is of the Accept/Reject type
            -same indexes as above, but only for pending bookings
        """
        collaborationIndex = IndexesHolder().getById("collaboration")
        indexes = [collaborationIndex.getAllBookingsIndex(),
                   collaborationIndex.getIndex(booking.getType())]

        for commonIndexName in booking.getCommonIndexes():
            indexes.append(collaborationIndex.getIndex(commonIndexName))

        if booking.hasAcceptReject() and booking.getAcceptRejectStatus() is None:
            indexes.extend(self._getPendingIndexList(booking))

        return indexes

    def _getPendingIndexList(self, booking):
        collaborationIndex = IndexesHolder().getById("collaboration")
        indexes = [collaborationIndex.getIndex("all_pending"),
                   collaborationIndex.getIndex(booking.getType() + "_pending")]

        for commonIndexName in booking.getCommonIndexes():
            indexes.append(collaborationIndex.getIndex(commonIndexName + "_pending"))

        return indexes

    def _sendMail(self, booking, operation):
        if MailTools.needToSendEmails():

            if operation == 'new':
                try:
                    notification = mail.NewBookingNotification(booking)
                    GenericMailer.sendAndLog(notification, self._conf,
                                         "MaKaC/plugins/Collaboration/base.py",
                                         self._conf.getCreator())
                except Exception, e:
                    Logger.get('VideoServ').error(
                        """Could not send NewBookingNotification for booking with id %s of event with id %s, exception: %s""" %
                        (booking.getId(), self._conf.getId(), str(e)))
                    raise e

            elif operation == 'modify':
                try:
                    notification = mail.BookingModifiedNotification(booking)
                    GenericMailer.sendAndLog(notification, self._conf,
                                         "MaKaC/plugins/Collaboration/base.py",
                                         self._conf.getCreator())
                except Exception, e:
                    Logger.get('VideoServ').error(
                        """Could not send BookingModifiedNotification for booking with id %s of event with id %s, exception: %s""" %
                        (booking.getId(), self._conf.getId(), str(e)))
                    raise e

            elif operation == 'remove':
                try:
                    notification = mail.BookingDeletedNotification(booking)
                    GenericMailer.sendAndLog(notification, self._conf,
                                         "MaKaC/plugins/Collaboration/base.py",
                                         self._conf.getCreator())
                except Exception, e:
                    Logger.get('VideoServ').error(
                        """Could not send BookingDeletedNotification for booking with id %s of event with id %s, exception: %s""" %
                        (booking.getId(), self._conf.getId(), str(e)))
                    raise e

    def getManagers(self):
        if not hasattr(self, "_managers"):
            self._managers = {}
        return self._managers

    def addPluginManager(self, plugin, user):
        #TODO: use .linkTo on the user. To be done when the list of roles of a user is actually needed for smth...
        self.getManagers().setdefault(plugin, []).append(user)
        self._notifyModification()

    def removePluginManager(self, plugin, user):
        #TODO: use .unlinkTo on the user. To be done when the list of roles of a user is actually needed for smth...
        if user in self.getManagers().setdefault(plugin,[]):
            self.getManagers()[plugin].remove(user)
            self._notifyModification()

    def getVideoServicesManagers(self):
        return self.getManagers().setdefault('all', [])

    def isVideoServicesManager(self, user):
        return user in self.getManagers().setdefault('all', [])

    def getPluginManagers(self, plugin):
        return self.getManagers().setdefault(plugin, [])

    def isPluginManager(self, plugin, user):
        return user in self.getManagers().setdefault(plugin, [])

    def getAllManagers(self):
        """ Returns a list with all the managers, no matter their type
            The returned list is not ordered.
        """
        managers = set()
        for managerList in self.getManagers().itervalues():
            managers = managers.union(managerList)
        return list(managers)

    def isPluginManagerOfAnyPlugin(self, user):
        #TODO: this method is not optimal. to be optimal, we should store somewhere an index where the key
        #is the user, and the value is a list of plugins where they are managers.
        #this could be done with .getLinkTo, but we would need to change the .linkTo method to add extra information
        #(since we cannot create a role for each plugin)
        if self.isVideoServicesManager(user):
            return True
        else:
            for plugin in self.getManagers().iterkeys():
                if self.isPluginManager(plugin, user):
                    return True
            return False

    def notifyTitleChange(self, oldTitle, newTitle):
        """ Notifies the CSBookingManager that the title of the event (meeting) it's attached to has changed.
            The CSBookingManager will reindex all its bookings in the event title index.
            This method will be called by the event (meeting) object
        """
        for booking in self.getBookingList():
            try:
                self._changeConfTitleInIndex(booking, oldTitle, newTitle)
            except Exception, e:
                Logger.get('VideoServ').error("Exception while reindexing a booking in the event title index because its event's title changed: " + str(e))


    def notifyEventDateChanges(self, oldStartDate = None, newStartDate = None, oldEndDate = None, newEndDate = None):
        """ Notifies the CSBookingManager that the start and / or end dates of the event it's attached to have changed.
            The CSBookingManager will change the dates of all the bookings that want to be updated.
            If there are problems (such as a booking not being able to be modified)
            it will write a list of strings describing the problems in the 'dateChangeNotificationProblems' context variable.
            (each string is produced by the _booking2NotifyProblem method).
            This method will be called by the event (meeting) object.
        """
        startDateChanged = oldStartDate is not None and newStartDate is not None and not oldStartDate == newStartDate
        endDateChanged = oldEndDate is not None and newEndDate is not None and not oldEndDate == newEndDate
        someDateChanged = startDateChanged or endDateChanged

        Logger.get("VideoServ").info("""CSBookingManager: starting notifyEventDateChanges. Arguments: confId=%s, oldStartDate=%s, newStartDate=%s, oldEndDate=%s, newEndDate=%s""" %
                                     (str(self._conf.getId()), str(oldStartDate), str(newStartDate), str(oldEndDate), str(newEndDate)))

        if someDateChanged:
            problems = []
            for booking in self.getBookingList():
                if booking.hasStartDate():
                    if startDateChanged:
                        try:
                            self._changeConfStartDateInIndex(booking, oldStartDate, newStartDate)
                        except Exception, e:
                            Logger.get('VideoServ').error("Exception while reindexing a booking in the event start date index because its event's start date changed: " + str(e))

                    if booking.needsToBeNotifiedOfDateChanges():
                        Logger.get("VideoServ").info("""CSBookingManager: notifying date changes to booking %s of event %s""" %
                                                     (str(booking.getId()), str(self._conf.getId())))
                        oldBookingStartDate = booking.getStartDate()
                        oldBookingEndDate = booking.getEndDate()
                        oldBookingParams = booking.getBookingParams() #this is a copy so it's ok

                        if startDateChanged:
                            booking.setStartDate(oldBookingStartDate + (newStartDate - oldStartDate) )
                        if endDateChanged:
                            booking.setEndDate(oldBookingEndDate + (newEndDate - oldEndDate) )

                        rollback = False
                        modifyResult = None
                        try:
                            modifyResult = booking._modify(oldBookingParams)
                            if isinstance(modifyResult, CSErrorBase):
                                Logger.get('VideoServ').warning("""Error while changing the dates of booking %s of event %s after event dates changed: %s""" %
                                                                (str(booking.getId()), str(self._conf.getId()), modifyResult.getLogMessage()))
                                rollback = True
                        except Exception, e:
                            Logger.get('VideoServ').error("""Exception while changing the dates of booking %s of event %s after event dates changed: %s""" %
                                                          (str(booking.getId()), str(self._conf.getId()), str(e)))
                            rollback = True

                        if rollback:
                            booking.setStartDate(oldBookingStartDate)
                            booking.setEndDate(oldBookingEndDate)
                            problems.append(CSBookingManager._booking2NotifyProblem(booking, modifyResult))
                        elif startDateChanged:
                            self._changeStartDateInIndex(booking, oldBookingStartDate, booking.getStartDate())
            if problems:
                ContextManager.get('dateChangeNotificationProblems')['Collaboration'] = [
                    'Some Video Services bookings could not be moved:',
                    problems,
                    'Go to [[' + str(urlHandlers.UHConfModifCollaboration.getURL(self.getOwner(), secure = CollaborationTools.isUsingHTTPS())) + ' the Video Services section]] to modify them yourself.'
                ]


    def notifyTimezoneChange(self, oldTimezone, newTimezone):
        """ Notifies the CSBookingManager that the timezone of the event it's attached to has changed.
            The CSBookingManager will change the dates of all the bookings that want to be updated.
            This method will be called by the event (Conference) object
        """
        return []

    @classmethod
    def _booking2NotifyProblem(cls, booking, modifyError):
        """ Turns a booking into a string used to tell the user
            why a date change of a booking triggered by the event's start or end date change
            went bad.
        """

        message = []
        message.extend(["The dates of the ", booking.getType(), " booking"])
        if booking.hasTitle():
            message.extend([': "', booking._getTitle(), '" (', booking.getStartDateAsString(), ' - ', booking.getEndDateAsString(), ')'])
        else:
            message.extend([' ongoing from ', booking.getStartDateAsString(), ' to ', booking.getEndDateAsString(), ''])

        message.append(' could not be changed.')
        if modifyError and modifyError.getUserMessage():
            message.extend([' Reason: ', modifyError.getUserMessage()])
        return "".join(message)


    def notifyDeletion(self):
        """ Notifies the CSBookingManager that the Conference object it is attached to has been deleted.
            The CSBookingManager will change the dates of all the bookings that want to be updated.
            This method will be called by the event (Conference) object
        """
        for booking in self.getBookingList():
            try:
                removeResult = booking._delete()
                if isinstance(removeResult, CSErrorBase):
                    Logger.get('VideoServ').warning("Error while deleting a booking of type %s after deleting an event: %s"%(booking.getType(), removeResult.getLogMessage() ))
                self._unindexBooking(booking)
            except Exception, e:
                Logger.get('VideoServ').error("Exception while deleting a booking of type %s after deleting an event: %s"%(booking.getType(), str(e) ))


    def getEventDisplayPlugins(self, sorted = False):
        """ Returns a list of names (strings) of plugins which have been configured
            as showing bookings in the event display page, and which have bookings
            already (or previously) created in the event.
            (does not check if the bookings are hidden or not)
        """

        pluginsWithEventDisplay = CollaborationTools.pluginsWithEventDisplay()
        l = []
        for pluginName in self._bookingsByType:
            if pluginName in pluginsWithEventDisplay:
                l.append(pluginName)
        if sorted:
            l.sort()
        return l

    def createTestBooking(self, bookingParams = {}):
        """ Function that creates a 'test' booking for performance test.
            Avoids to use any of the plugins except DummyPlugin
        """
        from MaKaC.plugins.Collaboration.DummyPlugin.collaboration import CSBooking as DummyBooking
        bookingType = 'DummyPlugin'
        newBooking = DummyBooking(bookingType, self._conf)
        error = newBooking.setBookingParams(bookingParams)
        if error:
            raise CollaborationServiceException("Problem while creating a test booking")
        else:
            newId = self._getNewBookingId()
            newBooking.setId(newId)
            createResult = newBooking._create()
            if isinstance(createResult, CSErrorBase):
                return createResult
            else:
                self._bookings[newId] = newBooking
                self._bookingsByType.setdefault(bookingType,[]).append(newId)
                if newBooking.isHidden():
                    self.getHiddenBookings().add(newId)
                self._indexBooking(newBooking)
                self._notifyModification()
                return newBooking

    def _notifyModification(self):
        self._p_changed = 1



class CSBookingBase(Persistent, Fossilizable):
    fossilizes(ICSBookingBaseConfModifFossil, ICSBookingBaseIndexingFossil)

    """ Base class that represents a Collaboration Systems booking.
        Every Collaboration plugin will have to implement this class.
        In the base class are gathered all the functionalities / elements that are common for all plugins.
        A booking is Persistent (DateChangeObserver inherits from Persistent) so it will be stored in the database.
        Also, every CSBookingBase object in the server will be mirrored by a Javascript object in the client, through "Pickling".

        Every class that implements the CSBookingBase has to declare the following class attributes:
            _hasStart : True if the plugin has a "start" concept. Otherwise, the "start" button will not appear, etc.
            _hasStop : True if the plugin has a "stop" concept. Otherwise, the "stop" button will not appear, etc.
            _hasCheckStatus: True if the plugin has a "check status" concept. Otherwise, the "check status" button will not appear, etc.
            _hasAcceptReject: True if the plugin has a "accept or reject" concept. Otherwise, the "accept" and "reject" buttons will not appear, etc.
            _requiresServerCallForStart : True if we should notify the server when the user presses the "start" button.
            _requiresServerCallForStop : True if we should notify the server when the user presses the "stop" button.
            _requiresClientCallForStart : True if the browser should execute some JS action when the user presses the "start" button.
            _requiresClientCallForStop : True if the browser should execute some JS action when the user presses the "stop" button.
            _needsBookingParamsCheck : True if the booking parameters should be checked after the booking is added / edited.
                                       If True, the _checkBookingParams method will be called by the setBookingParams method.
            _needsToBeNotifiedOnView: True if the booking object needs to be notified (through the "notifyOnView" method)
                                      when the user "sees" the booking, for example when returning the list of bookings.
            _canBeNotifiedOfEventDateChanges: True if bookings of this type should be able to be notified
                                              of their owner Event changing start date, end date or timezone.
            _allowMultiple: True if this booking type allows more than 1 booking per event.
    """

    _hasStart = False
    _hasStop = False
    _hasCheckStatus = False
    _hasAcceptReject = False
    _hasStartStopAll = False
    _requiresServerCallForStart = False
    _requiresServerCallForStop = False
    _requiresClientCallForStart = False
    _requiresClientCallForStop = False
    _needsBookingParamsCheck = False
    _needsToBeNotifiedOnView = False
    _canBeNotifiedOfEventDateChanges = True
    _allowMultiple = True
    _shouldBeIndexed = True
    _commonIndexes = []
    _hasStartDate = True
    _hasEventDisplay = False
    _hasTitle = False
    _adminOnly = False

    def __init__(self, bookingType, conf):
        """ Constructor for the CSBookingBase class.
            id: a string with the id of the booking
            bookingType: a string with the type of the booking. Example: "DummyPlugin", "EVO"
            conf: a Conference object to which this booking belongs (through the CSBookingManager object). The meeting of this booking.
            startTime: TODO
            endTime: TODO

            Other attributes initialized by this constructor:
            -_bookingParams: the parameters necessary to perform the booking.
                             The plugins will decide if the booking gets authorized or not depending on this.
                             Needs to be defined by the implementing class, as keys with empty values.
            -_startingParams: the parameters necessary to start the booking.
                              They will be used on the client for the local start action.
                              Needs to be defined by the implementing class, as keys with empty values.
            -_statusMessage, _statusClass : they represent the status message (and its CSS class) that will be displayed.
                 The status of a booking can be, for example: "Booking Accepted" (in green), "Booking refused" (in red)
            -_warning: A warning is a plugin-defined object, with information to show to the user when
                       the operation went well but we still have to show some info to the user.
            -_canBeStarted: If its value is true, the "start" button for the booking will be able to be pushed.
                            It can be false if, for example:
                              + The plugin didn't like the booking parameters and doesn't give permission for the booking to be started,
                              + The booking has already been started, so the "start" button has to be faded in order not to be pressed twice.
            -_canBeStopped: If its value is true, the "stop" button for the booking will be able to be pushed.
                            For example, before starting a booking the "stop" button for the booking will be faded.
            -_permissionToStart : Even if the "start" button for a booking is able to be pushed, there may be cases where the booking should
                            not start. For example, if it's not the correct time yet.
                            In that case "permissionToStart" should be set to false so that the booking doesn't start.
            -_permissionToStop: Same as permissionToStart. Sometimes the booking should not be allowed to stop even if the "stop" button is available.
        """
        self._id = None
        self._type = bookingType
        self._plugin = CollaborationTools.getPlugin(self._type)
        self._conf = conf
        self._warning = None
        self._creationDate = nowutc()
        self._modificationDate = nowutc()
        self._creationDateTimestamp = int(datetimeToUnixTimeInt(self._creationDate))
        self._modificationDateTimestamp = int(datetimeToUnixTimeInt(self._modificationDate))
        self._startDate = None
        self._endDate = None
        self._startDateTimestamp = None
        self._endDateTimestamp = None
        self._statusMessage = ""
        self._statusClass = ""
        self._acceptRejectStatus = None #None = not yet accepted / rejected; True = accepted; False = rejected
        self._rejectReason = ""
        self._bookingParams = {}
        self._canBeDeleted = True
        self._canBeStarted = self._hasStart
        self._canBeStopped = False
        self._permissionToStart = False
        self._permissionToStop = False
        self._needsToBeNotifiedOfDateChanges = self._canBeNotifiedOfEventDateChanges
        self._hidden = False

        setattr(self, "_" + bookingType + "Options", CollaborationTools.getPlugin(bookingType).getOptions())


    def getId(self):
        """ Returns the internal, per-conference id of the booking.
            This attribute will be available in Javascript with the "id" identifier.
        """
        return self._id

    def setId(self, id):
        """ Sets the internal, per-conference id of the booking
        """
        self._id = id

    def getType(self):
        """ Returns the type of the booking, as a string: "EVO", "DummyPlugin"
            This attribute will be available in Javascript with the "type" identifier.
        """
        return self._type

    def getConference(self):
        """ Returns the owner of this CSBookingBase object, which is a Conference object representing the meeting.
        """
        return self._conf

    def getWarning(self):
        """ Returns a warning attached to this booking.
            A warning is a plugin-defined object, with information to show to the user when
            the operation went well but we still have to show some info to the user.
            To be overloaded by plugins.
        """
        if not hasattr(self, '_warning'):
            self._warning = None
        return self._warning

    def getCreationDate(self):
        """ Returns the date this booking was created, as a timezone localized datetime object
        """
        if not hasattr(self, "_creationDate"): #TODO: remove when safe
            self._creationDate = nowutc()
        return self._creationDate

    def getAdjustedCreationDate(self, tz=None):
        """ Returns the booking creation date, adjusted to a given timezone.
            If no timezone is provided, the event's timezone is used
        """
        return getAdjustedDate(self.getCreationDate(), self.getConference(), tz)

    def getCreationDateTimestamp(self):
        if not hasattr(object, "_creationDateTimestamp"): #TODO: remove when safe
            self._creationDateTimestamp = int(datetimeToUnixTimeInt(self._creationDate))
        return self._creationDateTimestamp

    def getModificationDate(self):
        """ Returns the date this booking was modified last
        """
        if not hasattr(self, "_modificationDate"):  #TODO: remove when safe
            self._modificationDate = nowutc()
        return self._modificationDate

    def getAdjustedModificationDate(self, tz=None):
        """ Returns the booking last modification date, adjusted to a given timezone.
            If no timezone is provided, the event's timezone is used
        """
        return getAdjustedDate(self.getModificationDate(), self.getConference(), tz)

    def getModificationDateTimestamp(self):
        if not hasattr(object, "_modificationDateTimestamp"): #TODO: remove when safe
            self._modificationDateTimestamp = int(datetimeToUnixTimeInt(self._modificationDate))
        return self._modificationDateTimestamp

    def setModificationDate(self, date):
        """ Sets the date this booking was modified last
        """
        self._modificationDate = date
        if date:
            self._modificationDateTimestamp = int(datetimeToUnixTimeInt(date))
        else:
            self._modificationDateTimestamp = None

    def getBookingsOfSameType(self, sorted = False):
        """ Returns a list of the bookings of the same type as this one (including this one)
            sorted: if true, bookings will be sorted by id
        """
        return self._conf.getCSBookingManager().getBookingList(sorted, self._type)

    def getPlugin(self):
        """ Returns the Plugin object associated to this booking.
        """
        return self._plugin

    def getPluginOptions(self):
        """ Utility method that returns the plugin options for this booking's type of plugin
        """
        return self._plugin.getOptions()

    def getPluginOptionByName(self, optionName):
        """ Utility method that returns a plugin option, given its name, for this booking's type of plugin
        """
        return self.getPluginOptions()[optionName]

    def getStartDate(self):
        """ Returns the start date as an datetime object with timezone information (adjusted to the meeting's timezone)
        """
        return self._startDate

    def getAdjustedStartDate(self, tz=None):
        """ Returns the booking start date, adjusted to a given timezone.
            If no timezone is provided, the event's timezone is used
        """
        if self.getStartDate():
            return getAdjustedDate(self.getStartDate(), self.getConference(), tz)
        else:
            return None

    def getStartDateTimestamp(self):
        if not hasattr(object, "_startDateTimestamp"): #TODO: remove when safe
            self._startDateTimestamp = int(datetimeToUnixTimeInt(self._startDate))
        return self._startDateTimestamp

    def getStartDateAsString(self):
        """ Returns the start date as a string, expressed in the meeting's timezone
        """
        if self._startDate == None:
            return ""
        else:
            return formatDateTime(self.getAdjustedStartDate())

    def setStartDate(self, startDate):
        """ Sets the start date as an datetime object with timezone information (adjusted to the meeting's timezone)
        """
        self._startDate = startDate
        if startDate:
            self._startDateTimestamp = int(datetimeToUnixTimeInt(startDate))
        else:
            self._startDateTimestamp = None

    def setStartDateFromString(self, startDateString):
        """ Sets the start date from a string. It is assumed that the date is expressed in the meeting's timezone
        """
        if startDateString == "":
            self.setStartDate(None)
        else:
            try:
                self.setStartDate(setAdjustedDate(parseDateTime(startDateString), self._conf))
            except ValueError:
                raise CollaborationServiceException("startDate parameter (" + startDateString +" ) is in an incorrect format for booking with id: " + str(self._id))

    def getEndDate(self):
        """ Returns the end date as an datetime object with timezone information (adjusted to the meeting's timezone)
        """
        return self._endDate

    def getAdjustedEndDate(self, tz=None):
        """ Returns the booking end date, adjusted to a given timezone.
            If no timezone is provided, the event's timezone is used
        """
        return getAdjustedDate(self.getEndDate(), self.getConference(), tz)

    def getEndDateTimestamp(self):
        if not hasattr(object, "_endDateTimestamp"): #TODO: remove when safe
            self._endDateTimestamp = int(datetimeToUnixTimeInt(self._endDate))
        return self._endDateTimestamp

    def getEndDateAsString(self):
        """ Returns the start date as a string, expressed in the meeting's timezone
        """
        if self._endDate == None:
            return ""
        else:
            return formatDateTime(self.getAdjustedEndDate())

    def setEndDate(self, endDate):
        """ Sets the start date as an datetime object with timezone information (adjusted to the meeting's timezone)
        """
        self._endDate = endDate
        if endDate:
            self._endDateTimestamp = int(datetimeToUnixTimeInt(endDate))
        else:
            self._endDateTimestamp = None

    def setEndDateFromString(self, endDateString):
        """ Sets the start date from a string. It is assumed that the date is expressed in the meeting's timezone
        """
        if endDateString == "":
            self.setEndDate(None)
        else:
            try:
                self.setEndDate(setAdjustedDate(parseDateTime(endDateString), self._conf))
            except ValueError:
                raise CollaborationServiceException("endDate parameter (" + endDateString +" ) is in an incorrect format for booking with id: " + str(self._id))

    def getStatusMessage(self):
        """ Returns the status message as a string.
            This attribute will be available in Javascript with the "statusMessage"
        """
        return self._statusMessage

    def getStatusClass(self):
        """ Returns the status message CSS class as a string.
            This attribute will be available in Javascript with the "statusClass"
        """
        if not hasattr(self, "_statusClass"): #TODO: remove when safe
            self._statusClass = ""
        return self._statusClass

    def accept(self):
        """ Sets this booking as accepted
        """
        self._acceptRejectStatus = True
        self._accept()

    def reject(self, reason):
        """ Sets this booking as rejected, and stores the reason
        """
        self._acceptRejectStatus = False
        self._rejectReason = reason
        self._reject()

    def clearAcceptRejectStatus(self):
        """ Sets back the accept / reject status to None
        """
        self._acceptRejectStatus = None

    def getAcceptRejectStatus(self):
        """ Returns the Accept/Reject status of the booking
            This attribute will be available in Javascript with the "acceptRejectStatus"
            Its value will be:
            -None if the booking has not been accepted or rejected yet,
            -True if it has been accepted,
            -False if it has been rejected
        """
        if not hasattr(self, "_acceptRejectStatus"):
            self._acceptRejectStatus = None
        return self._acceptRejectStatus

    def getRejectReason(self):
        """ Returns the rejection reason.
            This attribute will be available in Javascript with the "rejectReason"
        """
        if not hasattr(self, "_rejectReason"):
            self._rejectReason = ""
        return self._rejectReason

    def getBookingParams(self):
        """ Returns a dictionary with the booking params.
            This attribute will be available in Javascript with the "bookingParams"

            If self._bookingParams has not been set by the implementing class, an exception is thrown.

            Support for "complex" parameters, that are not defined in the self._bookingParams dict, but can
            be retrieved through getter methods.
            If a subclass defines a class attributes called _complexParameters (a list of strings),
            parameter names that are in  this list will also be included in the returned dictionary.
            Their value will be retrieved by calling the corresponding getXXX methods
            but instead the inheriting class's setXXX method will be called.
            Example: _complexParameters = ["communityName", "accessPassword", "hasAccessPassword"] correspond
            to the methods getCommunityName, getAccessPassword, getHasAccessPassword.
            If you include a parameter in the _complexParameters list, you always have to implement the corresponding getter method.
        """
        bookingParams = {}
        for k, v in self.__class__._simpleParameters.iteritems():
            if k in self._bookingParams:
                value = self._bookingParams[k]
            else:
                value = v[1] #we use the default value
            if v[0] is bool and value is True: #we assume it will be used in a single checkbox
                value = ["yes"]
            if value is not False: #we do not include False, it means the single checkbox is not checked
                bookingParams[k] = value

        if hasattr(self.__class__, "_complexParameters") and len(self.__class__._complexParameters) > 0:
            getterMethods = dict(inspect.getmembers(self, lambda m: inspect.ismethod(m) and m.__name__.startswith('get')))
            for paramName in self.__class__._complexParameters:
                getMethodName = 'get' + paramName[0].upper() + paramName[1:]
                if getMethodName in getterMethods:
                    bookingParams[paramName] = getterMethods[getMethodName]()
                else:
                    raise CollaborationServiceException("Tried to retrieve complex parameter " + str(paramName) + " but the corresponding getter method " + getMethodName + " is not implemented")

        bookingParams["startDate"] = self.getStartDateAsString()
        bookingParams["endDate"] = self.getEndDateAsString()
        if self.needsToBeNotifiedOfDateChanges():
            bookingParams["notifyOnDateChanges"] = ["yes"]
        if self.isHidden():
            bookingParams["hidden"] = ["yes"]

        return bookingParams


    def getBookingParamByName(self, paramName):
        if paramName in self.__class__._simpleParameters:
            if not paramName in self._bookingParams:
                self._bookingParams[paramName] = self.__class__._simpleParameters[paramName][1]
            return self._bookingParams[paramName]
        elif hasattr(self.__class__, "_complexParameters") and paramName in self.__class__._complexParameters:
            getterMethods = dict(inspect.getmembers(self, lambda m: inspect.ismethod(m) and m.__name__.startswith('get')))
            getMethodName = 'get' + paramName[0].upper() + paramName[1:]
            if getMethodName in getterMethods:
                return getterMethods[getMethodName]()
            else:
                raise CollaborationServiceException("Tried to retrieve complex parameter " + str(paramName) + " but the corresponding getter method " + getMethodName + " is not implemented")
        else:
            raise CollaborationServiceException("Tried to retrieve parameter " + str(paramName) + " but this parameter does not exist")


    def setBookingParams(self, params):
        """ Sets new booking parameters.
            params: a dict with key/value pairs with the new values for the booking parameters.
            If the plugin's _needsBookingParamsCheck is True, the _checkBookingParams() method will be called.
            This function will return False if all the checks were OK or if there were no checks, and otherwise will throw
            an exception or return a CSReturnedErrorBase error.

            Support for "complex" parameters, that are not defined in the self._bookingParams dict, but can
            be set through setter methods.
            If a subclass defines a class attributes called _complexParameters (a list of strings),
            parameter names that are in 'params' and also in this list will not be assigned directly,
            but instead the inheriting class's setXXX method will be called.

            Example: _complexParameters = ["communityName", "accessPassword", "hasAccessPassword"] corresponds
            to methods setCommunityName, setAccessPassword, setHasAccessPassword.
            Note: even if a parameter is in this list, you can decide not to implement its corresponding set
            method if you never expect the parameter name to come up inside 'params'.
        """

        sanitizeResult = self.sanitizeParams(params)
        if sanitizeResult:
            return sanitizeResult

        self.setHidden(params.pop("hidden", False) == ["yes"])
        self.setNeedsToBeNotifiedOfDateChanges(params.pop("notifyOnDateChanges", False) == ["yes"])

        startDate = params.pop("startDate", None)
        if startDate is not None:
            self.setStartDateFromString(startDate)
        endDate = params.pop("endDate", None)
        if endDate is not None:
            self.setEndDateFromString(endDate)

        for k,v in params.iteritems():
            if k in self.__class__._simpleParameters:
                if self.__class__._simpleParameters[k][0]:
                    try:
                        v = self.__class__._simpleParameters[k][0](v)
                    except ValueError:
                        raise CollaborationServiceException("Tried to set value of parameter with name " + str(k) + ", recognized as a simple parameter of type" + str(self._simpleParameters[k]) + ", but the conversion failed")
                self._bookingParams[k] = v
            elif k in self.__class__._complexParameters:
                setterMethods = dict(inspect.getmembers(self, lambda m: inspect.ismethod(m) and m.__name__.startswith('set')))
                setMethodName = 'set' + k[0].upper() + k[1:]
                if setMethodName in setterMethods:
                    setterMethods[setMethodName](v)
                else:
                    raise CollaborationServiceException("Tried to set value of parameter with name " + str(k) + ", recognized as a complex parameter, but the corresponding setter method " + setMethodName + " is not implemented")
            else:
                raise CollaborationServiceException("Tried to set the value of a parameter with name " + str(k) + " that was not declared")

        for k, v in self.__class__._simpleParameters.iteritems():
            if not k in self._bookingParams:
                self._bookingParams[k] = self.__class__._simpleParameters[k][1]

        if self.needsBookingParamsCheck():
            return self._checkBookingParams()

        return False

    def sanitizeParams(self, params):
        """ Checks if the fields introduced into the booking / request form
            have any kind of HTML or script tag.
        """
        if not isinstance(params, dict):
            raise CollaborationServiceException("Booking parameters are not a dictionary")

        invalidFields = []
        for k, v in params.iteritems():
            if type(v) == str and hasTags(v):
                invalidFields.append(k)

        if invalidFields:
            return CSSanitizationError(invalidFields)
        else:
            return None

    def _getTypeDisplayName(self):
        return CollaborationTools.getXMLGenerator(self._type).getDisplayName()

    def _getFirstLineInfo(self, tz):
        return CollaborationTools.getXMLGenerator(self._type).getFirstLineInfo(self, tz)

    def _getTitle(self):
        if self.hasEventDisplay():
            raise CollaborationException("Method _getTitle was not overriden for the plugin type " + str(self._type))

    def _getInformationDisplay(self, tz):
        templateClass = CollaborationTools.getTemplateClass(self.getType(), "WInformationDisplay")
        if templateClass:
            return templateClass(self, tz).getHTML()
        else:
            return None

    def _getLaunchDisplayInfo(self):
        """ To be overloaded by plugins
        """
        return None

    def _checkBookingParams(self):
        """ To be overriden by inheriting classes.
            Verifies that the booking parameters are correct. For example, that a numeric field is actually a number.
            Otherwise, an exception should be thrown.
            If there are no errors, the method should just return.
        """
        if self.needsBookingParamsCheck():
            raise CollaborationServiceException("Method _checkBookingParams was not overriden for the plugin type " + str(self._type))

    def hasStart(self):
        """ Returns if this booking belongs to a plugin who has a "start" concept.
            This attribute will be available in Javascript with the "hasStart" attribute
        """
        return self._hasStart

    def hasStartStopAll(self):
        """ Returns if this booking belongs to a plugin who has a "start" concept, and all of its bookings for a conference
            can be started simultanously.
            This attribute will be available in Javascript with the "hasStart" attribute
        """
        return self._hasStartStopAll

    def hasStop(self):
        """ Returns if this booking belongs to a plugin who has a "stop" concept.
            This attribute will be available in Javascript with the "hasStop" attribute
        """
        return self._hasStop

    def hasCheckStatus(self):
        """ Returns if this booking belongs to a plugin who has a "check status" concept.
            This attribute will be available in Javascript with the "hasCheckStatus" attribute
        """
        return self._hasCheckStatus

    def hasAcceptReject(self):
        """ Returns if this booking belongs to a plugin who has a "accept or reject" concept.
            This attribute will be available in Javascript with the "hasAcceptReject" attribute
        """
        return self._hasAcceptReject

    def requiresServerCallForStart(self):
        """ Returns if this booking belongs to a plugin who requires a server call when the start button is pressed.
            This attribute will be available in Javascript with the "requiresServerCallForStart" attribute
        """
        return self._requiresServerCallForStart

    def requiresServerCallForStop(self):
        """ Returns if this booking belongs to a plugin who requires a server call when the stop button is pressed.
            This attribute will be available in Javascript with the "requiresServerCallForStop" attribute
        """
        return self._requiresServerCallForStop

    def requiresClientCallForStart(self):
        """ Returns if this booking belongs to a plugin who requires a client call when the start button is pressed.
            This attribute will be available in Javascript with the "requiresClientCallForStart" attribute
        """
        return self._requiresClientCallForStart

    def requiresClientCallForStop(self):
        """ Returns if this booking belongs to a plugin who requires a client call when the stop button is pressed.
            This attribute will be available in Javascript with the "requiresClientCallForStop" attribute
        """
        return self._requiresClientCallForStop

    def canBeDeleted(self):
        """ Returns if this booking can be deleted, in the sense that the "Remove" button will be active and able to be pressed.
            This attribute will be available in Javascript with the "canBeDeleted" attribute
        """

        if not hasattr(self, '_canBeDeleted'):
            self._canBeDeleted = True
        return self._canBeDeleted

    def canBeStarted(self):
        """ Returns if this booking can be started, in the sense that the "Start" button will be active and able to be pressed.
            This attribute will be available in Javascript with the "canBeStarted" attribute
        """
        return self._canBeStarted

    def canBeStopped(self):
        """ Returns if this booking can be stopped, in the sense that the "Stop" button will be active and able to be pressed.
            This attribute will be available in Javascript with the "canBeStopped" attribute
        """
        return self._canBeStopped

    def isPermittedToStart(self):
        """ Returns if this booking is allowed to start, in the sense that it will be started after the "Start" button is pressed.
            For example a booking should not be permitted to start before a given time, even if the button is active.
            This attribute will be available in Javascript with the "isPermittedToStart" attribute
        """
        return self._permissionToStart

    def isPermittedToStop(self):
        """ Returns if this booking is allowed to stop, in the sense that it will be started after the "Stop" button is pressed.
            This attribute will be available in Javascript with the "isPermittedToStop" attribute
        """
        return self._permissionToStop

    def needsBookingParamsCheck(self):
        """ Returns if this booking belongs to a plugin that needs to verify the booking parameters.
        """
        return self._needsBookingParamsCheck

    def needsToBeNotifiedOnView(self):
        """ Returns if this booking needs to be notified when someone views it (for example when the list of bookings is returned)
        """
        return self._needsToBeNotifiedOnView

    def canBeNotifiedOfEventDateChanges(self):
        """ Returns if bookings of this type should be able to be notified
            of their owner Event changing start date, end date or timezone.
        """
        return self._canBeNotifiedOfEventDateChanges

    def needsToBeNotifiedOfDateChanges(self):
        """ Returns if this booking in particular needs to be notified
            of their owner Event changing start date, end date or timezone.
        """
        return self._needsToBeNotifiedOfDateChanges

    def setNeedsToBeNotifiedOfDateChanges(self, needsToBeNotifiedOfDateChanges):
        """ Sets if this booking in particular needs to be notified
            of their owner Event changing start date, end date or timezone.
        """
        self._needsToBeNotifiedOfDateChanges = needsToBeNotifiedOfDateChanges

    def isHidden(self):
        """ Return if this booking is "hidden"
            A hidden booking will not appear in display pages
        """
        if not hasattr(self, '_hidden'):
            self._hidden = False
        return self._hidden

    def setHidden(self, hidden):
        """ Sets if this booking is "hidden"
            A hidden booking will not appear in display pages
            hidden: a Boolean
        """
        self._hidden = hidden

    def isAllowMultiple(self):
        """ Returns if this booking belongs to a type that allows multiple bookings per event.
        """
        return self._allowMultiple

    def shouldBeIndexed(self):
        """ Returns if bookings of this type should be indexed
        """
        return self._shouldBeIndexed

    def getCommonIndexes(self):
        """ Returns a list of strings with the names of the
            common (shared) indexes that bookings of this type want to
            be included in.
        """
        return self._commonIndexes

    def getModificationURL(self):
        return urlHandlers.UHConfModifCollaboration.getURL(self.getConference(),
                                                           secure = CollaborationTools.isUsingHTTPS(),
                                                           tab = CollaborationTools.getPluginTab(self.getPlugin()))

    def hasStartDate(self):
        """ Returns if bookings of this type have a start date
            (they may only have creation / modification date)
        """
        return self._hasStartDate

    def hasTitle(self):
        """ Returns if bookings of this type have a title
        """
        return self._hasTitle

    def hasEventDisplay(self):
        """ Returns if the type of this booking should display something on
            an event display page
        """
        return self._hasEventDisplay

    def isAdminOnly(self):
        """ Returns if this booking / this booking's plugin pages should only be displayed
            to Server Admins, Video Service Admins, or the respective plugin admins.
        """
        return self._adminOnly

    def _create(self):
        """ To be overriden by inheriting classes.
            This method is called when a booking is created, after setting the booking parameters.
            The plugin should decide if the booking is accepted or not.
            Often this will involve communication with another entity, like an MCU for the multi-point H.323 plugin,
            or a EVO HTTP server in the EVO case.
        """
        raise CollaborationException("Method _create was not overriden for the plugin type " + str(self._type))

    def _modify(self, oldBookingParams):
        """ To be overriden by inheriting classes.
            This method is called when a booking is modifying, after setting the booking parameters.
            The plugin should decide if the booking is accepted or not.
            Often this will involve communication with another entity, like an MCU for the multi-point H.323 plugin
            or a EVO HTTP server in the EVO case.
            A dictionary with the previous booking params is passed. This dictionary is the one obtained
            by the method self.getBookingParams() before the new params input by the user are applied.
        """
        raise CollaborationException("Method _modify was not overriden for the plugin type " + str(self._type))

    def _start(self):
        """ To be overriden by inheriting classes
            This method is called when the user presses the "Start" button in a plugin who has a "Start" concept
            and whose flag _requiresServerCallForStart is True.
            Often this will involve communication with another entity.
        """
        if self.hasStart():
            raise CollaborationException("Method _start was not overriden for the plugin type " + str(self._type))
        else:
            pass

    def _stop(self):
        """ To be overriden by inheriting classes
            This method is called when the user presses the "Stop" button in a plugin who has a "Stop" concept
            and whose flag _requiresServerCallForStop is True.
            Often this will involve communication with another entity.
        """
        if self.hasStop():
            raise CollaborationException("Method _stop was not overriden for the plugin type " + str(self._type))
        else:
            pass

    def _checkStatus(self):
        """ To be overriden by inheriting classes
            This method is called when the user presses the "Check Status" button in a plugin who has a "check status" concept.
            Often this will involve communication with another entity.
        """
        if self.hasCheckStatus():
            raise CollaborationException("Method _checkStatus was not overriden for the plugin type " + str(self._type))
        else:
            pass

    def _accept(self):
        """ To be overriden by inheriting classes
            This method is called when a user with privileges presses the "Accept" button
            in a plugin who has a "accept or reject" concept.
            Often this will involve communication with another entity.
        """
        if self.hasAcceptReject():
            raise CollaborationException("Method _accept was not overriden for the plugin type " + str(self._type))
        else:
            pass

    def _reject(self):
        """ To be overriden by inheriting classes
            This method is called when a user with privileges presses the "Reject" button
            in a plugin who has a "accept or reject" concept.
            Often this will involve communication with another entity.
        """
        if self.hasAcceptReject():
            raise CollaborationException("Method _reject was not overriden for the plugin type " + str(self._type))
        else:
            pass

    def _notifyOnView(self):
        """ To be overriden by inheriting classes
            This method is called when a user "sees" a booking, for example when the list of bookings is displayed.
            Maybe in this moment the booking wants to update its status.
        """
        if self.needsToBeNotifiedOnView():
            raise CollaborationException("Method _notifyOnView was not overriden for the plugin type " + str(self._type))
        else:
            pass

    def _delete(self):
        """ To be overriden by inheriting classes
            This method is called whent he user removes a booking. Maybe the plugin will need to liberate
            ressources that were allocated to it.
            This method does not unregister the booking from the list of date change observer of the meeting
        """
        raise CollaborationException("Method _delete was not overriden for the plugin type " + str(self._type))


class WCSTemplateBase(wcomponents.WTemplated):
    """ Base class for Collaboration templates.
        It stores the following attributes:
            _conf : the corresponding Conference object.
            _pluginName: the corresponding plugin ("EVO", "DummyPlugin", etc.).
            _XXXOptions: a dictionary whose values are the options of the plugin called pluginName.
                         So, for example, if an EVO template inherits from this class, an attribute self._EVOOptions will be available.
        This class also overloads the _setTPLFile method so that Indico knows where each plugin's *.tpl files are.
    """

    def __init__(self, pluginName):
        """ Constructor for the WCSTemplateBase class.
            conf: a Conference object
            pluginName: a string with the corresponding plugin name ("EVO", "DummyPlugin", etc.)
        """
        self._pluginName = pluginName
        self._ph = PluginsHolder()

        self._plugin = CollaborationTools.getPlugin(pluginName)
        setattr(self, "_" + pluginName + "Options", CollaborationTools.getPlugin(pluginName).getOptions())

    def _setTPLFile(self):
        dir = os.path.join(Collaboration.__path__[0], self._pluginName, "tpls")
        file = "%s.tpl"%self.tplId
        self.tplFile = os.path.join(dir, file)

        hfile = self._getSpecificTPL(os.path.join(dir,self._pluginName,'chelp'), self.tplId,extension='wohl')
        self.helpFile = os.path.join(dir,'chelp',hfile)


class WCSPageTemplateBase(WCSTemplateBase):
    """ Base class for Collaboration templates for the create / modify booking form.
    """

    def __init__(self, conf, pluginName, user):
        WCSTemplateBase.__init__(self, pluginName)
        self._conf = conf
        self._user = user


class WJSBase(WCSTemplateBase):
    """ Base class for Collaboration templates for Javascript code template.
        It overloads _setTPLFile so that indico can find the Main.js, Extra.js and Indexing.js files.
    """
    def __init__(self, conf, pluginName, user):
        WCSTemplateBase.__init__(self, pluginName)
        self._conf = conf
        self._user = user

    def _setTPLFile(self):
        dir = os.path.join(Collaboration.__path__[0], self._pluginName, "tpls")
        file = "%s.js"%self.tplId
        self.tplFile = os.path.join(dir, file)
        self.helpFile = ''

class WCSCSSBase(WCSTemplateBase):
    """ Base class for Collaboration templates for CSS code template
        It overloads _setTPLFile so that indico can find the style.css files.
    """

    def _setTPLFile(self):
        dir = os.path.join(Collaboration.__path__[0], self._pluginName)
        file = "%s.css"%self.tplId
        self.tplFile = os.path.join(dir, file)
        self.helpFile = ''

class CSErrorBase(Fossilizable):
    fossilizes(ICSErrorBaseFossil)

    """ When _create, _modify or _remove want to return an error,
        they should return an error that inherits from this class
    """

    def getUserMessage(self):
        """ To be overloaded.
            Returns the string that will be shown to the user when this error will happen.
        """
        raise CollaborationException("Method getUserMessage was not overriden for the a CSErrorBase object of class " + self.__class__.__name__)

    def getLogMessage(self):
        """ To be overloaded.
            Returns the string that will be printed in Indico's log when this error will happen.
        """
        raise CollaborationException("Method getLogMessage was not overriden for the a CSErrorBase object of class " + self.__class__.__name__)

class CSSanitizationError(CSErrorBase): #already Fossilizable
    fossilizes(ICSSanitizationErrorFossil)

    """ Class used to return which fields have a sanitization error (invalid html / script tags)
    """

    def __init__(self, invalidFields):
        self._invalidFields = invalidFields

    def invalidFields(self):
        return self._invalidFields


class CollaborationException(MaKaCError):
    """ Error for the Collaboration System "core". Each plugin should declare their own EVOError, etc.
    """
    def __init__(self, msg, area = 'Collaboration', inner = None):
        MaKaCError.__init__(self, msg, area)
        self._inner = inner

    def getInner(self):
        return self._inner

    def __str__(self):
        return MaKaCError.__str__(self) + '. Inner: ' + str(self._inner)

class CollaborationServiceException(ServiceError):
    """ Error for the Collaboration System "core", for Service calls.
    """
    def __init__(self, message, inner = None):
        ServiceError.__init__(self, "ERR-COLL", message, inner)
