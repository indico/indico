# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from indico.modules.rb.controllers import RHRoomBookingBase


class RHRoomBookingBlockingDetails(RHRoomBookingBase):

    def _checkParams(self, params):
        blockId = int(params.get('blockingId'))
        self._block = RoomBlockingBase.getById(blockId)
        if not self._block:
            raise MaKaCError('A blocking with this ID does not exist.')

    def _process(self):
        p = roomBooking_wp.WPRoomBookingBlockingDetails(self, self._block)
        return p.display()


class RHRoomBookingBlockingForm(RHRoomBookingBase):

    def _checkParams(self, params):

        self._action = params.get('action')
        blockId = params.get('blockingId')
        if blockId is not None:
            self._block = RoomBlockingBase.getById(int(blockId))
            if not self._block:
                raise MaKaCError('A blocking with this ID does not exist.')
        else:
            self._block = Factory.newRoomBlocking()()
            self._block.startDate = date.today()
            self._block.endDate = date.today()

        self._hasErrors = False
        if self._action == 'save':
            from MaKaC.services.interface.rpc import json
            self._reason = params.get('reason', '').strip()
            allowedUsers = json.decode(params.get('allowedUsers', '[]'))
            blockedRoomGuids = json.decode(params.get('blockedRooms', '[]'))
            startDate = params.get('startDate')
            endDate = params.get('endDate')
            if startDate and endDate:
                self._startDate = parseDate(startDate)
                self._endDate = parseDate(endDate)
            else:
                self._startDate = self._endDate = None

            self._blockedRooms = [RoomGUID.parse(guid).getRoom() for guid in blockedRoomGuids]
            self._allowedUsers = [RoomBlockingPrincipal.getByTypeId(fossil['_type'], fossil['id']) for fossil in allowedUsers]

            if not self._reason or not self._blockedRooms:
                self._hasErrors = True
            elif self._createNew and (not self._startDate or not self._endDate or self._startDate > self._endDate):
                self._hasErrors = True

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        if not self._doProcess: # if we are not logged in
            return
        if not self._createNew:
            if not self._block.canModify(self._getUser()):
                raise MaKaCError("You are not authorized to modify this blocking.")
        else:
            if not (Room.isAvatarResponsibleForRooms(self._getUser()) or self._getUser().isAdmin() or self._getUser().isRBAdmin()):
                raise MaKaCError("Only users who own at least one room are allowed to create blockings.")

    def _process(self):
        if self._action == 'save' and not self._hasErrors:
            self._block.message = self._reason
            if self._createNew:
                self._block.createdByUser = self._getUser()
                self._block.startDate = self._startDate
                self._block.endDate = self._endDate
            currentBlockedRooms = set()
            for room in self._blockedRooms:
                br = self._block.getBlockedRoom(room)
                if not br:
                    br = BlockedRoom(room)
                    self._block.addBlockedRoom(br)
                    if room.getResponsible() == self._getUser():
                        br.approve(sendNotification=False)
                currentBlockedRooms.add(br)
            # Remove blocked rooms which have been removed from the list
            for br in set(self._block.blockedRooms) - currentBlockedRooms:
                self._block.delBlockedRoom(br)
            # Replace allowed-users/groups list
            self._block.allowed = self._allowedUsers
            # Insert/update(re-index) the blocking
            if self._createNew:
                self._block.insert()
            else:
                self._block.update()
            self._redirect(urlHandlers.UHRoomBookingBlockingsBlockingDetails.getURL(self._block))

        elif self._action == 'save' and self._createNew and self._hasErrors:
            # If we are creating a new blocking and there are errors, populate the block object anyway to preserve the entered values
            self._block.message = self._reason
            self._block.startDate = self._startDate
            self._block.endDate = self._endDate
            self._block.allowed = self._allowedUsers
            for room in self._blockedRooms:
                self._block.addBlockedRoom(BlockedRoom(room))

        p = roomBooking_wp.WPRoomBookingBlockingForm(self, self._block, self._hasErrors)
        return p.display()

    @property
    def _createNew(self):
        return self._block.id is None


class RHRoomBookingDelete(RHRoomBookingBase):

    def _checkParams(self, params):
        blockId = int(params.get('blockingId'))
        self._block = RoomBlockingBase.getById(blockId)

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        if not self._block.canDelete(self._getUser()):
            raise MaKaCError("You are not authorized to delete this blocking.")

    def _process(self):
        self._block.remove()
        self._redirect(urlHandlers.UHRoomBookingBlockingList.getURL(onlyMine=True, onlyRecent=True))


class RHRoomBookingBlockingList(RHRoomBookingBase):

    def _checkParams(self, params):
        self.onlyMine = 'onlyMine' in params
        self.onlyRecent = 'onlyRecent' in params
        self.onlyThisYear = 'onlyThisYear' in params

    def _process(self):
        if self.onlyMine:
            blocks = RoomBlockingBase.getByOwner(self._getUser())
            if self.onlyThisYear:
                firstDay = date(date.today().year, 1, 1)
                lastDay = date(date.today().year, 12, 31)
                blocks = [block for block in blocks if block.startDate <= lastDay and firstDay <= block.endDate]
        elif self.onlyThisYear:
            blocks = RoomBlockingBase.getByDateSpan(date(date.today().year, 1, 1), date(date.today().year, 12, 31))
            if self.onlyMine:
                blocks = [block for block in blocks if block.createdByUser == self._getUser()]
        else:
            blocks = RoomBlockingBase.getAll()

        if self.onlyRecent:
            blocks = [block for block in blocks if date.today() <= block.endDate]
        p = roomBooking_wp.WPRoomBookingBlockingList(self, blocks)
        return p.display()


class RHRoomBookingBlockingsForMyRooms(RHRoomBookingBase):

    def _checkParams(self, params):
        self.filterState = params.get('filterState')

    def _process(self):
        activeState = -1
        if self.filterState == 'pending':
            activeState = None
        elif self.filterState == 'accepted':
            activeState = True
        elif self.filterState == 'rejected':
            activeState = False
        myRoomBlocks = defaultdict(list)
        for room in self._getUser().getRooms():
            roomBlocks = RoomBlockingBase.getByRoom(room, activeState)
            if roomBlocks:
                myRoomBlocks[str(room.guid)] += roomBlocks
        p = roomBooking_wp.WPRoomBookingBlockingsForMyRooms(self, myRoomBlocks)
        return p.display()
