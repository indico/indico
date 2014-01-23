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

from collections import defaultdict
from persistent import Persistent
from persistent.list import PersistentList
from MaKaC.plugins.RoomBooking.rb_roomblocking import RoomBlockingBase
from MaKaC.rb_location import RoomGUID, Location
from MaKaC.plugins.RoomBooking.default.factory import Factory
import datetime
from MaKaC.user import Avatar, Group, AvatarHolder, GroupHolder
from MaKaC.rb_reservation import RepeatabilityEnum
from MaKaC.plugins.RoomBooking.default.reservation import ResvHistoryEntry
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification
from indico.core.config import Config

# Branch name in ZODB root
_ROOMBLOCKING = 'RoomBlocking'

class RoomBlocking(Persistent, RoomBlockingBase):

    __dalManager = Factory.getDALManager()

    def __init__(self):
        RoomBlockingBase.__init__(self)
        self.blockedRooms = PersistentList()
        self.allowed = PersistentList()

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        return cmp(self.id, other.id)

    @staticmethod
    def getRoot():
        return RoomBlocking.__dalManager.getRoot(_ROOMBLOCKING)

    @staticmethod
    def getTotalCount():
        return len(RoomBlocking.getRoot()['Blockings'])

    @staticmethod
    def getAll():
        return [block for block in RoomBlocking.getRoot()['Blockings'].itervalues()]

    @staticmethod
    def getById(id):
        blockingsBTree = RoomBlocking.getRoot()['Blockings']
        return blockingsBTree.get(id)

    @staticmethod
    def getByOwner(owner):
        idx = RoomBlocking.getRoot()['Indexes']['OwnerBlockings']
        return idx.get(owner.id, [])

    @staticmethod
    def getByRoom(room, active=-1):
        idx = RoomBlocking.getRoot()['Indexes']['RoomBlockings']
        blocks = idx.get(str(room.guid), [])
        return [block for block in blocks if active is block.active or active == -1]

    @staticmethod
    def getByDate(date):
        idx = RoomBlocking.getRoot()['Indexes']['DayBlockings']
        return list(idx.getObjectsInDay(date))

    @staticmethod
    def getByDateSpan(begin, end):
        idx = RoomBlocking.getRoot()['Indexes']['DayBlockings']
        return list(idx.getObjectsInDays(begin, end))

    def addAllowed(self, principal):
        """
        Add a principal (Avatar, Group, LDAPGroup or a RoomBlockingPrincipal)
        to the blocking's ACL
        """
        if isinstance(principal, RoomBlockingPrincipal):
            self.allowed.append(principal)
        else:
            self.allowed.append(RoomBlockingPrincipal(principal))

    def delAllowed(self, principal):
        """
        Remove a principal (Avatar, Group, LDAPGroup or a RoomBlockingPrincipal)
        from the blocking's ACL
        """
        if isinstance(principal, RoomBlockingPrincipal):
            self.allowed.remove(principal)
        else:
            self.allowed.remove(RoomBlockingPrincipal(principal))

    def getBlockedRoom(self, room):
        """
        Get the BlockedRoom object for a certain room
        """
        for br in self.blockedRooms:
            if br.roomGUID == str(room.guid):
                return br
        return None

    def notifyOwners(self):
        """
        Send emails to all room owners who need to approve blockings.
        Every owner gets only a single email, containing all the affected rooms.
        """
        notify_owners = defaultdict(list)
        for rb in self.blockedRooms:
            if rb.active is None and not rb.notificationSent:
                notify_owners[rb.room.responsibleId].append(rb)
                rb.notificationSent = True
        emails = []
        for ownerId, roomBlockings in notify_owners.iteritems():
            emails += RoomBlockingNotification.requestConfirmation(AvatarHolder().getById(ownerId), self, roomBlockings)
        for email in emails:
            GenericMailer.send(GenericNotification(email))

    def insert(self):
        """
        Insert a new blocking in the database, index it and reject colliding bookings
        """
        self.createdDT = datetime.datetime.now()
        # Save
        blockingsBTree = RoomBlocking.getRoot()['Blockings']
        # Ensure ID
        if self.id is None:
            # Maximum ID + 1
            if len(blockingsBTree) > 0:
                self.id = blockingsBTree.maxKey() + 1
            else:
                self.id = 1 # Can not use maxKey for 1st record in a tree
        # Add self to the BTree
        blockingsBTree[self.id] = self
        self._index()
        # Reject colliding bookings.
        for rb in self.blockedRooms:
            if rb.active:
                rb.approve(sendNotification=False)
        self.notifyOwners()

    def remove(self):
        """
        Remove a blocking from the database
        """
        self._unindex()
        blockingsBTree = RoomBlocking.getRoot()['Blockings']
        del blockingsBTree[self.id]

    def update(self):
        """
        Re-index a blocking and notify owners which haven't been notified before
        """
        self._unindex()
        self._index()
        self.notifyOwners()

    def _index(self):
        # Update room => room blocking index (it maps to the BlockedRoom objects)
        rbi = RoomBlocking.getRoot()['Indexes']['RoomBlockings']
        for rb in self.blockedRooms:
            roomBlockings = rbi.get(rb.roomGUID)
            if roomBlockings is None:
                roomBlockings = PersistentList()
                rbi[rb.roomGUID] = roomBlockings
            roomBlockings.append(rb)

        # Update owner => room blocking index
        obi = RoomBlocking.getRoot()['Indexes']['OwnerBlockings']
        roomBlockings = obi.get(self._createdBy)
        if roomBlockings is None:
            roomBlockings = PersistentList()
            obi[self._createdBy] = roomBlockings
        roomBlockings.append(self)

        # Update day => room blocking index
        cdbi = RoomBlocking.getRoot()['Indexes']['DayBlockings']
        cdbi.indexConf(self)

    def _unindex(self):
        # Update room => room blocking index
        rbi = RoomBlocking.getRoot()['Indexes']['RoomBlockings']
        for rb in self.blockedRooms:
            roomBlockings = rbi.get(rb.roomGUID)
            if roomBlockings is not None and rb in roomBlockings:
                roomBlockings.remove(rb)

        # Update owner => room blocking index
        obi = RoomBlocking.getRoot()['Indexes']['OwnerBlockings']
        roomBlockings = obi.get(self._createdBy)
        if roomBlockings is not None and self in roomBlockings:
            roomBlockings.remove(self)

        # Update day => room blocking index
        cdbi = RoomBlocking.getRoot()['Indexes']['DayBlockings']
        cdbi.unindexConf(self)

    def __repr__(self):
        return '<RoomBlocking(%r, %r, %s)>' % (self.id, self.blockedRooms, self.allowed)


