# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.string import format_repr


class EventSpeakerLink(db.Model):
    __tablename__ = 'speaker_links'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_link_name_lower', cls.event_id, db.func.lower(cls.name), unique=True),
                {'schema': 'events'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    icon = db.Column(
        db.String,
        nullable=False
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'speaker_links',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    def __repr__(self):
        return format_repr(self, 'id', _text=self.name)


class EventSpeakerLinkData(db.Model):
    __tablename__ = 'speaker_link_data'
    __table_args__ = (db.UniqueConstraint('speaker_link_id', 'event_person_id'), {'schema': 'events'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    speaker_link_id = db.Column(
        db.Integer,
        db.ForeignKey('events.speaker_links.id'),
        nullable=False,
        index=True
    )
    event_person_id = db.Column(
        db.Integer,
        db.ForeignKey('events.persons.id'),
        nullable=False,
        index=True
    )
    data = db.Column(db.String, nullable=False)

    speaker_link = db.relationship(
        'EventSpeakerLink',
        lazy=False,
        backref=db.backref(
            'link_data',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    def __repr__(self):
        return format_repr(self, 'id', _text=self.data)
