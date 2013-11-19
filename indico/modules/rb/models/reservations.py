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
Schema of a reservation
"""

from sqlalchemy.ext.hybrid import hybrid_property

from datetime import datetime

from indico.core.db import db


class RepeatUnit(object):
    NEVER, HOUR, DAY, WEEK, MONTH, YEAR = xrange(6)


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)

    # dates
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    repeat_unit = db.Column(db.SmallInteger, nullable=False, default=0)  # week, month, year, etc.
    repeat_step = db.Column(db.SmallInteger, nullable=False, default=0)  # 1, 2, 3, etc.

    # user
    booked_for_id = db.Column(db.String, nullable=False)
    booked_for_name = db.Column(db.String, nullable=False)
    created_by = db.Column(db.String, nullable=False)

    # room
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)

    # reservation specific
    contact_email = db.Column(db.String)
    contact_phone = db.Column(db.String)

    is_confirmed = db.Column(db.Boolean, nullable=False)
    is_cancelled = db.Column(db.Boolean, nullable=False, default=False)
    is_rejected = db.Column(db.Boolean, nullable=False, default=False)

    reason = db.Column(db.String, nullable=False)

    edit_logs = db.relationship('ReservationEditLog',
                                backref='reservation',
                                cascade='all, delete-orphan')

    attributes = db.relationship('ReservationAttribute',
                                 backref='reservation',
                                 cascade='all, delete-orphan')

    excluded_dates = db.relationship('ExcludedDay',
                                     backref=db.backref('reservation', order_by='ExcludedDay.start_date'),
                                     cascade='all, delete-orphan')

    notifications = db.relationship('ReservationNotification',
                                    backref='reservation',
                                    cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return '<Reservation({0}, {1}, {2}, {3}, {4})>'.format(self.id, self.room_id,
                                                               self.booked_for_name,
                                                               self.start_date,
                                                               self.end_date)
    @hybrid_property
    def is_live(self):
        return self.end_date >= datetime.utcnow()

    def addEditLog(self, edit_log):
        self.edit_logs.append(edit_log)

    def removeEditLog(self, edit_log):
        self.edit_logs.remove(edit_log)

    def clearEditLogs(self):
        del self.edit_logs[:]

    def addExcludedDate(self, excluded_date):
        self.excluded_dates.append(excluded_date)

    def removeExcludedDate(self, excluded_date):
        self.excluded_dates.remove(excluded_date)

    def clearExcludedDates(self):
        del self.excluded_dates[:]
