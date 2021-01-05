# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
