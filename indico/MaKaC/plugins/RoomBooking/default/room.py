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

import os as os
from BTrees.OOBTree import OOBTree, OOSet
from persistent import Persistent
from persistent.mapping import PersistentMapping
from MaKaC.rb_room import RoomBase
from MaKaC.rb_location import CrossLocationQueries, Location
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.rb_tools import qbeMatch
from indico.core.config import Config
from indico.core.db import DBMgr
from MaKaC.webinterface import urlHandlers

# fossils
from MaKaC.fossils.roomBooking import IRoomMapFossil, IRoomCalendarFossil
from MaKaC.common.fossilize import fossilizes, Fossilizable
import datetime
from MaKaC.common.contextManager import ContextManager
from MaKaC.user import GroupHolder

from indico.core.index import Catalog

# Branch name in ZODB root
_ROOMS = 'Rooms'


class Room(Persistent, RoomBase, Fossilizable):
    """
    ZODB specific implementation.

    For documentation of methods see base class.
    """

    fossilizes(IRoomMapFossil, IRoomCalendarFossil)

    __dalManager = Factory.getDALManager()
    vcList = []

    def __init__(self):
        RoomBase.__init__(self)
        self.customAtts = PersistentMapping()
        self.avaibleVC = []
        self._nonBookableDates = []
        self._dailyBookablePeriods = []

    def getDailyBookablePeriods(self):
        try:
            if self._dailyBookablePeriods:
                pass
        except AttributeError:
            self._dailyBookablePeriods = []
            self._p_changed = 1
        return self._dailyBookablePeriods

    def addDailyBookablePeriod(self, startTime, endTime):
        nbp = DailyBookablePeriod(startTime, endTime)
        self._dailyBookablePeriods.append(nbp)
        self._p_changed = 1

    def clearDailyBookablePeriods(self):
        self._dailyBookablePeriods = []
        self._p_changed = 1

    def getNonBookableDates(self, skipPast=False):
        try:
            if self._nonBookableDates:
                pass
        except AttributeError:
            self._nonBookableDates = []
            self._p_changed = 1
        if skipPast:
            return [d for d in self._nonBookableDates if not d.isPast()]
        return self._nonBookableDates

    def addNonBookableDates(self, startDate, endDate):
        nbd = NonBookableDate(startDate, endDate)
        self._nonBookableDates.append(nbd)
        self._p_changed = 1

    def clearNonBookableDates(self):
        self._nonBookableDates = []
        self._p_changed = 1

    def getBlockedDay(self, day):
        blockings = Factory.newRoomBlocking().getByDate(day)
        for bl in blockings:
            rbl = bl.getBlockedRoom(self)
            if rbl and rbl.active is not False:
                return rbl
        return None

    def setAvailableVC(self, avc):
        self.avaibleVC = avc

    def getAvailableVC(self):
        try:
            return self.avaibleVC
        except:
            self.avaibleVC = []
        return self.avaibleVC

    @staticmethod
    def getRoot():
        return Room.__dalManager.getRoot(_ROOMS)

    def getAllManagers(self):
        managers = set([self.getResponsible()])
        if self.customAtts.get('Simba List'):
            groups = GroupHolder().match({'name': self.customAtts['Simba List']},
                                         exact=True, searchInAuthenticators=False)
            if not groups:
                groups = GroupHolder().match({'name': self.customAtts['Simba List']}, exact=True)
            if groups and len(groups) == 1:
                managers |= set(groups[0].getMemberList())
        return list(managers)

    def insert(self):
        """ Documentation in base class. """
        RoomBase.insert(self)
        roomsBTree = Room.getRoot()
        # Ensure ID
        if self.id is None:
            # Maximum ID + 1
            if len(roomsBTree) > 0:
                self.id = roomsBTree.maxKey() + 1
            else:
                self.id = 1  # Can not use maxKey for 1st record in a tree
        # Add self to the BTree
        roomsBTree[self.id] = self
        Catalog.getIdx('user_room').index_obj(self.guid)

    def update(self):
        """ Documentation in base class. """
        RoomBase.update(self)

        # Check Simba mailing list
        listName = self.customAtts.get('Simba List')
        if listName:
            from MaKaC.user import GroupHolder
            groups = GroupHolder().match({'name': listName}, searchInAuthenticators=False)
            if not groups:
                groups = GroupHolder().match({'name': listName})
            if not groups:
                self.customAtts['Simba List'] = 'Error: unknown mailing list'

        # reindex - needed due to possible manager changes
        # super slow, though...
        Catalog.getIdx('user_room').unindex_obj(self.guid)
        Catalog.getIdx('user_room').index_obj(self.guid)

        self._p_changed = True

    def remove(self):
        """ Documentation in base class. """
        RoomBase.remove(self)
        roomsBTree = Room.getRoot()
        del roomsBTree[self.id]
        if Catalog.getIdx('user_room').has_obj(self.guid):
            Catalog.getIdx('user_room').unindex_obj(self.guid)

    @classmethod
    def isAvatarResponsibleForRooms(cls, avatar):
        return Catalog.getIdx('user_room').get(avatar.getId()) is not None

    @classmethod
    def getUserRooms(cls, avatar):
        return Catalog.getIdx('user_room').get(avatar.getId())

    # Typical actions
    @staticmethod
    def getRooms(*args, **kwargs):
        """ Documentation in base class. """

        roomsBTree = Room.getRoot()
        location = kwargs.get('location')

        if kwargs.get('allFast') is True:
            return [room for room in roomsBTree.values() if room.isActive and (not location or room.locationName == location)]

        if kwargs.get('reallyAllFast') is True:
            return [room for room in roomsBTree.values() if (not location or room.locationName == location)]

        if len(kwargs) == 0:
            ret_lst = []
            for room in roomsBTree.values():
                ret_lst.append(room)

        roomID = kwargs.get('roomID')
        roomName = kwargs.get('roomName')
        roomEx = kwargs.get('roomExample')
        resvEx = kwargs.get('resvExample')
        freeText = kwargs.get('freeText')
        available = kwargs.get('available')
        countOnly = kwargs.get('countOnly')
        minCapacity = kwargs.get('minCapacity')
        location = kwargs.get('location')
        ownedBy = kwargs.get('ownedBy')
        customAtts = kwargs.get('customAtts')
