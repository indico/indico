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
Generic custom attribute holder for rooms and reservations (key, name, desc)
"""

from sqlalchemy import Table, Column, String, Integer, ForeignKey

from indico.core.db.schema import Base


traits_rooms = Table('traits_rooms', Base.metadata,
                     Column('trait_id', Integer, ForeignKey('traits.id'), primary_key=True),
                     Column('room_id', Integer, ForeignKey('rooms.id'), primary_key=True))


traits_reservations = Table('traits_reservations', Base.metadata,
                            Column('trait_id', Integer, ForeignKey('traits.id'), primary_key=True),
                            Column('reservation_id', Integer, ForeignKey('reservations.id'), primary_key=True))


class Trait(Base):
    __tablename__ = 'traits'

    # easier with single column pk
    # due to multi-associations with this table
    # but pk composed of (key, name) is also possible
    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
