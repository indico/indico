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
Schema of modifications done on a reservation
"""

from datetime import datetime

from indico.core.db import db


class ReservationEditLog(db.Model):
    __tablename__ = 'reservation_edit_logs'

    timestamp = db.Column(db.DateTime, primary_key=True, nullable=False, default=datetime.utcnow)
    info = db.Column(db.String, nullable=False)
    avatar_id = db.Column(db.String, nullable=False, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), primary_key=True, nullable=False)

    def __init__(self, info, timestamp, avatar_id):
        self.info = info
        self.timestamp = timestamp
        self.avatar_id = avatar_id

    def __str__(self):
        return '{0} by {1} at {2}'.format(self.info, self.avatar_id, self.timestamp)

    def __repr__(self):
        return '<Edit({0}, {1}, {2}, {3})>'.format(self.avatar_id, self.reservation_id,
                                                   self.timestamp, self.info)
