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
from indico.util.contextManager import ContextManager
import time
import pkg_resources
from persistent import Persistent
from hashlib import md5

from MaKaC.common.Counter import Counter
from MaKaC.common.utils import formatDateTime, parseDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate, setAdjustedDate,\
    datetimeToUnixTimeInt
from MaKaC.webinterface import wcomponents
from MaKaC.plugins import PluginsHolder
from MaKaC.errors import MaKaCError, NoReportError
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.logger import Logger
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools,\
    MailTools
from MaKaC.plugins.Collaboration.urlHandlers import UHConfModifCollaboration
from indico.core.index import Catalog
from MaKaC.conference import Observer
from MaKaC.webinterface.common.tools import hasTags
from MaKaC.plugins.Collaboration import mail
from MaKaC.common.mail import GenericMailer
import os, inspect
from indico.modules.scheduler.client import Client
from indico.modules.scheduler.tasks import HTTPTask
from indico.util import json
from indico.util.date_time import now_utc
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
from BTrees.OOBTree import OOBTree

from MaKaC.plugins.Collaboration.fossils import ICSErrorBaseFossil, ICSSanitizationErrorFossil,\
    ICSBookingBaseConfModifFossil, ICSBookingBaseIndexingFossil,\
    ISpeakerWrapperBaseFossil
from MaKaC.conference import Contribution


