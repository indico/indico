# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db


_paper_judges = db.Table(
    'judges',
    db.metadata,
    db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_paper_reviewing'
)


_paper_content_reviewers = db.Table(
    'content_reviewers',
    db.metadata,
    db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_paper_reviewing'
)


_paper_layout_reviewers = db.Table(
    'layout_reviewers',
    db.metadata,
    db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_paper_reviewing'
)
