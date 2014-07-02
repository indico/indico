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

from collections import defaultdict
from datetime import date

from flask import request, session

from indico.modules.rb.forms.base import FormDefaults
from indico.modules.rb.forms.blockings import CreateBlockingForm, BlockingForm
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.notifications.blockings import request_confirmation
from indico.util.i18n import _
from indico.core.db import db
from indico.core.errors import IndicoError
from indico.web.flask.util import url_for
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.views.user.blockings import (WPRoomBookingBlockingList, WPRoomBookingBlockingDetails,
                                                    WPRoomBookingBlockingsForMyRooms, WPRoomBookingBlockingForm)
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification


class RHRoomBookingBlockingDetails(RHRoomBookingBase):
    def _checkParams(self):
        self._blocking = Blocking.get(request.view_args['blocking_id'])
        if not self._blocking:
            raise IndicoError('A blocking with this ID does not exist.')

    def _process(self):
        return WPRoomBookingBlockingDetails(self, blocking=self._blocking).display()


class RHRoomBookingCreateModifyBlockingBase(RHRoomBookingBase):
    def _process(self):
        if self._form.validate_on_submit():
            self._save()
            self._redirect(url_for('rooms.blocking_details', blocking_id=str(self._blocking.id)))
        else:
            return WPRoomBookingBlockingForm(self, form=self._form, errors=self._form.error_list,
                                             blocking=self._blocking).display()

    def _process_blocked_rooms(self, blocked_rooms):
        rooms_by_owner = defaultdict(list)
        for blocked_room in blocked_rooms:
            owner = blocked_room.room.getResponsible()
            if owner == session.user:
                blocked_room.approve(False)
            else:
                rooms_by_owner[owner].append(blocked_room)

        for owner, rooms in rooms_by_owner.iteritems():
            GenericMailer.send(GenericNotification(request_confirmation(owner, self._blocking, rooms)))


class RHRoomBookingCreateBlocking(RHRoomBookingCreateModifyBlockingBase):
    def _checkParams(self):
        self._form = CreateBlockingForm(start_date=date.today(), end_date=date.today())
        self._blocking = None

    def _checkProtection(self):
        RHRoomBookingCreateModifyBlockingBase._checkProtection(self)
        if not self._doProcess:  # we are not logged in
            return

    def _save(self):
        self._blocking = blocking = Blocking()
        blocking.start_date = self._form.start_date.data
        blocking.end_date = self._form.end_date.data
        blocking.created_by_user = session.user
        blocking.reason = self._form.reason.data
        blocking.allowed = [BlockingPrincipal(entity_type=item['_type'], entity_id=item['id'])
                            for item in self._form.principals.data]
        blocking.blocked_rooms = [BlockedRoom(room_id=room_id) for room_id in self._form.blocked_rooms.data]
        db.session.add(blocking)
        db.session.flush()  # synchronizes relationships (e.g. BlockedRoom.room)
        self._process_blocked_rooms(blocking.blocked_rooms)


class RHRoomBookingModifyBlocking(RHRoomBookingCreateModifyBlockingBase):
    def _checkParams(self):
        self._blocking = Blocking.get(request.view_args['blocking_id'])
        if self._blocking is None:
            raise IndicoError('A blocking with this ID does not exist.')
        defaults = FormDefaults(self._blocking, attrs={'reason'},
                                principals=[p.entity.fossilize() for p in self._blocking.allowed],
                                blocked_rooms=[br.room_id for br in self._blocking.blocked_rooms])
        self._form = BlockingForm(obj=defaults)
        self._form._blocking = self._blocking

    def _checkProtection(self):
        RHRoomBookingCreateModifyBlockingBase._checkProtection(self)
        if not self._doProcess:  # we are not logged in
            return
        if not self._blocking.can_be_modified(self._getUser()):
            raise IndicoError(_("You are not authorized to modify this blocking."))

    def _save(self):
        blocking = self._blocking
        blocking.reason = self._form.reason.data
        # Just overwrite the whole list
        blocking.allowed = [BlockingPrincipal(entity_type=item['_type'], entity_id=item['id'])
                            for item in self._form.principals.data]
        # Blocked rooms need some more work as we can't just overwrite them
        old_blocked = {br.room_id for br in blocking.blocked_rooms}
        new_blocked = set(self._form.blocked_rooms.data)
        added_blocks = new_blocked - old_blocked
        removed_blocks = old_blocked - new_blocked
        for room_id in removed_blocks:
            blocked_room = next(br for br in blocking.blocked_rooms if br.room_id == room_id)
            blocking.blocked_rooms.remove(blocked_room)
        added_blocked_rooms = []
        for room_id in added_blocks:
            blocked_room = BlockedRoom(room_id=room_id)
            blocking.blocked_rooms.append(blocked_room)
            added_blocked_rooms.append(blocked_room)
        db.session.flush()
        self._process_blocked_rooms(added_blocked_rooms)


class RHRoomBookingDeleteBlocking(RHRoomBookingBase):
    def _checkParams(self):
        self._block = Blocking.get(request.view_args['blocking_id'])
        if not self._block:
            raise IndicoError('A blocking with this ID does not exist.')

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        if not self._block.can_be_deleted(self._getUser()):
            raise IndicoError('You are not authorized to delete this blocking.')

    def _process(self):
        db.session.delete(self._block)
        self._redirect(url_for('rooms.blocking_list', only_mine=True, timeframe='recent'))


class RHRoomBookingBlockingList(RHRoomBookingBase):
    def _checkParams(self):
        self.only_mine = request.args.get('only_mine') == '1'
        self.timeframe = request.args.get('timeframe', 'recent')
        if self.timeframe not in {'all', 'year', 'recent'}:
            self.timeframe = 'recent'

    def _process(self):
        criteria = []
        if self.only_mine:
            criteria += [Blocking.created_by == self._getUser().getId()]
        if self.timeframe == 'year':
            criteria += [Blocking.start_date <= date(date.today().year, 12, 31),
                         Blocking.end_date >= date(date.today().year, 1, 1)]
        elif self.timeframe == 'recent':
            criteria += [Blocking.end_date >= date.today()]

        blockings = Blocking.find(*criteria).order_by(Blocking.start_date.desc()).all()
        return WPRoomBookingBlockingList(self, blockings=blockings).display()


class RHRoomBookingBlockingsForMyRooms(RHRoomBookingBase):
    def _checkParams(self):
        self.state = request.args.get('state')

    def _process(self):
        state = BlockedRoom.State.get(self.state)
        my_blocks = defaultdict(list)
        for room in self._getUser().getRooms():
            roomBlocks = room.blocked_rooms.filter(True if state is None else BlockedRoom.state == state).all()
            if roomBlocks:
                my_blocks[room] += roomBlocks
        return WPRoomBookingBlockingsForMyRooms(self, room_blocks=my_blocks).display()
