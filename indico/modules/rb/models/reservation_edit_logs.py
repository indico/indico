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

from sqlalchemy.dialects.postgresql import ARRAY

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class ReservationEditLog(db.Model):
    __tablename__ = 'reservation_edit_logs'
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    timestamp = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    info = db.Column(
        ARRAY(db.String),
        nullable=False
    )
    user_name = db.Column(
        db.String,
        nullable=False
    )
    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.reservations.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - reservation (Reservation.edit_logs)

    @return_ascii
    def __repr__(self):
        return u'<ReservationEditLog({0}, {1}, {2}, {3})>'.format(
            self.user_name,
            self.reservation_id,
            self.timestamp,
            self.info
        )
