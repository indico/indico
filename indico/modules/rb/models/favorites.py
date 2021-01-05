# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db


favorite_room_table = db.Table(
    'favorite_rooms',
    db.metadata,
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    db.Column(
        'room_id',
        db.Integer,
        db.ForeignKey('roombooking.rooms.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='roombooking'
)
