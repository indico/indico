# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import time

from indico.core.db import db
from indico.util.date_time import overlaps
from indico.util.string import format_repr


class BookableHours(db.Model):
    __tablename__ = 'room_bookable_hours'
    __table_args__ = (
        db.CheckConstraint("weekday IN ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')", 'valid_weekdays'),
        db.Index(None, 'room_id', 'start_time', 'end_time', 'weekday', unique=True),
        {'schema': 'roombooking'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    start_time = db.Column(
        db.Time,
        nullable=False,
    )
    end_time = db.Column(
        db.Time,
        nullable=False,
    )
    weekday = db.Column(
        db.String,
        nullable=True,
        default=None
    )  # mon, tue, wed, etc.
    room_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.rooms.id'),
        nullable=False
    )

    # relationship backrefs:
    # - room (Room.bookable_hours)

    def __repr__(self):
        return format_repr(self, 'room_id', 'start_time', 'end_time', weekday=None)

    @property
    def key(self):
        return self.start_time, self.end_time, self.weekday

    def overlaps(self, st, et):
        return overlaps((st, et), (self.start_time, self.end_time))

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
