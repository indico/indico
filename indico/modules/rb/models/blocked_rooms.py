# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

"""
Schema of a blocked room (rejection and notification info about blocking)
"""

from indico.core.db import db


class BlockedRoom(db.Model):
    __tablename__ = 'blocked_rooms'

    is_active = db.Column(db.Boolean, nullable=False, default=False)
    notification_sent = db.Column(db.Boolean, nullable=False, default=False)
    rejected_by = db.Column(db.String)
    rejection_reason = db.Column(db.String)

    blocking_id = db.Column(db.Integer, db.ForeignKey('blockings.id'), primary_key=True, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), primary_key=True, nullable=False)

    def __init__(self, is_active, notification_sent):
        self.is_active = is_active
        self.notification_sent = notification_sent

    def __str__(self):
        return 'Blocking is{0} active on {1}'.format('' if self.is_active else ' not',
                                                     self.room)

    def __repr__(self):
        return '<BlockedRoom({0}, {1}, {2})>'.format(self.blocking_id, self.room_id,
                                                     self.is_active)

    @staticmethod
    def getBlockedRoomById(brid):
        return BlockedRoom.query.get(brid)
