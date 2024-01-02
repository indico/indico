# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


favorite_user_table = db.Table(
    'favorite_users',
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
        'target_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='users'
)

favorite_category_table = db.Table(
    'favorite_categories',
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
        'target_id',
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='users'
)

favorite_event_table = db.Table(
    'favorite_events',
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
        'target_id',
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='users'
)
