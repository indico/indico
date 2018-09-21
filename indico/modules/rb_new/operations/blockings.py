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

from __future__ import unicode_literals

from collections import defaultdict
from datetime import date

from flask import session
from sqlalchemy.orm import contains_eager

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.groups import GroupProxy
from indico.modules.rb.models.blocked_rooms import BlockedRoom, BlockedRoomState
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.blockings import notify_request
from indico.modules.users.models.users import User
from indico.util.struct.iterables import group_list


def get_room_blockings(timeframe=None, created_by=None, in_rooms_owned_by=None):
    query = (Blocking.query
             .join(Blocking.blocked_rooms)
             .join(BlockedRoom.room)
             .options(contains_eager('blocked_rooms').contains_eager('room')))

    criteria = []
    if timeframe == 'recent':
        criteria.append(Blocking.end_date >= date.today())
    elif timeframe == 'year':
        criteria.extend([Blocking.start_date <= date(date.today().year, 12, 31),
                         Blocking.end_date >= date(date.today().year, 1, 1)])
    if created_by:
        criteria.append(Blocking.created_by_user == created_by)
    if in_rooms_owned_by:
        criteria.append(Room.owner == in_rooms_owned_by)

    query = query.filter(db.and_(*criteria))
    return query.all()


def get_rooms_blockings(rooms, start_date, end_date):
    room_ids = [room.id for room in rooms]
    query = (BlockedRoom.query
             .filter(BlockedRoom.room_id.in_(room_ids),
                     BlockedRoom.state == BlockedRoomState.accepted,
                     Blocking.start_date <= end_date,
                     Blocking.end_date >= start_date)
             .join(BlockedRoom.blocking)
             .options(contains_eager('blocking')))
    return group_list(query, key=lambda obj: obj.room_id)


def _group_id_or_name(principal):
    provider = principal['provider']
    if provider is None or provider == 'indico':
        return principal['id']
    else:
        return principal['name']


@no_autoflush
def _populate_blocking(blocking, room_ids, allowed_principals, reason):
    blocking.blocked_rooms = [BlockedRoom(room_id=room.id) for room in Room.query.filter(Room.id.in_(room_ids))]
    blocking.reason = reason
    blocking.allowed = [GroupProxy(_group_id_or_name(pr), provider=pr['provider'])
                        if pr.get('is_group')
                        else User.get_one(pr['id'])
                        for pr in allowed_principals]


def create_blocking(room_ids, allowed_principals, start_date, end_date, reason, created_by):
    blocking = Blocking()
    blocking.start_date = start_date
    blocking.end_date = end_date
    blocking.created_by_user = created_by
    _populate_blocking(blocking, room_ids, allowed_principals, reason)
    db.session.add(blocking)
    db.session.flush()
    return blocking


def update_blocking(blocking, room_ids, allowed_principals, reason):
    _populate_blocking(blocking, room_ids, allowed_principals, reason)
    db.session.flush()


def approve_or_request_blocking(blocking):
    rooms_by_owner = defaultdict(list)
    for blocked_room in blocking.blocked_rooms:
        owner = blocked_room.room.owner
        if owner == session.user:
            blocked_room.approve(notify_blocker=False)
        else:
            rooms_by_owner[owner].append(blocked_room)

    for owner, rooms in rooms_by_owner.iteritems():
        notify_request(owner, blocking, rooms)


def get_blocked_rooms(start_dt, end_dt, states=None):
    query = (Room.query
             .join(Room.blocked_rooms)
             .join(BlockedRoom.blocking)
             .filter(db_dates_overlap(Blocking, 'start_date', start_dt, 'end_date', end_dt)))

    if states:
        query = query.filter(BlockedRoom.state.in_(states))
    return query.all()
