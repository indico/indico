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

# For now, disable Pylint
# pylint: disable-all

from indico.tests.env import *
from indico.tests.python.unit.util import IndicoTestFeature, IndicoTestCase, with_context
from MaKaC.user import AvatarHolder, Avatar, Group, GroupHolder, LoginInfo
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common.info import HelperMaKaCInfo
from indico.core import config as Configuration
from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
from MaKaC.plugins.RoomBooking.CERN.initialize import initializeRoomBookingDB
from MaKaC.rb_location import Location
from datetime import date, datetime, time, timedelta
from MaKaC.rb_reservation import RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.plugins.RoomBooking.default.roomblocking import BlockedRoom
from MaKaC.common.mail import GenericMailer
from MaKaC.plugins.RoomBooking.rb_roomblocking import RoomBlockingBase


class RoomBooking_Feature(IndicoTestFeature):
    _requires = ['db.DummyUser', 'plugins.Plugins']

    def start(self, obj):
        super(RoomBooking_Feature, self).start(obj)

        with obj._context('database'):
            # Tell indico to use the current database for roombooking stuff
            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
            cfg = Configuration.Config.getInstance()
            minfo.setRoomBookingDBConnectionParams(cfg.getDBConnectionParams())

            obj._ph.getById('RoomBooking').setActive(True)

            DALManagerCERN.connect()
            initializeRoomBookingDB("Universe", force=False)
            DALManagerCERN.disconnect()
            # do not use the method for it as it tries to re-create jsvars and fails
            minfo._roomBookingModuleActive = True
            DALManagerCERN.connect()

            # Create dummy rooms in obj._roomN - owners are fake1 and fake2 (r1 has f1, r2 has f2, r3 has f1, ...)
            location = Location.getDefaultLocation()
            obj._rooms = []
            for i in xrange(1, 8):
                room = location.newRoom()
                room.locationName = location.friendlyName
                room.name = 'DummyRoom%d' % i
                room.site = 'a'
                room.building = 1
                room.floor = 'b'
                room.roomNr = 'c'
                room.latitude = ''
                room.longitude = ''
                room.isActive = True
                room.isReservable = True
                room.resvsNeedConfirmation = False
                room.responsibleId = 'fake-%d' % (((i - 1) % 2) + 1)
                room.whereIsKey = 'Nowhere'
                room.telephone = '123456789'
                room.capacity = 10
                room.division = ''
                room.surfaceArea = 50
                room.comments = ''
                room.setEquipment([])
                room.setAvailableVC([])
                room.insert()
                obj._rooms.append(room)
                setattr(obj, '_room%d' % i, room)


class RoomBookingTestCase(IndicoTestCase):
    _requires = ['util.RequestEnvironment', 'db.DummyUser', RoomBooking_Feature]

    def _createResv(self, room, user, startDate, endDate, pre=False):
        resv = Location.getDefaultLocation().factory.newReservation()
        resv.room = room
        resv.startDT = datetime.combine(startDate, time(8, 30))
        resv.endDT = datetime.combine(endDate, time(17, 30))
        if startDate != endDate:
            resv.repeatability = RepeatabilityEnum.daily
        resv.reason = ''
        resv.needsAVCSupport = False
        resv.usesAVC = False
        resv.createdDT = datetime.now()
        resv.createdBy = str(user.getId())
        resv.bookedForName = user.getFullName()
        resv.contactEmail = user.getEmail()
        resv.contactPhone = user.getTelephone()
        resv.isRejected = False
        resv.isCancelled = False
        resv.isConfirmed = True if not pre else None
        resv.insert()
        return resv


class TestRoomBookingDBSetup(IndicoTestCase):
    _requires = [RoomBooking_Feature]

    @with_context('database')
    def testDummies(self):
        self.assertEqual(self._room1.getResponsible(), self._avatar1)
        self.assertEqual(self._room2.getResponsible(), self._avatar2)
        self.assertEqual(self._room3.getResponsible(), self._avatar1)
        self.assertEqual(self._room4.getResponsible(), self._avatar2)


