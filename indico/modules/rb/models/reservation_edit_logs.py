# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
