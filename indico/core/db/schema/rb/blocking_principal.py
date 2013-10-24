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
Schema of the user who is responsible for the blocking
"""

from sqlalchemy import Table, Column, String, Integer, ForeignKey

from indico.core.db.schema import Base


principals_blockings = Table('principals_blockings', Base.metadata,
                             Column('blocking_id', Integer, ForeignKey('blockings.id'), primary_key=True),
                             Column('blocking_principal_id', Integer, ForeignKey('blocking_principals.id'), primary_key=True))


class BlockingPrincipal(Base):
    __tablename__ = 'blocking_principals'

    id = Column(Integer, primary_key=True)
    avatar_id = Column(String, nullable=False)
    access_right = Column(String, nullable=False)
