# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.util.string import return_ascii
from indico.util.user import retrieve_principal


class BlockingPrincipal(db.Model):
    __tablename__ = 'blocking_principals'
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    blocking_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.blockings.id'),
        nullable=False
    )
    _principal = db.Column(
        'principal',
        JSON,
        nullable=False
    )

    @property
    def entity(self):
        return retrieve_principal(self._principal, legacy=True)

    @property
    def principal(self):
        return retrieve_principal(self._principal, legacy=False)

    @principal.setter
    def principal(self, value):
        self._principal = value.as_principal

    @property
    def entity_name(self):
        return 'User' if self._principal[0] in {'Avatar', 'User'} else 'Group'

    @return_ascii
    def __repr__(self):
        return u'<BlockingPrincipal({}, {}, {})>'.format(
            self.id,
            self.blocking_id,
            self.principal
        )
