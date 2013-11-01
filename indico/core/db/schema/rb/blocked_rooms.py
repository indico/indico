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

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from indico.core.db.schema import Base


class BlockedRoom(Base):
    __tablename__ = 'blocked_rooms'

    is_active = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    rejected_by = Column(String)
    rejection_reason = Column(String)

    blocking_id = Column(Integer, ForeignKey('blockings.id'), primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), primary_key=True)

    def __repr__(self):
        return '<BlockedRoom({0}, {1}, {2})>'.format(self.blocking_id, self.room_id,
                                                     self.is_active)
