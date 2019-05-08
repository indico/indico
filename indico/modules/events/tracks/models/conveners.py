# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db


_track_conveners_table = db.Table(
    'track_conveners',
    db.metadata,
    db.Column(
        'id',
        db.Integer,
        primary_key=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    ),
    db.Column(
        'event_id',
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True
    ),
    db.Column(
        'track_id',
        db.Integer,
        db.ForeignKey('events.tracks.id'),
        index=True
    ),
    db.CheckConstraint('(track_id IS NULL) != (event_id IS NULL)', name='track_xor_event_id_null'),
    schema='events'
)
