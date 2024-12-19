# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.util.string import format_repr


class UserSession(db.Model):
    __tablename__ = 'sessions'
    __table_args__ = {'schema': 'users'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    sid = db.Column(
        db.String(),
        unique=True,
        nullable=False
    )
    data = db.Column(
        db.LargeBinary,
        nullable=False
    )
    ttl = db.Column(
        db.DateTime,
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False
    )

    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'sessions',
            lazy='dynamic'
        )
    )

    def __repr__(self):
        return format_repr(self, 'sid', 'ttl')
