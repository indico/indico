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

from indico.core.db.sqlalchemy import db


_reviewed_for_tracks = db.Table(
    'reviewed_for_tracks',
    db.metadata,
    db.Column(
        'abstract_id',
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'track_id',
        db.Integer,
        db.ForeignKey('events.tracks.id', ondelete='CASCADE'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_abstracts'
)

_submitted_for_tracks = db.Table(
    'submitted_for_tracks',
    db.metadata,
    db.Column(
        'abstract_id',
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'track_id',
        db.Integer,
        db.ForeignKey('events.tracks.id', ondelete='CASCADE'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_abstracts'
)

_proposed_for_tracks = db.Table(
    'proposed_for_tracks',
    db.metadata,
    db.Column(
        'review_id',
        db.Integer,
        db.ForeignKey('event_abstracts.abstract_reviews.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'track_id',
        db.Integer,
        db.ForeignKey('events.tracks.id', ondelete='CASCADE'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_abstracts'
)