#        responsibleID = kwargs.get( 'responsibleID' )
        pendingBlockings = kwargs.get('pendingBlockings')

        # onlyPublic - there are no restrictions to booking (no ACL)
        onlyPublic = kwargs.get('onlyPublic')

        ret_lst = []
        counter = 0
        if roomID is not None:
            return roomsBTree.get(roomID)
        if roomName is not None:
            for room in roomsBTree.itervalues():
                if room.name == roomName:
                    if location is None or room.locationName == location:
                        return room
            return None

        for room in roomsBTree.itervalues():
            # Apply all conditions =========
            if location is not None:
                if room.locationName != location:
                    continue
            if onlyPublic and (not room.isReservable or room.hasBookingACL()):
                    continue
            if roomEx is not None:
                if not qbeMatch(roomEx, room, Room.__attrSpecialEqual, minCapacity=minCapacity):
                    continue
                if not room.__hasEquipment(roomEx.getEquipment()):
                    continue
            if freeText is not None:
                if not room.__hasFreeText(freeText.split()):
                    continue
            if resvEx is not None:
                resvEx.room = room
                aval = room.isAvailable(resvEx)
                if aval != available:
                    continue
                blockState = resvEx.getBlockingConflictState(ContextManager.get('currentUser'))
                if blockState == 'active':
                    continue
                elif blockState == 'pending' and pendingBlockings:
                    continue
            if ownedBy is not None:
                if not room.isOwnedBy(ownedBy):
                    continue
            if customAtts is not None:
                if not hasattr(room, "customAtts"):
                    continue
                discard = False
                for condition in customAtts:
                    attName = condition["name"]
                    allowEmpty = condition.get("allowEmpty", False)
                    filter = condition.get("filter", None)
                    if not attName in room.customAtts:
                        discard = True
                        break
                    elif not allowEmpty and str(room.customAtts[attName]).strip() == "":
                        discard = True
                        break
                    elif not filter(room.customAtts[attName]):
                        discard = True
                        break
                if discard:
                    continue

            # All conditions are met: add room to the results
            counter += 1
            if not countOnly:
                ret_lst.append(room)

        #print "Found %d rooms." % counter
        if countOnly:
            return counter
        else:
            return ret_lst

    # Statistics ====================================

    @staticmethod
    def countRooms(*args, **kwargs):
        """ Documentation in base class. """
        kwargs['countOnly'] = True
        return Room.getRooms(**kwargs)

    @staticmethod
    def getNumberOfRooms(*args, **kwargs):
        """ Documentation in base class. """
        location = kwargs.get('location', Location.getDefaultLocation().friendlyName)
        return Room.countRooms(location=location)

    @staticmethod
    def getNumberOfActiveRooms(*args, **kwargs):
        """ Documentation in base class. """
        location = kwargs.get('location', Location.getDefaultLocation().friendlyName)
        room = Factory.newRoom()
        room.isActive = True
        return Room.countRooms(roomExample=room, location=location)

    @staticmethod
    def getNumberOfReservableRooms(*args, **kwargs):
        """ Documentation in base class. """
        location = kwargs.get('location', Location.getDefaultLocation().friendlyName)
        room = Factory.newRoom()
        room.isReservable = True
        room.isActive = True
        return Room.countRooms(roomExample=room, location=location)

    def getLocationName(self):
        #from MaKaC.plugins.RoomBooking.default.factory import Factory
        #return Factory.locationName
        return self._locationName

    def setLocationName(self, locationName):
        self._locationName = locationName

    def savePhoto(self, photoPath):
        filePath = Config.getInstance().getRoomPhotosDir()
        fileName = self._doGetPhotoId(force=True) + ".jpg"
        try:
            os.makedirs(filePath)
        except:
            pass
        fullPath = os.path.join(filePath, fileName)

        f = open(fullPath, "wb")
        f.write(photoPath.file.read())
        f.close()

    def saveSmallPhoto(self, photoPath):
        filePath = Config.getInstance().getRoomSmallPhotosDir()
        fileName = self._doGetPhotoId(force=True) + ".jpg"
        try:
            os.makedirs(filePath)
        except:
            pass
        fullPath = os.path.join(filePath, fileName)

        f = open(fullPath, "wb")
        f.write(photoPath.file.read())
        f.close()

    # ==== Private ===================================================

    def _getSafeLocationName(self):
        if self.locationName is None:
            return None
        s = ""
        for i in xrange(0, len(self.locationName)):
            code = ord(self.locationName[i])
            if (code in xrange(ord('a'), ord('z') + 1)) or \
               (code in xrange(ord('A'), ord('Z') + 1)) or \
               (code in xrange(ord('0'), ord('9') + 1)):
                # Valid
                s += self.locationName[i]
            else:
                s += '_'  # Replace all other characters with underscore
        return s

    def _doGetPhotoId(self, force=False):
        photoId = "%s-%s-%s-%s" % (str(self._getSafeLocationName()), str(self.building).strip(), str(self.floor).strip(), str(self.roomNr).strip())

        filePath = Config.getInstance().getRoomPhotosDir()
        fileName = photoId + ".jpg"
        fullPath = os.path.join(filePath, fileName)
        from os.path import exists
        if exists(fullPath) or force:
            return photoId
        else:
            return None

    def _doSetPhotoId(self):
        """
        For this plugin, photoId is always composed of location-building-floor-room.jpg
        """
        pass

    def __hasFreeText(self, freeTextList):
        # OR
        for freeText in freeTextList:
            freeText = freeText.lower()
            if self.__hasOneFreeText(freeText):
                return True
        return False

    def __hasOneFreeText(self, freeText):
        # Look for freeText in all string and int attributes
        for attrName in dir(self):
            if attrName[0] == '_':
                continue
            attrType = eval('self.' + attrName + '.__class__.__name__')
            if attrType == 'str':
                attrVal = eval('self.' + attrName)
                if attrVal.lower().find(freeText) != -1:
                    return True

        # Look for freeText in equipment
        if self.__hasEquipment([freeText]):
            return True

        # Look for freeText in responsible
        if self.responsibleId is not None:
            user = self.getResponsible()
            if freeText in user.getFullName().lower() or freeText in user.getEmail().lower():
                return True

        # Look for freeText in custom attributes
        for value in self.customAtts.itervalues():
            if value and (freeText in value.lower()):
                return True

        # Not found
        return False

    @staticmethod
    def __goodCapacity(val1, val2, minCapacity=None):
        # Difference in capacity less than 20%
        if val1 < 1:
            val1 = 1

        if not minCapacity:
            return abs(val1 - val2) / float(val1) <= 0.2
        else:
            return val2 > val1

    @classmethod
    def __attrSpecialEqual(cls, attrName, exampleVal, candidateVal, **kwargs):
        if attrName in ('guid', 'locationName', 'name', 'photoId', 'needsAVCSetup'):
            return True  # Skip by stating they match
        if attrName in ('responsibleId', 'responsibleID'):
            return exampleVal == candidateVal  # Just exact string matching
        if attrName[0:7] == 'verbose':
            return True
        if attrName.find('capacity') != -1:
            minCapacity = kwargs.get('minCapacity')
            return cls.__goodCapacity(exampleVal, candidateVal, minCapacity)
        if attrName == 'customAtts':
            # Check if all values in exampleVal are contained
            # in corresponding values of candidateVal
            for k, v in exampleVal.iteritems():
                if v:  # If value is specified
                    if candidateVal.get(k) is None:
                        # Candidate does not have the attribute
                        return False
                    if not (v in candidateVal[k]):
                        # Candidate's attribute value does not match example
                        return False
            return True
        return None

    def __hasEquipment(self, requiredEquipmentList):
        iHave = self.getEquipment()
        for reqEq in requiredEquipmentList:
            have = False
            for myEq in iHave:
                if myEq.lower().find(reqEq.lower()) != -1:
                    have = True
                    break
            if not have:
                return False
        return True

    def getBookingUrl(self):
        """ Room booking URL """
        return str(urlHandlers.UHRoomBookingBookingForm.getURL(target=self))

    def getDetailsUrl(self):
        """ Room details URL """
        return str(urlHandlers.UHRoomBookingRoomDetails.getURL(target=self))

    def getMarkerDescription(self):
        """ Room description for the map marker """
        infos = []
        if self.capacity:
            infos.append("%s %s" % (self.capacity, _("people")))
        if self.isReservable and not self.hasBookingACL():
            infos.append(_("public"))
        else:
            infos.append(_("private"))
        if self.resvsNeedConfirmation:
            infos.append(_("needs confirmation"))
        else:
            infos.append(_("auto-confirmation"))
        if self.needsAVCSetup:
            infos.append(_("video conference"))
        return ", ".join(infos)

    def getTipPhotoURL(self):
        """ URL of the tip photo of the room """
        from MaKaC.webinterface.urlHandlers import UHRoomPhoto
        photoId = self._doGetPhotoId() or "NoPhoto"
        return str(UHRoomPhoto.getURL(photoId))

    def getThumbnailPhotoURL(self):
        """ URL of the tip photo of the room """
        from MaKaC.webinterface.urlHandlers import UHRoomPhotoSmall
        if self._doGetPhotoId():
            photoId = self._doGetPhotoId()
            return str(UHRoomPhotoSmall.getURL(photoId))
        else:
            photoId = "NoPhoto"
            return str(UHRoomPhotoSmall.getURL(photoId, "png"))

    def hasPhoto(self):
        return self._doGetPhotoId() is not None

    def getIsAutoConfirm(self):
        """ Has the room auto-confirmation of schedule? """
        return not self.resvsNeedConfirmation

    def isPublic(self):
        return self.isReservable and not self.customAtts.get('Booking Simba List')

    locationName = property(getLocationName, setLocationName)


