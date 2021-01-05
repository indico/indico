# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import defaultdict
from datetime import date
from operator import attrgetter

from flask import session
from sqlalchemy.orm import contains_eager, selectinload

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.rb.models.blocked_rooms import BlockedRoom, BlockedRoomState
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.blockings import notify_request
from indico.modules.rb.operations.rooms import get_managed_room_ids
from indico.util.struct.iterables import group_list


def get_room_blockings(timeframe=None, created_by=None, in_rooms_owned_by=None):
    query = (Blocking.query
             .join(Blocking.blocked_rooms)
             .join(BlockedRoom.room)
             .options(contains_eager('blocked_rooms').contains_eager('room'),
                      selectinload('_allowed')))

    criteria = []
    if timeframe == 'recent':
        criteria.append(Blocking.end_date >= date.today())
    elif timeframe == 'year':
        criteria.extend([Blocking.start_date <= date(date.today().year, 12, 31),
                         Blocking.end_date >= date(date.today().year, 1, 1)])
    if created_by:
        criteria.append(Blocking.created_by_user == created_by)
    if in_rooms_owned_by:
        criteria.append(BlockedRoom.room_id.in_(get_managed_room_ids(in_rooms_owned_by)))

    query = query.filter(db.and_(*criteria))
    return query.all()


def filter_blocked_rooms(blocked_rooms, overridable_only=False, nonoverridable_only=False, explicit=False):
    if overridable_only:
        blocked_rooms = [room for room in blocked_rooms
                         if room.blocking.can_override(session.user, room=room.room, explicit_only=explicit)]
    if nonoverridable_only:
        blocked_rooms = [room for room in blocked_rooms
                         if not room.blocking.can_override(session.user, room=room.room, explicit_only=explicit)]
    return blocked_rooms


def group_blocked_rooms(blocked_rooms):
    return group_list(blocked_rooms, key=attrgetter('room_id'))


def get_blockings_with_rooms(start_date, end_date):
    return (BlockedRoom.query
            .filter(BlockedRoom.state == BlockedRoomState.accepted,
                    Blocking.start_date <= end_date,
                    Blocking.end_date >= start_date)
            .join(BlockedRoom.blocking)
            .join(BlockedRoom.room)
            .options(contains_eager('blocking'), contains_eager('room'))
            .all())


def get_rooms_blockings(rooms, start_date, end_date):
    room_ids = [room.id for room in rooms]
    return (BlockedRoom.query
            .filter(BlockedRoom.room_id.in_(room_ids),
                    BlockedRoom.state == BlockedRoomState.accepted,
                    Blocking.start_date <= end_date,
                    Blocking.end_date >= start_date)
            .join(BlockedRoom.blocking)
            .options(contains_eager('blocking'))
            .all())


@no_autoflush
def _populate_blocking(blocking, room_ids, allowed, reason):
    blocking.reason = reason
    blocking.allowed = allowed
    # We don't use `=` here to prevent SQLAlchemy from deleting and re-adding unchanged entries
    blocking.allowed |= allowed  # add new
    blocking.allowed &= allowed  # remove deleted
    _update_blocked_rooms(blocking, room_ids)


def _update_blocked_rooms(blocking, room_ids):
    old_blocked = {br.room_id for br in blocking.blocked_rooms}
    new_blocked = set(room_ids)
    added_blocks = new_blocked - old_blocked
    removed_blocks = old_blocked - new_blocked
    blocked_rooms_by_room = {br.room_id: br for br in blocking.blocked_rooms}
    for room_id in removed_blocks:
        blocking.blocked_rooms.remove(blocked_rooms_by_room[room_id])
    added_blocked_rooms = set()
    rooms = {r.id: r for r in Room.query.filter(~Room.is_deleted, Room.id.in_(added_blocks))}
    for room_id in added_blocks:
        blocked_room = BlockedRoom(room=rooms[room_id])
        blocking.blocked_rooms.append(blocked_room)
        added_blocked_rooms.add(blocked_room)
    db.session.flush()
    _approve_or_request_rooms(blocking, added_blocked_rooms)


def _approve_or_request_rooms(blocking, blocked_rooms=None):
    if blocked_rooms is None:
        blocked_rooms = set(blocking.blocked_rooms)
    rooms_by_owner = defaultdict(list)
    for blocked_room in blocked_rooms:
        if blocked_room.room.can_manage(session.user, allow_admin=False):
            blocked_room.approve(notify_blocker=False)
        else:
            # TODO: notify all managers of a room?
            rooms_by_owner[blocked_room.room.owner].append(blocked_room)
    for owner, rooms in rooms_by_owner.iteritems():
        notify_request(owner, blocking, rooms)


def create_blocking(room_ids, allowed, start_date, end_date, reason, created_by):
    blocking = Blocking()
    blocking.start_date = start_date
    blocking.end_date = end_date
    blocking.created_by_user = created_by
    _populate_blocking(blocking, room_ids, allowed, reason)
    db.session.add(blocking)
    db.session.flush()
    return blocking


def update_blocking(blocking, room_ids, allowed, reason):
    _populate_blocking(blocking, room_ids, allowed, reason)
    db.session.flush()


def get_blocked_rooms(start_dt, end_dt, states=None):
    query = (Room.query
             .join(Room.blocked_rooms)
             .join(BlockedRoom.blocking)
             .filter(db_dates_overlap(Blocking, 'start_date', start_dt, 'end_date', end_dt)))

    if states:
        query = query.filter(BlockedRoom.state.in_(states))
    return query.all()
