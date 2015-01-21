# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.ext.hybrid import hybrid_method

from indico.core.db import db
from indico.util.string import return_ascii


class NonBookablePeriod(db.Model):
    __tablename__ = 'room_nonbookable_periods'
    __table_args__ = {'schema': 'roombooking'}

    start_dt = db.Column(
        db.DateTime,
        nullable=False,
        primary_key=True
    )
    end_dt = db.Column(
        db.DateTime,
        nullable=False,
        primary_key=True
    )
    room_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.rooms.id'),
        primary_key=True,
        nullable=False
    )

    # relationship backrefs:
    # - room (Room.nonbookable_periods)

    @return_ascii
    def __repr__(self):
        return u'<NonBookablePeriod({0}, {1}, {2})>'.format(
            self.room_id,
            self.start_dt,
            self.end_dt
        )

    @hybrid_method
    def overlaps(self, st, et):
        return (self.start_dt < et) & (self.end_dt > st)
