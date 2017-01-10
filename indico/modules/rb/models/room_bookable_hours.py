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

from datetime import time

from indico.core.db import db
from indico.util.string import return_ascii


class BookableHours(db.Model):
    __tablename__ = 'room_bookable_hours'
    __table_args__ = {'schema': 'roombooking'}

    start_time = db.Column(
        db.Time,
        nullable=False,
        primary_key=True
    )
    end_time = db.Column(
        db.Time,
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
    # - room (Room.bookable_hours)

    @return_ascii
    def __repr__(self):
        return u'<BookableHours({0}, {1}, {2})>'.format(
            self.room_id,
            self.start_time,
            self.end_time
        )

    def fits_period(self, st, et):
        st = _tuplify(st, False)
        et = _tuplify(et, True)
        period_st = _tuplify(self.start_time, False)
        period_et = _tuplify(self.end_time, True)
        return period_st <= st and period_et >= et


def _tuplify(t, end):
    if end and t == time(0):
        return 24, 0
    return t.hour, t.minute