class BlockedRoom(Persistent):

    def __init__(self, room, active=None):
        self.block = None
        self.roomGUID = str(room.guid)
        self.active = active # None = not approved yet
        self.notificationSent = False
        self.rejectionReason = None
        self.rejectedBy = None

    @property
    def room(self):
        return RoomGUID.parse(self.roomGUID).getRoom()

    def _unindex(self):
        rbi = RoomBlocking.getRoot()['Indexes']['RoomBlockings']
        roomBlockings = rbi.get(self.roomGUID)
        if roomBlockings is not None and self in roomBlockings:
            roomBlockings.remove(self)

    def approve(self, sendNotification=True):
        """
        Approve the room blocking and reject colloding bookings
        """
        self.active = True
        # If the blocking has not been saved yet, don't reject anything - will be done later in block.insert()
        if self.block.id is None:
            return
        # Create a fake reservation candidate to find bookings colliding with the blocking
        candResv = Location.parse(self.room.locationName).factory.newReservation()
        candResv.room = self.room
        candResv.startDT = datetime.datetime.combine(self.block.startDate, datetime.time())
        candResv.endDT = datetime.datetime.combine(self.block.endDate, datetime.time(23, 59))
        candResv.repeatability = RepeatabilityEnum.daily
        candResv.isConfirmed = None
        collisions = candResv.getCollisions()
        rejectionReason = "Conflict with blocking %s: %s" % (self.block.id, self.block.message)
        emailsToBeSent = []
        for coll in collisions:
            collResv = coll.withReservation
            if collResv.isRejected:
                continue
            elif self.block.canOverride(collResv.createdByUser(), self.room):
                continue
            elif (collResv.repeatability is None or
                (collResv.startDT.date() >= self.block.startDate and collResv.endDT.date() <= self.block.endDate)):
                collResv.rejectionReason = rejectionReason
                collResv.reject() # Just sets isRejected = True
                collResv.update()
                emails = collResv.notifyAboutRejection()
                emailsToBeSent += emails

                # Add entry to the booking history
                info = []
                info.append("Booking rejected")
                info.append("Reason: '%s'" % collResv.rejectionReason)
                histEntry = ResvHistoryEntry(self.block.createdByUser, info, emails)
                collResv.getResvHistory().addHistoryEntry(histEntry)
            else: # repeatable -> only reject the specific days
                rejectDate = coll.startDT.date()
                collResv.excludeDay(rejectDate, unindex=True)
                collResv.update()
                emails = collResv.notifyAboutRejection(date=rejectDate, reason=rejectionReason)
                emailsToBeSent += emails

                # Add entry to the booking history
                info = []
                info.append("Booking occurence of the %s rejected" % rejectDate.strftime("%d %b %Y"))
                info.append("Reason: '%s'" % rejectionReason)
                histEntry = ResvHistoryEntry(self.block.createdByUser, info, emails)
                collResv.getResvHistory().addHistoryEntry(histEntry)
        if sendNotification:
            emailsToBeSent += RoomBlockingNotification.blockingRequestProcessed(self)
        for email in emailsToBeSent:
            GenericMailer.send(GenericNotification(email))

    def reject(self, user=None, reason=None, sendNotification=True):
        """
        Reject the room blocking
        """
        self.active = False
        if reason:
            self.rejectionReason = reason
        if user:
            self.rejectedBy = user.getFullName()
        emails = RoomBlockingNotification.blockingRequestProcessed(self)
        for email in emails:
            GenericMailer.send(GenericNotification(email))

    def getActiveString(self):
        """
        Return a string describing the status
        """
        if self.active is None:
            return 'Pending'
        elif self.active:
            return 'Active'
        else:
            return 'Rejected'

    def getLocator(self):
        d = self.block.getLocator()
        d['room'] = self.roomGUID
        return d

    def __eq__(self, other):
        """
        Check if the room blockings are considered equal.
        This is the case if the rooms and parent blocks are identical.
        """
        return self.roomGUID == other.roomGUID and self.block is other.block

    def __repr__(self):
        return '<BlockedRoom(%r, %r)>' % (self.roomGUID, self.active)

