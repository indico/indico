# This file is part of the CERN Indico plugins.
# Copyright (C) 2014 - 2019 CERN
#
# The CERN Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License; see
# the LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db.sqlalchemy import UTCDateTime, db
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.util.date_time import now_utc


class Notification(db.Model, RenderModeMixin):
    """Notifications sent by Indico to its users"""
    __tablename__ = 'notifications'
    __table_args__ = {'schema': 'indico'}

    possible_render_modes = {RenderMode.markdown, RenderMode.html, RenderMode.plain_text}
    default_render_mode = RenderMode.plain_text

    #: Entry ID (mainly used to sort by insertion order)
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: ID of the user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    #: subject of the message
    subject = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    #: the timestamp when the notification was created
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        index=True,
        default=now_utc
    )
    #: the timestamp when the notification was sent
    sent_dt = db.Column(
        UTCDateTime,
        index=True
    )

    #: the user associated with the notification
    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'notifications',
            lazy='dynamic'
        )
    )

    @declared_attr
    def _body(cls):
        return db.Column(
            'body',
            db.Text,
            nullable=False,
            default=''
        )

    #: message body
    body = RenderModeMixin.create_hybrid_property('_body')
