# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as pg_UUID

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import format_repr, return_ascii


class StaticListLink(db.Model):
    """Display configuration data used in static links to listing pages.

    This allows users to share links to listing pages in events
    while preserving e.g. column/filter configurations.
    """

    __tablename__ = 'static_list_links'
    __table_args__ = {'schema': 'events'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    type = db.Column(
        db.String,
        nullable=False
    )
    uuid = db.Column(
        pg_UUID,
        index=True,
        unique=True,
        nullable=False,
        default=lambda: unicode(uuid4())
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    last_used_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    data = db.Column(
        JSONB,
        nullable=False
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'static_list_links',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    @classmethod
    def load(cls, event, type_, uuid):
        """Load the data associated with a link.

        :param event: the `Event` the link belongs to
        :param type_: the type of the link
        :param uuid: the UUID of the link
        :return: the link data or ``None`` if the link does not exist
        """
        try:
            UUID(uuid)
        except ValueError:
            return None
        static_list_link = event.static_list_links.filter_by(type=type_, uuid=uuid).first()
        if static_list_link is None:
            return None
        static_list_link.last_used_dt = now_utc()
        return static_list_link.data

    @classmethod
    def create(cls, event, type_, data):
        """Create a new static list link.

        If one exists with the same data, that link is used instead of
        creating a new one.

        :param event: the `Event` for which to create the link
        :param type_: the type of the link
        :param data: the data to associate with the link
        :return: the newly created `StaticListLink`
        """
        static_list_link = event.static_list_links.filter_by(type=type_, data=data).first()
        if static_list_link is None:
            static_list_link = cls(event=event, type=type_, data=data)
        else:
            # bump timestamp in case we start expiring old links
            # in the future
            if static_list_link.last_used_dt is not None:
                static_list_link.last_used_dt = now_utc()
            else:
                static_list_link.created_dt = now_utc()
        db.session.flush()
        return static_list_link

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'uuid')