class CSBookingManager(Persistent, Observer):
    """ Class for managing the bookins of a meeting.
        It will store the list of bookings. Adding / removing / editing bookings should be through this class.
    """

    _shouldBeTitleNotified = True
    _shouldBeDateChangeNotified = True
    _shouldBeLocationChangeNotified = True
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

        # an index of bookings to video services by event.uniqueId : video.uniqueId pairind.
        self._bookingsToVideoServices = OOBTree()

        # a list of ids with hidden bookings
        self._hiddenBookings = set()

        # an index of video services managers for each plugin. key: plugin name, value: list of users
        self._managers = {}

        # list of speaker wrapper for a conference
        self._speakerWrapperList = []
        self.updateSpeakerWrapperList()

        # Send email to managers when Electronic Agreement accepted
        self._notifyElectronicAgreementAnswer = True

    def getOwner(self):
        """ Returns the Conference (the meeting) that owns this CSBookingManager object.
        """
        return self._conf

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

        bookingList = [self._bookings[k] for k in keys if not self._bookings[k].hasSessionOrContributionLink() or self._bookings[k].getLinkObject()]

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
        return self._bookings.get(id,None)

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

    def checkVideoLink(self, bookingParams):

        if bookingParams.get('videoLinkType',"") == "session":
            sessSlotId = bookingParams.get("videoLinkSession","")
            import re
            regExp = re.match(r"""(s[0-9a]*)(l[0-9]*)""", sessSlotId)
            if not regExp:
                raise CollaborationException(_('No session has been passed when the type is session.'))
            sessionId = regExp.group(1)[1:]
            slotId = regExp.group(2)[1:]
            session = self._conf.getSessionById(sessionId)
            if session is None:
                raise CollaborationException(_('The session does not exist.'))
            slot = session.getSlotById(slotId)
            if slot is None:
                raise CollaborationException(_('The session does not exist.'))
            return slot.getUniqueId()

        elif bookingParams.get('videoLinkType',"") == "contribution":
            contId = bookingParams.get("videoLinkContribution","")
            if contId == "":
                raise CollaborationException(_('No contribution has been passed when the type is contribution.'))
            cont = self._conf.getContributionById(contId)
            if cont is None:
                raise CollaborationException(_('The contribution does not exist.'))
            return cont.getUniqueId()

        return self._conf.getUniqueId()

    def addBooking(self, booking):
        """ Adds an existing booking to the list of bookings.

            booking: The existing booking to be added.
        """
        booking.setId( self._getNewBookingId())
        self._bookings[booking.getId()] = booking
        self._bookingsByType.setdefault(booking.getType(),[]).append(booking.getId())
        if booking.isHidden():
            self.getHiddenBookings().add(booking.getId())
        self._indexBooking(booking)

        booking.index_instances()

        self._notifyModification()

        # the unique id can be diferent for the new conference
        booking.setLinkType({booking.getLinkType():ContextManager.get('clone.unique_id_map').get(booking.getLinkId(),"")})
        if booking.hasSessionOrContributionLink():
            linkObject = booking.getLinkObject()
            bp=booking.getBookingParams()
            if isinstance(linkObject, Contribution):
                bp["videoLinkContribution"] = linkObject.getId()
            else: #session
                bp["videoLinkSession"] = linkObject.getId()
            booking.setBookingParams(bp)

        self.addVideoService(booking.getLinkId(), booking)


    def _createBooking(self, bookingType, bookingParams = {}, operation = "_create"):
        if self.canCreateBooking(bookingType):

            uniqueId = self.checkVideoLink(bookingParams)

            if (self.hasVideoService(uniqueId) and bookingParams.has_key("videoLinkType") and bookingParams.get("videoLinkType","") != "event"): # Restriction: 1 video service per session or contribution.
                raise NoReportError(_('Only one video service per contribution or session is allowed.'))

            newBooking = CollaborationTools.getCSBookingClass(bookingType)(bookingType, self._conf)
            if bookingParams.has_key("videoLinkType"):
                newBooking.setLinkType({bookingParams["videoLinkType"] : uniqueId})

            error = newBooking.setBookingParams(bookingParams)

            if isinstance(error, CSErrorBase):
                return error
            elif error:
                raise CollaborationServiceException("Problem while creating a booking of type " + bookingType)
            else:
                newId = self._getNewBookingId()
                newBooking.setId(newId)
                createResult = getattr(newBooking, operation)()
                if isinstance(createResult, CSErrorBase):
                    return createResult
                else:
                    self._bookings[newId] = newBooking
                    self._bookingsByType.setdefault(bookingType,[]).append(newId)
                    if newBooking.isHidden():
                        self.getHiddenBookings().add(newId)

                    newBooking.index_instances()

                    self._indexBooking(newBooking)
                    self._notifyModification()

                    if uniqueId is not None: # if we're here and uniqueId has a value, register the video service.
                        self.addVideoService(uniqueId, newBooking)

                    if MailTools.needToSendEmails(bookingType):
                        newBooking._sendNotifications('new')

                    return newBooking
        else:
            #we raise an exception because the web interface should take care of this never actually happening
            raise CollaborationServiceException(bookingType + " only allows to create 1 booking per event")

    def createBooking(self, bookingType, bookingParams = {}):
        """ Adds a new booking to the list of bookings.
            The id of the new booking is auto-generated incrementally.
            After generating the booking, its "performBooking" method will be called.

            bookingType: a String with the booking's plugin. Example: "DummyPlugin", "EVO"
            bookingParams: a dictionary with the parameters necessary to create the booking.
                           "create the booking" usually means Indico deciding if the booking can take place.
                           if "startDate" and "endDate" are among the keys, they will be taken out of the dictionary.
        """
        return self._createBooking(bookingType, bookingParams)

    def attachBooking(self, bookingType, bookingParams = {}):
        """ Attach an existing booking to the list of bookings.
             The checking and the params are the same as create the booking
        """
        for booking in self.getBookingList(sorted, bookingType):
            result = booking.checkAttachParams(bookingParams)
            if isinstance(result, CSErrorBase):
                return result
        return self._createBooking(bookingType, bookingParams, "_attach")

    def searchBookings(self, bookingType, user, query, offset=0, limit=None):
        """ Adds a new booking to the list of bookings.
            The id of the new booking is auto-generated incrementally.
            After generating the booking, its "performBooking" method will be called.

            bookingType: a String with the booking's plugin. Example: "DummyPlugin", "EVO"
            bookingParams: a dictionary with the parameters necessary to create the booking.
                           "create the booking" usually means Indico deciding if the booking can take place.
                           if "startDate" and "endDate" are among the keys, they will be taken out of the dictionary.
        """
        if CollaborationTools.hasOption(bookingType, "searchAllow") \
                and CollaborationTools.getOptionValue(bookingType, "searchAllow"):
            res = CollaborationTools.getCSBookingClass(bookingType)._search(user, query, offset, limit)
            return {'results': res[0],
                    'offset': res[1]}
        else:
            raise CollaborationException("Plugin type " + str(bookingType) + " does not allow search.")

    def _indexBooking(self, booking, index_names=None):
        indexes = self._getIndexList(booking)
        if index_names is not None:
            ci = IndexesHolder().getById('collaboration')
            all_indexes = list(ci.getIndex(index) for index in index_names)
            indexes = list(index for index in all_indexes if index in indexes)

        if booking.shouldBeIndexed():
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

        booking.unindex_instances()

        error = booking.setBookingParams(bookingParams)
        if isinstance(error, CSSanitizationError):
            return error
        elif error:
            CSBookingManager._rollbackChanges(booking, oldBookingParams, oldModificationDate)
            if isinstance(error, CSErrorBase):
                return error
            raise CollaborationServiceException("Problem while modifying a booking of type " + booking.getType())
        else:
            modifyResult = booking._modify(oldBookingParams)
            if isinstance(modifyResult, CSErrorBase):
                CSBookingManager._rollbackChanges(booking, oldBookingParams, oldModificationDate)
                return modifyResult
            else:
                modificationDate = now_utc()
                booking.setModificationDate(modificationDate)

                if booking.isHidden():
                    self.getHiddenBookings().add(booking.getId())
                elif booking.getId() in self.getHiddenBookings():
                    self.getHiddenBookings().remove(booking.getId())

                eventLinkUpdated = False
                newLinkId = self.checkVideoLink(bookingParams)

                if bookingParams.has_key("videoLinkType"):
                    oldLinkData = booking.getLinkIdDict()
                    oldLinkId = oldLinkData.values()[0]

                    # Details changed, we need to remove the association and re-create it
                    if not (oldLinkData.has_key(bookingParams.get('videoLinkType','')) and oldLinkId == newLinkId):
                        self.removeVideoSingleService(booking.getLinkId(), booking)
                        eventLinkUpdated = True

                if eventLinkUpdated or (bookingParams.has_key("videoLinkType") and bookingParams.get("videoLinkType","") != "event"):
                    if self.hasVideoService(newLinkId, booking):
                        pass # No change in the event linking
                    elif newLinkId is not None:
                        if (self.hasVideoService(newLinkId) and bookingParams.has_key("videoLinkType") and bookingParams.get("videoLinkType","") != "event"): # Restriction: 1 video service per session or contribution.
                            raise NoReportError(_('Only one video service per contribution or session is allowed.'))
                        else:
                            self.addVideoService(newLinkId, booking)
                            if bookingParams.has_key("videoLinkType"):
                                booking.setLinkType({bookingParams['videoLinkType']: newLinkId})
                    else: # If it's still None, event linking has been completely removed.
                        booking.resetLinkParams()

                self._changeStartDateInIndex(booking, oldStartDate, booking.getStartDate())
                self._changeModificationDateInIndex(booking, oldModificationDate, modificationDate)
                booking.index_instances()

                if booking.hasAcceptReject():
                    if booking.getAcceptRejectStatus() is not None:
                        booking.clearAcceptRejectStatus()
                        self._addToPendingIndex(booking)

                self._notifyModification()

                if MailTools.needToSendEmails(booking.getType()):
                    booking._sendNotifications('modify')

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
        if booking.shouldBeIndexed() and oldConfStartDate is not None and newConfStartDate is not None:
            indexes = self._getIndexList(booking)
            for index in indexes:
                index.changeConfStartDate(booking, oldConfStartDate, newConfStartDate)

    def removeBooking(self, id):
        """ Removes a booking given its id.
        """
        booking = self.getBooking(id)
        bookingType = booking.getType()
        bookingLinkId = booking.getLinkId()

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

            # If there is an association to a session or contribution, remove it
            if bookingLinkId is not None:
                self.removeVideoSingleService(bookingLinkId, booking)

            booking.unindex_instances()

            self._unindexBooking(booking)

            self._notifyModification()

            if MailTools.needToSendEmails(booking.getType()):
                booking._sendNotifications('remove')

            return booking

    def _unindexBooking(self, booking):
        if booking.shouldBeIndexed() and not booking.keepForever():
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
            result = booking._checkStatus()
            if isinstance(result, CSErrorBase):
                return result
            else:
                return booking
        else:
            raise ServiceError(message=_("Tried to check status of booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking does not support the check status service."))

    def acceptBooking(self, id, user = None):
        booking = self._bookings[id]
        if booking.hasAcceptReject():
            if booking.getAcceptRejectStatus() is None:
                self._removeFromPendingIndex(booking)
            booking.accept(user)
            return booking
        else:
            raise ServiceError(message=_("Tried to accept booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking cannot be accepted."))

    def rejectBooking(self, id, reason):
        booking = self._bookings[id]
        if booking.hasAcceptReject():
            if booking.getAcceptRejectStatus() is None:
                self._removeFromPendingIndex(booking)
            booking.reject(reason)
            return booking
        else:
            raise ServiceError("ERR-COLL10", _("Tried to reject booking ") + str(id) + _(" of meeting ") + str(self._conf.getId()) + _(" but this booking cannot be rejected."))

    def makeMeModeratorBooking(self, id, user):
        booking = self._bookings[id]
        bookingParams = booking.getBookingParams()
        bookingParams["owner"] = user
        return self.changeBooking(id,bookingParams)

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
                Logger.get('VideoServ').exception("Exception while reindexing a booking in the event title index because its event's title changed: " + str(e))

    def notifyInfoChange(self):
        self.updateSpeakerWrapperList()

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

                # booking "instances" provide higher granularity in search
                booking.unindex_instances()
                booking.index_instances()

                if startDateChanged:
                    try:
                        self._changeConfStartDateInIndex(booking, oldStartDate, newStartDate)
                    except Exception, e:
                        Logger.get('VideoServ').error("Exception while reindexing a booking in the event start date index because its event's start date changed: " + str(e))

                if booking.hasStartDate():
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

                if hasattr(booking, "notifyEventDateChanges"):
                    try:
                        booking.notifyEventDateChanges(oldStartDate, newStartDate, oldEndDate, newEndDate)
                    except Exception, e:
                        Logger.get('VideoServ').exception("Exception while notifying a plugin of an event date changed: " + str(e))

            if problems:
                ContextManager.get('dateChangeNotificationProblems')['Collaboration'] = [
                    'Some Video Services bookings could not be moved:',
                    problems,
                    'Go to [[' + str(UHConfModifCollaboration.getURL(self.getOwner(), secure = ContextManager.get('currentRH').use_https())) + ' the Video Services section]] to modify them yourself.'
                ]


    def notifyTimezoneChange(self, oldTimezone, newTimezone):
        """ Notifies the CSBookingManager that the timezone of the event it's attached to has changed.
            The CSBookingManager will change the dates of all the bookings that want to be updated.
            This method will be called by the event (Conference) object
        """
        return []

    def notifyLocationChange(self):
        for booking in self.getBookingList():
            if hasattr(booking, "notifyLocationChange"):
                try:
                    booking.notifyLocationChange()
                except Exception, e:
                    Logger.get('VideoServ').exception("Exception while notifying a plugin of a location change: " + str(e))

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
                # We will delete the bookings connected to the event, not Contribution or
                if booking.getLinkType() and booking.getLinkType() != "event":
                    continue
                removeResult = booking._delete()
                if isinstance(removeResult, CSErrorBase):
                    Logger.get('VideoServ').warning("Error while deleting a booking of type %s after deleting an event: %s"%(booking.getType(), removeResult.getLogMessage() ))
                booking.unindex_instances()
                self._unindexBooking(booking)
            except Exception, e:
                Logger.get('VideoServ').exception("Exception while deleting a booking of type %s after deleting an event: %s" % (booking.getType(), str(e)))

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

    def getSortedContributionSpeaker(self, exclusive):
        ''' This method will create a dictionary by sorting the contribution/speakers
            that they are in recording, webcast or in both.
            bool: exclusive - if True, every dicts (recording, webcast, both) will
                                have different speaker list (no repetition allowed)
                                if an element is present in 'both', it will be deleted from
                                'recording and 'webcast'

            returns d = { 'recording': {}, 'webcast' : {}, 'both': {} }
        '''

        d = {}

        recordingBooking = self.getSingleBooking("RecordingRequest")
        webcastBooking = self.getSingleBooking("WebcastRequest")

        d["recording"] = recordingBooking.getContributionSpeakerSingleBooking() if recordingBooking else {}
        d["webcast"] = webcastBooking.getContributionSpeakerSingleBooking() if webcastBooking else {}

        contributions = {}
        ''' Look for speaker intersections between 'recording' and 'webcast' dicts
            and put them in 'both' dict. Additionally, if any intersection has been found,
            we exclude them from the original dictionary.
        '''
        for cont in d["recording"].copy():
            if cont in d["webcast"].copy():
                # Check if same contribution/speaker in 'recording' and 'webcast'
                intersection = set(d['recording'][cont]) & set(d['webcast'][cont])
                if intersection:
                    contributions[cont] = list(intersection)

                    # if exclusive is True, and as we found same contribution/speaker,
                    # we delete them from 'recording' and 'webcast' dicts
                    if exclusive:
                        exclusion = set(d['recording'][cont]) ^ set(contributions[cont])
                        if not exclusion:
                            del d["recording"][cont]
                        else:
                            d["recording"][cont] = list(exclusion)

                        exclusion = set(d['webcast'][cont]) ^ set(contributions[cont])
                        if not exclusion:
                            del d["webcast"][cont]
                        else:
                            d["webcast"][cont] = list(exclusion)

        d["both"] = contributions

        return d

    def getContributionSpeakerByType(self, requestType):
        ''' Return a plain dict of contribution/speaker according to the requestType
            if the request type is 'both', we need to merge the lists
        '''
        d = self.getSortedContributionSpeaker(False) # We want non exclusive dict

        if requestType == "recording":
            return d['recording']
        elif requestType == "webcast":
            return d['webcast']
        elif requestType == "both":
            # We merge 'recording' and 'webcast'
            m = dict(((cont, list(set(spks) | \
                set(d['webcast'].get(cont, [])))) for cont, spks in d['recording'].iteritems()))
            m.update(dict((cont, spks) for cont, spks in d['webcast'].iteritems() if cont not in m))

            return m
        else:
            return {}

    def updateSpeakerWrapperList(self, newList = False):
        """
        if newList arg is True, don't check if there is an existing speakerWrapperList
        and create a new one straight forward. (Done to avoid loops)
        """
        SWList = []
        contributions = self.getSortedContributionSpeaker(True)
        requestType = ['recording', 'webcast', 'both']

        for type in requestType:
            for cont in contributions[type]:
                for spk in contributions[type][cont]:
                    if newList:
                        sw = None
                    else:
                        sw = self.getSpeakerWrapperByUniqueId("%s.%s"%(cont, spk.getId()))

                    if sw:
                        if not sw.getObject().getEmail():
                            if sw.getStatus() not in [SpeakerStatusEnum.SIGNED,
                                                      SpeakerStatusEnum.FROMFILE,
                                                      SpeakerStatusEnum.REFUSED]:
                                sw.setStatus(SpeakerStatusEnum.NOEMAIL)
                        elif sw.getStatus() == SpeakerStatusEnum.NOEMAIL:
                            sw.setStatus(SpeakerStatusEnum.NOTSIGNED)
                        sw.setRequestType(type)
                        SWList.append(sw)
                    else:
                        newSw = SpeakerWrapper(spk, cont, type)
                        if not newSw.getObject().getEmail():
                            newSw.setStatus(SpeakerStatusEnum.NOEMAIL)
                        SWList.append(newSw)

        self._speakerWrapperList = SWList

    def getSpeakerWrapperList(self):
        if not hasattr(self, "_speakerWrapperList"):#TODO: remove when safe
            self.updateSpeakerWrapperList(True)

        return self._speakerWrapperList

    def getSpeakerWrapperByUniqueId(self, id):

        if not hasattr(self, "_speakerWrapperList"):#TODO: remove when safe
            self.updateSpeakerWrapperList(True)

        for spkWrap in self._speakerWrapperList:
            if spkWrap.getUniqueId() == id:
                return spkWrap

        return None

    def areSignatureCompleted(self):
        value = True;
        for spkWrap in self._speakerWrapperList:
            if spkWrap.getStatus() != SpeakerStatusEnum.FROMFILE and \
                spkWrap.getStatus() != SpeakerStatusEnum.SIGNED:
                value = False;

        return value

    def getSpeakerWrapperListByStatus(self, status):
        '''Return a list of SpeakerWrapper matching the status.
        '''
        list = []
        for spkWrap in self._speakerWrapperList:
            if spkWrap.getStatus() == status:
                list.append(spkWrap)

        return list

    def getSpeakerEmailByUniqueId(self, id, user):
        ''' Return the email of a speaker according to the uniqueId.
            id: uniqueId of the speaker wrapper.
            user: user object of the sender of the emails, in order to check the rights.
        '''

        canManageRequest = CollaborationTools.getRequestTypeUserCanManage(self._conf, user)
        requestTypeAccepted = ""

        if canManageRequest == "recording":
            requestTypeAccepted = ["recording"]
        elif canManageRequest == "webcast":
            requestTypeAccepted = ["webcast"]
        elif canManageRequest == "both":
            requestTypeAccepted = ["recording", "webcast", "both"]

        list = []
        for spkWrap in self._speakerWrapperList:
            if spkWrap.getUniqueId() == id and \
                   spkWrap.hasEmail() and spkWrap.getStatus() not in \
                   [SpeakerStatusEnum.SIGNED, SpeakerStatusEnum.FROMFILE] and \
                   spkWrap.getRequestType() in requestTypeAccepted:

                list.append(spkWrap.getObject().getEmail())

        return list

    def addVideoService(self, uniqueId, videoService):
        """ Adds a video service to Contribution / Session link in the tracking
            dictionary in order {uniqueId : videoService}
        """
        if self.getVideoServices().has_key(uniqueId):
            self.getVideoServices()[uniqueId].append(videoService)
        else:
            self.getVideoServices()[uniqueId] = [videoService]

    def removeVideoAllServices(self, uniqueId):
        """ Removes all associations of Contributions / Sessions with video
            services from the dictionary, key included.
        """

        if not self.hasVideoService(uniqueId):
            return None

        del self.getVideoServices()[uniqueId]

    def removeVideoSingleService(self, uniqueId, videoService):
        """ Removes a specific video service from a specific contribution. As
            the list of services is unordered, iterate through to match for
            removal - performance cost therefore occurs here.
        """

        if not self.hasVideoService(uniqueId):
            return None

        target = self.getVideoServicesById(uniqueId)

        for service in target:
            if service == videoService:
                target.remove(service)
                break

        # There are no more entries, therefore remove the dictionary entry too.
        if len(target) == 0:
            self.removeVideoAllServices(uniqueId)

    def getVideoServices(self):
        """ Returns the OOBTree associating event unique IDs with the List
            of video services associated.
        """

        if not hasattr(self, "_bookingsToVideoServices"):
            self._bookingsToVideoServices = OOBTree()

        return self._bookingsToVideoServices

    def getVideoServicesById(self, uniqueId):
        """ Returns a list of video services associated with the uniqueId
            for printing in event timetable. Returns None if no video services
            are found.
        """

        if not self.hasVideoService(uniqueId):
            return None

        return self.getVideoServices()[uniqueId]

    def hasVideoService(self, uniqueId, service=None):
        """ Returns True if the uniqueId of the Contribution or Session provided
            has an entry in the self._bookingsToVideoServices dictionary, thusly
            denoting the presence of linked bookings. Second parameter is for more
            specific matching, i.e. returns True if unique ID is associated with
            specific service.
        """
        if service is None:
            return self.getVideoServices().has_key(uniqueId)

        if self.getVideoServices().has_key(uniqueId):
            for serv in self.getVideoServicesById(uniqueId):
                if serv == service:
                    return True
        else:
            return self.getVideoServices().has_key(uniqueId)

    def isAnyRequestAccepted(self):
        '''
            Return true if at least one between recording and webcast request
            has been accepted.
        '''
        value = False
        rr = self.getSingleBooking("RecordingRequest")
        wr = self.getSingleBooking("WebcastRequest")

        if rr:
            value = rr.getAcceptRejectStatus()

        if wr:
            value = value or wr.getAcceptRejectStatus()

        return value

    def isContributionReadyToBePublished(self, contId):
        if not hasattr(self, "_speakerWrapperList"):#TODO: remove when safe
            self.updateSpeakerWrapperList(True)

        exists = False
        for spkWrap in self._speakerWrapperList:
            if spkWrap.getContId() == contId:
                exists = True
                if spkWrap.getStatus() != SpeakerStatusEnum.SIGNED and \
                    spkWrap.getStatus() != SpeakerStatusEnum.FROMFILE:
                    return False

        #The list has to have at least one spkWrap with the given contId
        return exists

    def notifyElectronicAgreementAnswer(self):
        if not hasattr(self, "_notifyElectronicAgreementAnswer"):
            self._notifyElectronicAgreementAnswer = True
        return self._notifyElectronicAgreementAnswer

    def setNotifyElectronicAgreementAnswer(self, notifyElectronicAgreementAnswer):
        self._notifyElectronicAgreementAnswer = notifyElectronicAgreementAnswer



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
            _hasConnect : True if the plugin has a "connect" concept. Otherwise, the "connect" button will not appear, etc.
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
            _keepForever: True if this booking has to be in the Video Services Overview indexes forever
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
    _complexParameters = []
    _linkVideoType = None
    _linkVideoId = None
    _keepForever = False

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
            -_warning: A warning is a plugin-defined object, with information to show to the user when
                       the operation went well but we still have to show some info to the user.
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
        self._acceptRejectStatus = None #None = not yet accepted / rejected; True = accepted; False = rejected
        self._rejectReason = ""
        self._bookingParams = {}
        self._canBeDeleted = True
        self._permissionToStart = False
        self._permissionToStop = False
        self._needsToBeNotifiedOfDateChanges = self._canBeNotifiedOfEventDateChanges
        self._hidden = False
        self._play_status = None

        setattr(self, "_" + bookingType + "Options", CollaborationTools.getPlugin(bookingType).getOptions())
        #NOTE:  Should maybe notify the creation of a new booking, specially if it's a single booking
        #       like that can update requestType of the speaker wrapper...

    def getId(self):
        """ Returns the internal, per-conference id of the booking.
            This attribute will be available in Javascript with the "id" identifier.
        """
        return self._id

    def setId(self, id):
        """ Sets the internal, per-conference id of the booking
        """
        self._id = id

    def getUniqueId(self):
        """ Returns an unique Id that identifies this booking server-wide.
            Useful for ExternalOperationsManager
        """
        return "%scsbook%s" % (self.getConference().getUniqueId(), self.getId())

    def getType(self):
        """ Returns the type of the booking, as a string: "EVO", "DummyPlugin"
            This attribute will be available in Javascript with the "type" identifier.
        """
        return self._type

    def getConference(self):
        """ Returns the owner of this CSBookingBase object, which is a Conference object representing the meeting.
        """
        return self._conf

    def setConference(self, conf):
        """ Sets the owner of this CSBookingBase object, which is a Conference object representing the meeting.
        """
        self._conf = conf

    def getWarning(self):
        """ Returns a warning attached to this booking.
            A warning is a plugin-defined object, with information to show to the user when
            the operation went well but we still have to show some info to the user.
            To be overloaded by plugins.
        """
        if not hasattr(self, '_warning'):
            self._warning = None
        return self._warning

    def setWarning(self, warning):
        """ Sets a warning attached to this booking.
            A warning is a plugin-defined object, with information to show to the user when
            the operation went well but we still have to show some info to the user.
            To be overloaded by plugins.
        """
        self._warning = warning

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
        return Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId()).getBookingList(sorted, self._type)

    def getPlugin(self):
        """ Returns the Plugin object associated to this booking.
        """
        return self._plugin

    def setPlugin(self, plugin):
        """ Sets the Plugin object associated to this booking.
        """
        self._plugin = plugin

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

    def setStartDateTimestamp(self, startDateTimestamp):
        self._startDateTimestamp = startDateTimestamp

    def getStartDateAsString(self):
        """ Returns the start date as a string, expressed in the meeting's timezone
        """
        if self.getStartDate() == None:
            return ""
        else:
            return formatDateTime(self.getAdjustedStartDate(), locale='en_US')

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

    def isHappeningNow(self):
        now = nowutc()
        return self.getStartDate() < now and self.getEndDate() > now

    def hasHappened(self):
        now = nowutc()
        return now > self.getEndDate()

    def getAdjustedEndDate(self, tz=None):
        """ Returns the booking end date, adjusted to a given timezone.
            If no timezone is provided, the event's timezone is used
        """
        return getAdjustedDate(self.getEndDate(), self.getConference(), tz)

    def getEndDateTimestamp(self):
        if not hasattr(object, "_endDateTimestamp"): #TODO: remove when safe
            self._endDateTimestamp = int(datetimeToUnixTimeInt(self._endDate))
        return self._endDateTimestamp

    def setEndDateTimestamp(self, endDateTimestamp):
        self._endDateTimestamp = endDateTimestamp

    def getEndDateAsString(self):
        """ Returns the start date as a string, expressed in the meeting's timezone
        """
        if self.getEndDate() == None:
            return ""
        else:
            return formatDateTime(self.getAdjustedEndDate(), locale='en_US')

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
        status = self.getPlayStatus()
        if status == None:
            if self.isHappeningNow():
                return _("Ready to start!")
            elif self.hasHappened():
                return _("Already took place")
            else:
                return _("Booking created")
        elif status:
            return _("Conference started")
        elif not status:
            return _("Conference stopped")

    def getStatusClass(self):
        """ Returns the status message CSS class as a string.
            This attribute will be available in Javascript with the "statusClass"
        """
        if self.getPlayStatus() == None or self.hasHappened():
            return "statusMessageOther"
        else:
            return "statusMessageOK"

    def accept(self, user = None):
        """ Sets this booking as accepted
        """
        self._acceptRejectStatus = True
        self._accept(user)

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

    ## methods relating to the linking of CSBooking objects to Contributions & Sessions

    def hasSessionOrContributionLink(self):
        return (self.isLinkedToContribution() or self.isLinkedToSession())

    def isLinkedToSession(self):
        return (self._linkVideoType == "session")

    def isLinkedToContribution(self):
        return (self._linkVideoType == "contribution")

    def getLinkId(self):
        """ Returns the unique ID of the Contribution or Session which this
            object is associated with, completely agnostic of the link type.
            Returns None if no association (default) found.
        """

        return self._linkVideoId

    def getLinkIdDict(self):
        """ Returns a dictionary of structure linkType (session | contribution)
            : unique ID of referenced object.
            Returns None if no association is found.
        """
        linkId = self.getLinkId()

        if linkId == None:
            return linkId

        return {self._linkVideoType : linkId}

    def getLinkType(self):
        """ Returns a string denoting the link type, that is whether linked
            to a session or contribution.
        """

        return self._linkVideoType

    def setLinkType(self, linkDict):
        """ Accepts a dictionary of linkType: linkId """

        # case of non-linked bookings
        if linkDict is None:
            return

        self._linkVideoType = linkDict.keys()[0]
        self._linkVideoId = linkDict.values()[0]

    def resetLinkParams(self):
        """ Removes all association with a Session or Contribution from this
            CSBooking only.
        """

        self._linkVideoType = self._linkVideoId = None

    def getLocation(self):
        return self._conf.getLocation().getName() if self._conf.getLocation() else ""

    def getRoom(self):
        return self._conf.getRoom().getName() if self._conf.getRoom() else ""

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

    def getContributionSpeakerSingleBooking(self):
        ''' Return a dictionnary with the contributions and their speakers that need to be recorded
            e.g: {contId:[Spk1Object, Spk2Object, Spk3Object], cont2:[Spk1Object]}...
        '''
        request = {}

        recordingTalksChoice = self.getBookingParams()["talks"] #either "all", "choose" or ""
        listTalksToRecord = self.getBookingParams()["talkSelection"]

        if self._conf.getType() == "simple_event":
            request[self._conf.getId()] = []
            for chair in self._conf.getChairList():
                request[self._conf.getId()].append(chair)
        else:
            for cont in self._conf.getContributionList():
                ''' We select the contributions that respect the following conditions:
                    - They have Speakers assigned.
                    - They are scheduled. (to discuss...)
                    - They have been chosen for the recording request.
                '''
                if recordingTalksChoice != "choose" or cont.getId() in listTalksToRecord:
                    if cont.isScheduled():
                        request[cont.getId()] = []
                        for spk in cont.getSpeakerList():
                            request[cont.getId()].append(spk)

        return request

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

    def hasConnect(self):
        """ Returns if this booking belongs to a plugin who has a "connect" concept.
            This attribute will be available in Javascript with the "hasConnect" attribute
        """
        if not hasattr(self, '_hasConnect'):
            self._hasConnect = False
        return self._hasConnect

    def hasDisconnect(self):
        """ Returns if this booking belongs to a plugin who has a "connect" concept.
            This attribute will be available in Javascript with the "hasConnect" attribute
        """
        if not hasattr(self, '_hasDisconnect'):
            self._hasDisconnect = False
        return self._hasDisconnect

    def hasCheckStatus(self):
        """ Returns if this booking belongs to a plugin who has a "check status" concept.
            This attribute will be available in Javascript with the "hasCheckStatus" attribute
        """
        return self._hasCheckStatus

    def isLinkedToEquippedRoom(self):
        return None

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

    def requiresClientCallForConnect(self):
        """ Returns if this booking belongs to a plugin who requires a client call when the connect button is pressed.
            This attribute will be available in Javascript with the "requiresClientCallForConnect" attribute
        """
        if not hasattr(self, '_requiresClientCallForConnect'):
            self._requiresClientCallForConnect = False
        return self._requiresClientCallForConnect

    def requiresClientCallForDisconnect(self):
        """ Returns if this booking belongs to a plugin who requires a client call when the connect button is pressed.
            This attribute will be available in Javascript with the "requiresClientCallForDisconnect" attribute
        """
        if not hasattr(self, '_requiresClientCallForDisconnect'):
            self._requiresClientCallForDisconnect = False
        return self._requiresClientCallForDisconnect

    def canBeDeleted(self):
        """ Returns if this booking can be deleted, in the sense that the "Remove" button will be active and able to be pressed.
            This attribute will be available in Javascript with the "canBeDeleted" attribute
        """

        return self._canBeDeleted

    def setCanBeDeleted(self, canBeDeleted):
        """ Sets if this booking can be deleted, in the sense that the "Remove" button will be active and able to be pressed.
            This attribute will be available in Javascript with the "canBeDeleted" attribute
        """
        self._canBeDeleted = canBeDeleted

    def canBeStarted(self):
        """ Returns if this booking can be started, in the sense that the "Start" button will be active and able to be pressed.
            This attribute will be available in Javascript with the "canBeStarted" attribute
        """
        return self.isHappeningNow()

    def canBeStopped(self):
        """ Returns if this booking can be stopped, in the sense that the "Stop" button will be active and able to be pressed.
            This attribute will be available in Javascript with the "canBeStopped" attribute
        """
        return self.isHappeningNow()

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
        return False

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

    def index_instances(self):
        """
        To be overloaded
        """
        return

    def unindex_instances(self):
        """
        To be overloaded
        """
        return

    def index_talk(self, talk):
        """
        To be overloaded
        """
        return

    def unindex_talk(self, talk):
        """
        To be overloaded
        """
        return

    def getModificationURL(self):
        return UHConfModifCollaboration.getURL(self.getConference(),
                                                           secure = ContextManager.get('currentRH').use_https(),
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

    def keepForever(self):
        """ Returns if this booking has to be in the Video Services Overview indexes forever
        """
        return self._keepForever

    def canBeDisplayed(self):
        """ Returns if this booking can be displayed in the event page.
            By default is True and it will be shown as "Active" but can be overriden
        """
        return True

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

    def _attach(self):
        """ To be overriden by inheriting classes.
            This method is called when a booking is attached, after setting the booking parameters.
            The plugin should decide if the booking is accepted or not.
            Often this will involve communication with another entity, like an MCU for the multi-point H.323 plugin,
            or a EVO HTTP server in the EVO case.
        """
        raise CollaborationException("Method _attach was not overriden for the plugin type " + str(self._type))

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

    def _accept(self, user = None):
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

    def _sendNotifications(self, operation):
        """
        Sends a mail, wrapping it with ExternalOperationsManager
        """
        ExternalOperationsManager.execute(self, "sendMail_" + operation, self._sendMail, operation)

    def _sendMail(self, operation):
        if operation == 'new':
            try:
                notification = mail.NewBookingNotification(self)
                GenericMailer.sendAndLog(notification, self._conf,
                                         self.getPlugin().getName())
            except Exception, e:
                Logger.get('VideoServ').error(
                    """Could not send NewBookingNotification for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self._conf.getId(), str(e)))
                raise

        elif operation == 'modify':
            try:
                notification = mail.BookingModifiedNotification(self)
                GenericMailer.sendAndLog(notification, self._conf,
                                         self.getPlugin().getName())
            except Exception, e:
                Logger.get('VideoServ').error(
                    """Could not send BookingModifiedNotification for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self._conf.getId(), str(e)))
                raise

        elif operation == 'remove':
            try:
                notification = mail.BookingDeletedNotification(self)
                GenericMailer.sendAndLog(notification, self._conf,
                                         self.getPlugin().getName())
            except Exception, e:
                Logger.get('VideoServ').error(
                    """Could not send BookingDeletedNotification for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self._conf.getId(), str(e)))
                raise

    def getPlayStatus(self):
        if not hasattr(self, '_play_status'):
            self._play_status = None
        return self._play_status

    """ Methods relating to the certain plugin architectures whereby talk
        selection is appropriate through the inheriting class' attributes.
    """
    def hasTalkSelection(self):
        """ Some plugin types select individual contributions stored as a list
            of IDs in this parameter, returns param if this instance is one of them.
        """
        return self._bookingParams.has_key('talkSelection')

    def _getTalkSelection(self):
        """ Returns the attribute if it is defined, None on error. """
        if self.hasTalkSelection():
            return self._bookingParams.get('talkSelection')
        return None

    def _hasTalkSelectionContent(self):
        """ If the talkSelection attribute is present and it has a quantity of
            items in its list greater than 0, individual talks have been chosen.
        """
        ts = self._getTalkSelection()

        if ts is None:
            return False

        return len(ts) > 0

    def getTalkSelectionList(self):
        """ Returns the resultant list if it is present and populated. None if
            neither are true.
        """
        if not self._hasTalkSelectionContent():
            return None

        return self._getTalkSelection()

    def _hasTalks(self):
        """ Returns the attribute if it is defined, None on error. """
        return self._bookingParams.has_key('talks')

    def isChooseTalkSelected(self):
        """ Returns if the talks are choosen"""
        if self._hasTalks():
            return self._bookingParams.get('talks') == "choose"
        else:
            return False

    def __cmp__(self, booking):
        return cmp(self.getUniqueId(), booking.getUniqueId()) if booking else 1

    def checkAttachParams(self, bookingParams):
        return None

    def notifyDeletion(self, obj):
        """ To be overriden by inheriting classes
            This method is called when the parent object has been deleted and some actions are needed.
        """
        pass


class WCSTemplateBase(wcomponents.WTemplated):
    """ Base class for Collaboration templates.
        It stores the following attributes:
            _conf : the corresponding Conference object.
            _pluginName: the corresponding plugin ("EVO", "DummyPlugin", etc.).
            _XXXOptions: a dictionary whose values are the options of the plugin called pluginName.
                         So, for example, if an EVO template inherits from this class, an attribute self._EVOOptions will be available.
        This class also overloads the _setTPLFile method so that Indico knows where each plugin's *.tpl files are.
    """

    def __init__(self, pluginId):
        """ Constructor for the WCSTemplateBase class.
            conf: a Conference object
            plugin: the corresponding plugin
        """
        self._plugin = CollaborationTools.getPlugin(pluginId)
        self._pluginId = self._plugin.getId()
        self._ph = PluginsHolder()

        setattr(self, "_" + self._pluginId + "Options", self._plugin.getOptions())

    def _setTPLFile(self, extension='tpl'):
        tplDir = pkg_resources.resource_filename(self._plugin.getModule().__name__, "tpls")

        fname = "%s.%s" % (self.tplId, extension)
        self.tplFile = os.path.join(tplDir, fname)

        hfile = self._getSpecificTPL(os.path.join(tplDir,self._pluginId,'chelp'), self.tplId,extension='wohl')
        self.helpFile = os.path.join(tplDir,'chelp',hfile)


class WCSPageTemplateBase(WCSTemplateBase):
    """ Base class for Collaboration templates for the create / modify booking form.
    """

    def __init__(self, conf, pluginId, user):
        WCSTemplateBase.__init__(self, pluginId)
        self._conf = conf
        self._user = user


class WJSBase(WCSTemplateBase):
    """ Base class for Collaboration templates for Javascript code template.
        It overloads _setTPLFile so that indico can find the Main.js, Extra.js and Indexing.js files.
    """
    def __init__(self, conf, plugin, user):
        WCSTemplateBase.__init__(self, plugin)
        self._conf = conf
        self._user = user

    def _setTPLFile(self):
        WCSTemplateBase._setTPLFile(self, extension='js')
        self.helpFile = ''


class WCSCSSBase(WCSTemplateBase):
    """ Base class for Collaboration templates for CSS code template
        It overloads _setTPLFile so that indico can find the style.css files.
    """

    def _setTPLFile(self):
        tplDir = pkg_resources.resource_filename(self._plugin.getModule().__name__, "")
        fname = "%s.css" % self.tplId
        self.tplFile = os.path.join(tplDir, fname)
        self.helpFile = ''


class CSErrorBase(Fossilizable):
    fossilizes(ICSErrorBaseFossil)

    """ When _create, _modify or _remove want to return an error,
        they should return an error that inherits from this class
    """

    def __init__(self):
        pass

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

class SpeakerStatusEnum:
    (NOEMAIL, NOTSIGNED, SIGNED, FROMFILE, PENDING, REFUSED) = xrange(6)

class SpeakerWrapper(Persistent, Fossilizable):

    fossilizes(ISpeakerWrapperBaseFossil)

    def __init__(self, speaker, contId, requestType):
        self.status = not speaker.getEmail() and SpeakerStatusEnum.NOEMAIL or SpeakerStatusEnum.NOTSIGNED
        self.speaker = speaker
        self.contId = contId
        self.requestType = requestType
        self.reason = ""
        self.localFile = None
        self.dateAgreement = 0
        self.ipSignature = None
        self.modificationDate = nowutc()
        self.uniqueIdHash = md5("%s.%s"%(time.time(), self.getUniqueId())).hexdigest()

    def getUniqueId(self):
        return "%s.%s"%(self.contId, self.speaker.getId())

    def getUniqueIdHash(self):
        # to remove once saved
        if not hasattr(self, "uniqueIdHash"):#TODO: remove when safe
            return md5(self.getUniqueId()).hexdigest()
        else:
            return self.uniqueIdHash

    def getStatus(self):
        return self.status

    def setStatus(self, newStatus, ip=None):
        try:
            self.status = newStatus
            if newStatus == SpeakerStatusEnum.SIGNED or newStatus == SpeakerStatusEnum.FROMFILE:
                self.dateAgreement = now_utc()
                if newStatus == SpeakerStatusEnum.SIGNED:
                    self.ipSignature = ip
        except Exception, e:
            Logger.get('VideoServ').error("Exception while changing the speaker status. Exception: " + str(e))

    def getDateAgreementSigned(self):
        if hasattr(self, "dateAgreement"):#TODO: remove when safe
            return self.dateAgreement
        return 0

    def getIpAddressWhenSigned(self):
        if hasattr(self, "ipSignature"):#TODO: remove when safe
            return self.ipSignature
        return None

    def getRejectReason(self):
        if hasattr(self, "reason"):#TODO: remove when safe
            if self.status == SpeakerStatusEnum.REFUSED and hasattr(self, "reason"):
                return self.reason
            else:
                return "This speaker has not refused the agreement."
        else:
            return "Information not available."

    def setRejectReason(self, reason):
        if hasattr(self, "reason"):#TODO: remove when safe
            self.reason = reason

    def getObject(self):
        return self.speaker

    def getContId(self):
        return self.contId

    def getRequestType(self):
        if hasattr(self, "requestType"):#TODO: remove when safe
            return self.requestType
        return "NA"

    def setRequestType(self, type):
        self.requestType = type

    def getSpeakerId(self):
        return self.speaker.getId()

    def getLocalFile(self):
        '''
        If exists, return path to paper agreement
        '''
        if hasattr(self, "localFile"):#TODO: remove when safe
            return self.localFile

    def setLocalFile(self, localFile):
        '''
        Set localFile of paper agreement
        '''
        if hasattr(self, "localFile"):#TODO: remove when safe
            self.localFile = localFile

    def hasEmail(self):
        if self.speaker.getEmail():
            return True
        return False

    def getCategory(self):
        return None

    def getConference(self):
        return self.speaker.getConference()

    def getContribution(self):
        # if the conference is a lecture, the getContribution will fail.
        if self.getConference().getType() == "simple_event":
            return None
        else:
            return self.speaker.getContribution()

    def getSession(self):
        return None

    def getSubContribution(self):
        return None

    def getModificationDate(self):
        if hasattr(self, "modificationDate"):  # TODO: remove when safe
            return self.modificationDate
        return None

    def setModificationDate(self):
        if hasattr(self, "modificationDate"):  # TODO: remove when safe
            self.modificationDate = now_utc()

    def getLocator(self):
        return self.getContribution().getLocator()

    def triggerNotification(self):
        if self.getRequestType() in ('recording', 'webcast'):
            self._triggerNotification(self.getRequestType())
        elif self.getRequestType() == 'both':
            self._triggerNotification('recording')
            self._triggerNotification('webcast')

    def _triggerNotification(self, type):
        url = None
        if type == 'recording':
            url =  CollaborationTools.getOptionValue('RecordingRequest', 'AgreementNotificationURL')
        elif type == 'webcast':
            url =  CollaborationTools.getOptionValue('WebcastRequest', 'AgreementNotificationURL')
        if not url:
            return
        signed = None
        if self.getStatus() in (SpeakerStatusEnum.FROMFILE, SpeakerStatusEnum.SIGNED):
            signed = True
        elif self.getStatus() == SpeakerStatusEnum.REFUSED:
            signed = False
        spk = self.getObject()
        payload = {
            'confId': self.getConference().getId(),
            'contrib': self.getContId(),
            'type': type,
            'status': self.getStatus(),
            'signed': signed,
            'speaker': {
                'id': spk.getId(),
                'name': spk.getFullName(),
                'email': spk.getEmail()
            }
        }
        cl = Client()
        cl.enqueue(HTTPTask(url, {'data': json.dumps(payload)}))
