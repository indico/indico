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
Sent notifications of a reservation
"""

from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db


class ReservationOccurrence(db.Model):
    __tablename__ = 'reservation_occurrence'

    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('reservations.id'),
        nullable=False,
        primary_key=True
    )
    start = db.Column(
        db.DateTime,
        nullable=False,
        primary_key=True
    )
    end = db.Column(
        db.DateTime,
        nullable=False
    )
    is_sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    is_cancelled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    is_rejected = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    def __str__(self):
        return '{} -- {}'.format(self.start, self.end)

    def __repr__(self):
        return '<ReservationOccurrence({0}, {1}, {2}, {3}, {4})>'.format(
            self.reservation_id,
            self.start,
            self.end,
            self.is_cancelled,
            self.is_sent
        )

    @hybrid_property
    def is_same_day(self, d):
        return self.start.date() == d

    @hybrid_property
    def day(self):
        return self.start.date()

    @hybrid_property
    def length(self):
        return (self.end - self.start).total_seconds()
