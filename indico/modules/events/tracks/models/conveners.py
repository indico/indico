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
