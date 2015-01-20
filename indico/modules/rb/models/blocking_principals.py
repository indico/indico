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

from indico.core.db import db
from indico.util.string import return_ascii
from MaKaC.user import AvatarHolder, GroupHolder


class BlockingPrincipal(db.Model):
    __tablename__ = 'blocking_principals'
    __table_args__ = {'schema': 'roombooking'}

    blocking_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.blockings.id'),
        primary_key=True,
        nullable=False
    )
    entity_type = db.Column(
        db.String,
        primary_key=True,
        nullable=False
    )
    entity_id = db.Column(
        db.String,
        primary_key=True,
        nullable=False
    )

    @property
    def entity(self):
        if self.entity_type == 'Avatar':
            return AvatarHolder().getById(self.entity_id)
        else:  # Group, LDAPGroup
            return GroupHolder().getById(self.entity_id)

    @property
    def entity_name(self):
        return 'User' if self.entity_type == 'Avatar' else 'Group'

    @return_ascii
    def __repr__(self):
        return u'<BlockingPrincipal({0}, {1}, {2})>'.format(
            self.blocking_id,
            self.entity_id,
            self.entity_type
        )