class NonBookableDate(Persistent):

    def __init__(self, startDate, endDate):
        self.setStartDate(startDate)
        self.setEndDate(endDate)

    def toDict(self):
        return {"startDate": self._startDate,
                "endDate": self._endDate}

    def saveFromDict(self, data):
        self.setStartDate(data["startDate"])
        self.setEndDate(data["endDate"])

    def getStartDate(self):
        return self._startDate

    def setStartDate(self, startDate):
        if startDate is None:
            self._startDate = None
        else:
            self._startDate = startDate

    def getEndDate(self):
        return self._endDate

    def setEndDate(self, endDate):
        if endDate is None:
            self._endDate = None
        else:
            self._endDate = endDate

    def doesPeriodOverlap(self, startDate, endDate):
        if self.getEndDate() <= startDate or endDate <= self.getStartDate():
            return False
        return True

    def isPast(self):
        return self.getEndDate() <= datetime.datetime.now()


class DailyBookablePeriod(Persistent):

    def __init__(self, startTime, endTime):
        self.setStartTime(startTime)
        self.setEndTime(endTime)

    def toDict(self):
        return {"startTime": self._startTime,
                "endTime": self._endTime}

    def saveFromDict(self, data):
        self.setStartTime(data["startTime"])
        self.setEndTime(data["endTime"])

    def getStartTime(self):
        return self._startTime

    def setStartTime(self, startTime):
        self._startTime = startTime

    def getEndTime(self):
        return self._endTime

    def setEndTime(self, endTime):
        self._endTime = endTime

    def doesPeriodFit(self, startTime, endTime):
        periodStart = datetime.datetime.strptime(self.getStartTime(), "%H:%M").time()
        periodEnd = datetime.datetime.strptime(self.getEndTime(), "%H:%M").time()
        return startTime >= periodStart and endTime <= periodEnd


