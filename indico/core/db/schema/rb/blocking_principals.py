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
Schema of a principal (user or group that isn't affected by blocking)
"""

from sqlalchemy import Column, ForeignKey, Integer, String

from indico.core.db.schema import Base


class BlockingPrincipal(Base):
    __tablename__ = 'blocking_principals'

    blocking_id = Column(Integer, ForeignKey('blockings.id'), primary_key=True)
    entity_type = Column(String, primary_key=True)
    entity_id = Column(String, primary_key=True)