class RoomBlockingPrincipal(Persistent):

    def __init__(self, principal):
        self._id = principal.id
        if isinstance(principal, Avatar):
            self._type = 'Avatar'
        elif isinstance(principal, Group):
            self._type = 'Group'
        else:
            raise ValueError('Invalid principal: %r' % principal)

    @classmethod
    def getByTypeId(cls, type, id):
        if type == 'Avatar':
            return cls(AvatarHolder().getById(id))
        elif type.endswith('Group'):
            return cls(GroupHolder().getById(id))
        else:
            return None

    def getPrincipal(self):
        if self._type == 'Avatar':
            return AvatarHolder().getById(self._id)
        else:
            return GroupHolder().getById(self._id)

    def getTypeString(self):
        if self._type == 'Avatar':
            return 'User'
        else:
            return 'Group'

    def containsUser(self, user):
        return self.getPrincipal().containsUser(user)

    def __eq__(self, other):
        return self._id == other._id and self._type == other._type

    def __repr__(self):
        return '<RoomBlockingPrincipal(%r, %r, %s)>' % (self._type, self._id, self.getPrincipal().getName())


class RoomBlockingNotification(object):

    @staticmethod
    def requestConfirmation(owner, block, roomBlockings):
        """
        Notifies (e-mails) room owner about blockings he has to approve.
        Expects only blockings for rooms owned by the specified owner
        """

        emails = []
        # ---- Email creator and contact ----

        to = owner.getEmail()

        subject = "Confirm room blockings"
        wc = WTemplated('RoomBookingEmail_2ResponsibleConfirmBlocking')
        text = wc.getHTML({
            'owner': owner,
            'block': block,
            'roomBlockings': roomBlockings
        })
        fromAddr = Config.getInstance().getNoReplyEmail()
        mailData = {
            "fromAddr": fromAddr,
            "toList": [to],
            "subject": subject,
            "body": text
        }
        emails.append(mailData)
        return emails

    @staticmethod
    def blockingRequestProcessed(roomBlocking):
        """
        Notifies (e-mails) blocking creator about approval/rejection of his
        blocking request for a room
        """

        emails = []
        # ---- Email creator and contact ----

        to = roomBlocking.block.createdByUser.getEmail()

        if roomBlocking.active == True:
            verb = 'ACCEPTED'
        else:
            verb = 'REJECTED'
        subject = "Room blocking %s" % verb
        wc = WTemplated('RoomBookingEmail_2BlockingCreatorRequestProcessed')
        text = wc.getHTML({
            'block': roomBlocking.block,
            'roomBlocking': roomBlocking,
            'verb': verb
        })
        fromAddr = Config.getInstance().getSupportEmail()
        mailData = {
            "fromAddr": fromAddr,
            "toList": [to],
            "subject": subject,
            "body": text
        }
        emails.append(mailData)
        return emails
