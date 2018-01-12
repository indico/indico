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

from indico.core.db import db
from indico.util.string import return_ascii


class Photo(db.Model):
    __tablename__ = 'photos'
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    thumbnail = db.Column(
        db.LargeBinary,
        nullable=True
    )
    data = db.Column(
        db.LargeBinary,
        nullable=True
    )

    # relationship backrefs:
    # - room (Room.photo)

    @return_ascii
    def __repr__(self):
        return u'<Photo({0})>'.format(self.id)