class TestRoomBlocking(RoomBookingTestCase):

    def setUp(self):
        super(TestRoomBlocking, self).setUp()

    def _blockRoom(self, block, room, approve=True):
        br = BlockedRoom(room)
        block.addBlockedRoom(br)
        if approve:
            br.approve(sendNotification=False)
        return br

    def _createTestBlocking(self):
        block = Factory.newRoomBlocking()()
        block.startDate = date(2010, 12, 31)
        block.endDate = date(2011, 1, 1)
        block.createdByUser = self._avatar2
        block.addAllowed(self._avatar4)
        block.message = 'Testing'
        self._blockRoom(block, self._room1)
        self._blockRoom(block, self._room2)
        self._blockRoom(block, self._room3)
        self._blockRoom(block, self._room4)
        self._blockRoom(block, self._room6)
        block.insert()
        return block

    def _createTestReservations(self):
        self._resv1 = self._createResv(self._room1, self._avatar1, date(2011, 1, 1), date(2011, 1, 1)) # booked by owner
        self._resv2 = self._createResv(self._room2, self._avatar2, date(2011, 1, 1), date(2011, 1, 1)) # booked by owner
        self._resv3 = self._createResv(self._room3, self._avatar3, date(2011, 1, 1), date(2011, 1, 1))
        self._resv4 = self._createResv(self._room4, self._avatar4, date(2011, 1, 1), date(2011, 1, 1))
        self._resv5 = self._createResv(self._room7, self._avatar1, date(2011, 1, 2), date(2011, 1, 2))
        self._resv6 = self._createResv(self._room3, self._avatar2, date(2010, 1, 31), date(2010, 1, 31))
        self._resv7 = self._createResv(self._room5, self._avatar2, date(2011, 1, 1), date(2011, 1, 1))
        self._resv8 = self._createResv(self._room6, self._avatar3, date(2010, 12, 30), date(2011, 1, 2))
        self._resv9 = self._createResv(self._room7, self._avatar3, date(2011, 1, 1), date(2011, 1, 1))

    @with_context('database')
    def testGeneralData(self):
        block = self._createTestBlocking()
        self.assertEqual(block.createdByUser, self._avatar2)
        self.assertEqual(block.getStartDate().date(), block.startDate)
        self.assertEqual(block.getEndDate().date(), block.endDate)
        self.assertEqual(block.getStartDate().time(), time())
        self.assertEqual(block.getEndDate().time(), time())

    @with_context('database')
    def testIndexes(self):
        block = self._createTestBlocking()
        block2 = Factory.newRoomBlocking()()
        block2.startDate = date(2011, 1, 1)
        block2.endDate = date(2011, 1, 10)
        block2.createdByUser = self._avatar3
        block2.message = 'Testing 2'
        self._blockRoom(block2, self._room1)
        block2.insert()
        # Test if all indexes work properly
        self.assertEqual(frozenset(RoomBlockingBase.getAll()), frozenset((block, block2)))
        self.assertTrue(RoomBlockingBase.getById(0) is None)
        self.assertEqual(RoomBlockingBase.getById(1), block)
        self.assertEqual(RoomBlockingBase.getById(2), block2)
        self.assertTrue(not RoomBlockingBase.getByOwner(self._dummy))
        self.assertTrue(not RoomBlockingBase.getByOwner(self._avatar1))
        self.assertEqual(frozenset(RoomBlockingBase.getByOwner(self._avatar2)), frozenset((block,)))
        self.assertEqual(frozenset(RoomBlockingBase.getByOwner(self._avatar3)), frozenset((block2,)))
        self.assertTrue(not RoomBlockingBase.getByRoom(self._room5))
        self.assertEqual(frozenset(RoomBlockingBase.getByRoom(self._room1)),
                         frozenset((block.getBlockedRoom(self._room1), block2.getBlockedRoom(self._room1))))
        self.assertEqual(frozenset(RoomBlockingBase.getByRoom(self._room2)),
                         frozenset((block.getBlockedRoom(self._room2),)))
        self.assertTrue(block2.getBlockedRoom(self._room2) is None)
        self.assertEqual(frozenset(RoomBlockingBase.getByDate(date(2010, 12, 31))), frozenset((block,)))
        self.assertEqual(frozenset(RoomBlockingBase.getByDate(date(2011, 1, 1))), frozenset((block, block2)))
        self.assertEqual(frozenset(RoomBlockingBase.getByDate(date(2011, 1, 2))), frozenset((block2,)))
        self.assertEqual(frozenset(RoomBlockingBase.getByDateSpan(date(2011, 1, 1), date(2011, 1, 2))),
                         frozenset((block, block2)))
        self.assertEqual(frozenset(RoomBlockingBase.getByDateSpan(date(2011, 1, 2), date(2011, 2, 1))),
                         frozenset((block2,)))
        self.assertTrue(not RoomBlockingBase.getByDateSpan(date(2011, 2, 1), date(2012, 1, 1)))
        # Remove a block
        block.remove()
        self.assertEqual(len(RoomBlockingBase.getAll()), 1)
        self.assertTrue(RoomBlockingBase.getById(block.id) is None)
        self.assertTrue(not RoomBlockingBase.getByOwner(self._avatar2))
        self.assertEqual(frozenset(RoomBlockingBase.getByRoom(self._room1)),
                         frozenset((block2.getBlockedRoom(self._room1),)))
        self.assertTrue(not RoomBlockingBase.getByRoom(self._room2))
        self.assertTrue(not RoomBlockingBase.getByDate(date(2010, 12, 31)))
        self.assertEqual(frozenset(RoomBlockingBase.getByDate(date(2011, 1, 1))), frozenset((block2,)))
        self.assertEqual(frozenset(RoomBlockingBase.getByDate(date(2011, 1, 2))), frozenset((block2,)))
        # Add a blocked room
        br = self._blockRoom(block2, self._room2)
        block2.addBlockedRoom(br)
        # When adding a blocked room, update() may be (and is) required for it to beindexed
        block2.update()
        self.assertEqual(frozenset(RoomBlockingBase.getByRoom(self._room2)),
                         frozenset((block2.getBlockedRoom(self._room2),)))
        self.assertEqual(frozenset(RoomBlockingBase.getByRoom(self._room1)),
                         frozenset((block2.getBlockedRoom(self._room1),)))
        block2.delBlockedRoom(block2.getBlockedRoom(self._room1))
        # Deletion has to update indexes immediately as the object will no longer be reachable from its parent block
        self.assertTrue(not RoomBlockingBase.getByRoom(self._room1))
        block2.update()
        self.assertTrue(not RoomBlockingBase.getByRoom(self._room1))

    @with_context('database')
    @with_context('request')
    def testBlockingRejectionIfNotAllowed(self):
        self._createTestReservations()
        block = self._createTestBlocking()

        # Check rejection flags
        self.assertFalse(self._resv1.isRejected) # should not be rejected: owner booking
        self.assertFalse(self._resv2.isRejected) # should not be rejected: owner booking and blocking owner
        self.assertTrue(self._resv3.isRejected)  # should be rejected
        self.assertFalse(self._resv4.isRejected) # should not be rejected: blocking ACL
        self.assertFalse(self._resv5.isRejected) # should not be rejected: date
        self.assertFalse(self._resv6.isRejected) # should not be rejected: blocking owner
        self.assertFalse(self._resv7.isRejected) # should not be rejected: room not blocked
        self.assertFalse(self._resv8.isRejected) # should be partially rejected - excluded days assertion is done later
        self.assertFalse(self._resv9.isRejected) # should not be rejected: room not blocked
        # Check partial rejections
        self.assertEqual(self._resv1.getExcludedDays(), [])
        self.assertEqual(self._resv2.getExcludedDays(), [])
        self.assertEqual(self._resv3.getExcludedDays(), [])
        self.assertEqual(self._resv4.getExcludedDays(), [])
        self.assertEqual(self._resv5.getExcludedDays(), [])
        self.assertEqual(self._resv6.getExcludedDays(), [])
        self.assertEqual(self._resv7.getExcludedDays(), [])
        self.assertEqual(frozenset(self._resv8.getExcludedDays()),
                         frozenset((date(2010, 12, 31), date(2011, 1, 1))))
        self.assertEqual(self._resv9.getExcludedDays(), [])
        # Add blocked room to existing blocking
        self._blockRoom(block, self._room5)
        block.update()
        self.assertFalse(self._resv7.isRejected) # should still not be rejected: room booked by blocking owner
        br = self._blockRoom(block, self._room7, False)
        block.update()
        self.assertFalse(self._resv9.isRejected) # should still not be rejected: blocking is pending
        br.approve(sendNotification=False)
        self.assertTrue(self._resv9.isRejected) # should be rejected: blocking has been approved

    @with_context('database')
    @with_context('request')
    def testReservationSpecificBlockingMethods(self):
        block = self._createTestBlocking()
        candResv = Location.getDefaultLocation().factory.newReservation()
        candResv.startDT = datetime.combine(block.startDate - timedelta(days=1), time())
        candResv.endDT = datetime.combine(block.endDate + timedelta(days=1), time(23, 59))
        candResv.repeatability = RepeatabilityEnum.daily
        candResv.isConfirmed = None

        candResv.room = self._room7
        self.assertTrue(candResv.getBlockingConflictState() is None) # No blocking
        self.assertEqual(candResv.getBlockedDates(), [])
        br = self._blockRoom(block, self._room7, False)
        block.update()
        self.assertEqual(candResv.getBlockingConflictState(), 'pending') # Pending blocking
        self.assertEqual(candResv.getBlockedDates(), [])
        br.approve(sendNotification=False)
        self.assertEqual(candResv.getBlockingConflictState(), 'active') # Active blocking
        blockingDays = frozenset((date(2010, 12, 31), date(2011, 1, 1)))
        self.assertEqual(frozenset(candResv.getBlockedDates()), blockingDays)
        # Test with various users set. This basically tests if all people who are allowed to override can actually override
        self.assertTrue(candResv.getBlockingConflictState(self._avatar1) is None) # room owner
        self.assertEqual(candResv.getBlockedDates(self._avatar1), [])
        self.assertTrue(candResv.getBlockingConflictState(self._avatar2) is None) # blocking owner
        self.assertEqual(candResv.getBlockedDates(self._avatar2), [])
        self.assertEqual(candResv.getBlockingConflictState(self._avatar3), 'active') # not permitted to override
        self.assertEqual(frozenset(candResv.getBlockedDates(self._avatar3)), blockingDays)
        self.assertTrue(candResv.getBlockingConflictState(self._avatar4) is None) # on blocking ACL
        self.assertEqual(candResv.getBlockedDates(self._avatar4), [])
        # Rejecting an existing blocking is not possible via the UI, but we can test it anyway
        br.reject(sendNotification=False)
        self.assertTrue(candResv.getBlockingConflictState() is None) # No blocking
        self.assertEqual(candResv.getBlockedDates(), [])

    @with_context('database')
    def testPrivileges(self):
        block = self._createTestBlocking() # owner: av2, acl: av4
        # canModify: admins and owner
        self.assertFalse(block.canModify(self._avatar3)) # some random user
        self.assertFalse(block.canModify(self._avatar4)) # acl
        self.assertTrue(block.canModify(self._avatar2)) # owner
        self.assertTrue(block.canModify(self._dummy)) # admin
        # canDelete: admins and owner
        self.assertFalse(block.canDelete(self._avatar3)) # some random user
        self.assertFalse(block.canDelete(self._avatar4)) # acl
        self.assertTrue(block.canDelete(self._avatar2)) # owner
        self.assertTrue(block.canDelete(self._dummy)) # admin
        # canOverride
        ## no room given, not only explicitly allowed (acl/owner) users
        self.assertFalse(block.canOverride(self._avatar3)) # some random user
        self.assertTrue(block.canOverride(self._avatar4)) # acl
        self.assertTrue(block.canOverride(self._avatar2)) # owner
        self.assertTrue(block.canOverride(self._dummy)) # admin
        self.assertFalse(block.canOverride(self._avatar1)) # owner of a blocked room
        ## no room given, only explicitly allowed (acl/owner) users
        self.assertFalse(block.canOverride(self._avatar3, explicitOnly=True)) # some random user
        self.assertTrue(block.canOverride(self._avatar4, explicitOnly=True)) # acl
        self.assertTrue(block.canOverride(self._avatar2, explicitOnly=True)) # owner
        self.assertFalse(block.canOverride(self._dummy, explicitOnly=True)) # admin
        self.assertFalse(block.canOverride(self._avatar1, explicitOnly=True)) # owner of a blocked room
        ## room given, not only explicitly allowed (acl/owner) users
        self.assertFalse(block.canOverride(self._avatar3, room=self._room1)) # some random user
        self.assertTrue(block.canOverride(self._avatar4, room=self._room1)) # acl
        self.assertTrue(block.canOverride(self._avatar2, room=self._room1)) # owner
        self.assertTrue(block.canOverride(self._dummy, room=self._room1)) # admin
        self.assertTrue(block.canOverride(self._avatar1, room=self._room1)) # owner of a blocked room, checking for his room
        self.assertFalse(block.canOverride(self._avatar1, room=self._room2)) # owner of a blocked room, checking for another roomm
        ## room given, only explicitly allowed (acl/owner) users
        self.assertFalse(block.canOverride(self._avatar3, room=self._room1, explicitOnly=True)) # some random user
        self.assertTrue(block.canOverride(self._avatar4, room=self._room1, explicitOnly=True)) # acl
        self.assertTrue(block.canOverride(self._avatar2, room=self._room1, explicitOnly=True)) # owner
        self.assertFalse(block.canOverride(self._dummy, room=self._room1, explicitOnly=True)) # admin
        self.assertFalse(block.canOverride(self._avatar1, room=self._room1, explicitOnly=True)) # owner of a blocked room, checking for his room
        self.assertFalse(block.canOverride(self._avatar1, room=self._room2, explicitOnly=True)) # owner of a blocked room, checking for another room

        # isOwnedBy: obviously only the owner
        self.assertFalse(block.isOwnedBy(self._avatar3)) # some random user
        self.assertFalse(block.isOwnedBy(self._avatar4)) # acl
        self.assertTrue(block.isOwnedBy(self._avatar2)) # owner
        self.assertFalse(block.isOwnedBy(self._dummy)) # admin

    @with_context('database')
    def testACL(self):
        block = self._createTestBlocking()
        grp = Group()
        grp.setName('Test')
        GroupHolder().add(grp)

        self.assertFalse(block.canOverride(self._avatar1))
        self.assertTrue(block.canOverride(self._avatar2))
        self.assertFalse(block.canOverride(self._avatar3))
        self.assertTrue(block.canOverride(self._avatar4))
        # Add user to acl
        block.addAllowed(self._avatar1)
        self.assertTrue(block.canOverride(self._avatar1))
        # Add empty group to acl
        block.addAllowed(grp)
        self.assertTrue(block.canOverride(self._avatar1))
        self.assertTrue(block.canOverride(self._avatar2))
        self.assertFalse(block.canOverride(self._avatar3))
        self.assertTrue(block.canOverride(self._avatar4))
        # Add user to group
        grp.addMember(self._avatar3)
        self.assertTrue(block.canOverride(self._avatar3))
        # Remove user from acl
        block.delAllowed(self._avatar1)
        self.assertFalse(block.canOverride(self._avatar1))
        # But add him to a permitted group!
        grp.addMember(self._avatar1)
        self.assertTrue(block.canOverride(self._avatar1))
        # Remove users from group
        for m in list(grp.getMemberList()):
            grp.removeMember(m)
        self.assertFalse(block.canOverride(self._avatar1))
        self.assertTrue(block.canOverride(self._avatar2))
        self.assertFalse(block.canOverride(self._avatar3))
        self.assertTrue(block.canOverride(self._avatar4))
