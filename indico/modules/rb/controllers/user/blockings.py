# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict
from datetime import date

from flask import flash, redirect, request, session
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.forms.blockings import BlockingForm, CreateBlockingForm
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.blockings import notify_request
from indico.modules.rb.views.user.blockings import (WPRoomBookingBlockingDetails, WPRoomBookingBlockingForm,
                                                    WPRoomBookingBlockingList, WPRoomBookingBlockingsForMyRooms)
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHRoomBookingBlockingDetails(RHRoomBookingBase):
    def _process_args(self):
        self._blocking = Blocking.get(request.view_args['blocking_id'])
        if not self._blocking:
            raise NotFound('A blocking with this ID does not exist.')

    def _process(self):
        return WPRoomBookingBlockingDetails(self, blocking=self._blocking).display()


class RHRoomBookingCreateModifyBlockingBase(RHRoomBookingBase):
    def _process(self):
        if self._form.validate_on_submit():
            self._save()
            return redirect(url_for('rooms.blocking_details', blocking_id=str(self._blocking.id)))
        return WPRoomBookingBlockingForm(self, form=self._form, errors=self._form.error_list,
                                         blocking=self._blocking).display()

    def _process_blocked_rooms(self, blocked_rooms):
        rooms_by_owner = defaultdict(list)
        for blocked_room in blocked_rooms:
            owner = blocked_room.room.owner
            if owner == session.user:
                blocked_room.approve(False)
                flash(_(u"Blocking for your room '{0}' has been accepted automatically").format(
                    blocked_room.room.full_name), 'info')
            else:
                rooms_by_owner[owner].append(blocked_room)

        for owner, rooms in rooms_by_owner.iteritems():
            notify_request(owner, self._blocking, rooms)


class RHRoomBookingCreateBlocking(RHRoomBookingCreateModifyBlockingBase):
    def _process_args(self):
        self._form = CreateBlockingForm(start_date=date.today(), end_date=date.today())
        self._blocking = None

    def _save(self):
        self._blocking = blocking = Blocking()
        blocking.start_date = self._form.start_date.data
        blocking.end_date = self._form.end_date.data
        blocking.created_by_user = session.user
        blocking.reason = self._form.reason.data
        blocking.allowed = self._form.principals.data
        blocking.blocked_rooms = [BlockedRoom(room_id=room_id) for room_id in self._form.blocked_rooms.data]
        db.session.add(blocking)
        db.session.flush()  # synchronizes relationships (e.g. BlockedRoom.room)
        flash(_(u'Blocking created'), 'success')
        self._process_blocked_rooms(blocking.blocked_rooms)


class RHRoomBookingModifyBlocking(RHRoomBookingCreateModifyBlockingBase):
    def _process_args(self):
        self._blocking = Blocking.get(request.view_args['blocking_id'])
        if self._blocking is None:
            raise NotFound('A blocking with this ID does not exist.')
        defaults = FormDefaults(self._blocking, attrs={'reason'},
                                principals=self._blocking.allowed,
                                blocked_rooms=[br.room_id for br in self._blocking.blocked_rooms])
        self._form = BlockingForm(obj=defaults)
        self._form._blocking = self._blocking

    def _check_access(self):
        RHRoomBookingCreateModifyBlockingBase._check_access(self)
        if not self._blocking.can_be_modified(session.user):
            raise Forbidden(_("You are not authorized to modify this blocking."))

    def _save(self):
        blocking = self._blocking
        blocking.reason = self._form.reason.data
        # Update the ACL. We don't use `=` here to prevent SQLAlchemy
        # from deleting and re-adding unchanged entries.
        blocking.allowed |= self._form.principals.data
        blocking.allowed &= self._form.principals.data
        # Add/remove blocked rooms if necessary
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
        flash(_(u'Blocking updated'), 'success')
        self._process_blocked_rooms(added_blocked_rooms)


class RHRoomBookingDeleteBlocking(RHRoomBookingBase):
    def _process_args(self):
        self._block = Blocking.get(request.view_args['blocking_id'])
        if not self._block:
            raise NotFound('A blocking with this ID does not exist.')

    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self._block.can_be_deleted(session.user):
            raise Forbidden('You are not authorized to delete this blocking.')

    def _process(self):
        db.session.delete(self._block)
        flash(_(u'Blocking deleted'), 'success')
        return redirect(url_for('rooms.blocking_list', only_mine=True, timeframe='recent'))


class RHRoomBookingBlockingList(RHRoomBookingBase):
    def _process_args(self):
        self.only_mine = request.args.get('only_mine') == '1'
        self.timeframe = request.args.get('timeframe', 'recent')
        if self.timeframe not in {'all', 'year', 'recent'}:
            self.timeframe = 'recent'

    def _process(self):
        criteria = []
        if self.only_mine:
            criteria += [Blocking.created_by_user == session.user]
        if self.timeframe == 'year':
            criteria += [Blocking.start_date <= date(date.today().year, 12, 31),
                         Blocking.end_date >= date(date.today().year, 1, 1)]
        elif self.timeframe == 'recent':
            criteria += [Blocking.end_date >= date.today()]

        blockings = (Blocking
                     .find(*criteria)
                     .options(joinedload('blocked_rooms').joinedload('room'))
                     .order_by(Blocking.start_date.desc())
                     .all())
        return WPRoomBookingBlockingList(self, blockings=blockings).display()


class RHRoomBookingBlockingsForMyRooms(RHRoomBookingBase):
    def _process_args(self):
        self.state = request.args.get('state')

    def _process(self):
        state = BlockedRoom.State.get(self.state)
        my_blocks = defaultdict(list)
        for room in Room.get_owned_by(session.user):
            roomBlocks = room.blocked_rooms.filter(True if state is None else BlockedRoom.state == state).all()
            if roomBlocks:
                my_blocks[room] += roomBlocks
        return WPRoomBookingBlockingsForMyRooms(self, room_blocks=my_blocks).display()
