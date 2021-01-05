# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
