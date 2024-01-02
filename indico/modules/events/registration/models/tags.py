# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.string import format_repr


class RegistrationTag(db.Model):
    """Registration tag used to mark/filter registrations."""

    __tablename__ = 'tags'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_tags_title_lower', cls.event_id, db.func.lower(cls.title), unique=True),
                {'schema': 'event_registration'})

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event where this tag was created
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: Tag name
    title = db.Column(
        db.String,
        nullable=False
    )
    #: Tag color (hex)
    color = db.Column(
        db.String,
        nullable=False
    )
    #: The Event where this tag was created
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'registration_tags',
            lazy=True,
            cascade='all, delete-orphan',
        )
    )

    # relationship backrefs:
    # - registrations (Registration.tags)

    @property
    def locator(self):
        return dict(self.event.locator, tag_id=self.id)

    def __repr__(self):
        return format_repr(self, 'id', 'event_id', _text=self.title)
