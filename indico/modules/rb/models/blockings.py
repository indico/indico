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
Schema of a blocking (dates, related rooms and principals)
"""

from datetime import datetime

from indico.core.db import db


class Blocking(db.Model):
    __tablename__ = 'blockings'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    created_by = db.Column(
        db.String,
        nullable=False
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    start_date = db.Column(
        db.DateTime,
        nullable=False
    )
    end_date = db.Column(
        db.DateTime,
        nullable=False
    )
    reason = db.Column(
        db.String,
        nullable=False
    )

    # relationships

    allowed = db.relationship(
        'BlockingPrincipal',
        backref='blocking',
        cascade='all, delete-orphan'
    )
    blocked_rooms = db.relationship(
        'BlockedRoom',
        backref='blocking',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return '<Blocking({0}, {1}, {2}, {3}, {4})>'.format(
            self.id,
            self.created_by,
            self.reason,
            self.start_date,
            self.end_date
        )