# ============================================================================
# ================================== TEST ====================================
# ============================================================================

class Test(object):

    dalManager = Factory.getDALManager()

    @staticmethod
    def do():
        # Set equipment
        Test.dalManager.connect()
        em = Factory.getEquipmentManager()
        saved = ['a ', 'bbb', 'c']
        em.setPossibleEquipment(saved)
        Test.dalManager.commit()
        Test.dalManager.disconnect()

        # Get equipment
        Test.dalManager.connect()
        loaded = em.getPossibleEquipment()
        assert(loaded == saved)
        Test.dalManager.disconnect()

    @staticmethod
    def getRoomsByExample():
        Test.dalManager.connect()

        # By ID
        room = RoomBase.getRooms(roomID=176)
        assert(room.name == '4-1-021')

        # By other attributes
        roomEx = Factory.newRoom()
        roomEx.site = 'prevessin'
        roomEx.comments = 'res'
        rooms = RoomBase.getRooms(roomExample=roomEx)
        assert(len(rooms) == 8)  # 20

        roomEx = Factory.newRoom()
        roomEx.capacity = 20
        rooms = RoomBase.getRooms(roomExample=roomEx)
        assert(len(rooms) == 26)

        roomEx = Factory.newRoom()
        roomEx.isReservable = True
        roomEx.setEquipment(['Video projector', 'Wireless'])
        rooms = RoomBase.getRooms(roomExample=roomEx)
        assert(len(rooms) == 33)

        Test.dalManager.disconnect()

    @staticmethod
    def getRoomsByFreeText():
        Test.dalManager.connect()

        rooms = RoomBase.getRooms(freeText='meyrin vrvs')  # 78828
        assert(len(rooms) == 12)

        Test.dalManager.disconnect()

    @staticmethod
    def getRoomsByExampleDemo():
        Test.dalManager.connect()

        roomEx = Factory.newRoom()

        roomEx.building = 513
        roomEx.capacity = 20

        rooms = CrossLocationQueries.getRooms(roomExample=roomEx)

        for room in rooms:
            print "============================="
            print room

        Test.dalManager.disconnect()

    @staticmethod
    def stats():
        Test.dalManager.connect()
        print "All rooms: %d" % RoomBase.getNumberOfRooms()
        print "Active rooms: %d" % RoomBase.getNumberOfActiveRooms()
        print "Reservable rooms: %d" % RoomBase.getNumberOfReservableRooms()
        Test.dalManager.disconnect()

    @staticmethod
    def getAvailableRooms():
        Test.dalManager.connect()

        from datetime import datetime

        roomEx = Factory.newRoom()
        roomEx.isActive = True
        roomEx.isReservable = True

        resvEx = Factory.newReservation()
        resvEx.startDT = datetime(2006, 12, 01, 10)
        resvEx.endDT = datetime(2006, 12, 14, 15)
        resvEx.repeatability = 0  # Daily

        rooms = RoomBase.getRooms(
            roomExample=roomEx,
            resvExample=resvEx,
            available=True)

        for room in rooms:
            print "\n=======================================\n"
            print room

        Test.dalManager.disconnect()

if __name__ == '__main__':
    Test.getAvailableRooms()
#    Test.do()
#    Test.getRoomsByExampleDemo()
#    for i in xrange( 3 ):
#        Test.getRoomsByFreeText()
#        Test.getRoomsByExample()
#        Test.stats()
