# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class EditingTag(db.Model):
    __tablename__ = 'tags'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_tags_event_id_code_lower', cls.event_id, db.func.lower(cls.code), unique=True),
                {'schema': 'event_editing'})

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
    title = db.Column(
        db.String,
        nullable=False
    )
    code = db.Column(
        db.String,
        nullable=False
    )
    color = db.Column(
        db.String,
        nullable=False
    )
    #: Whether the tag is system-managed and cannot be modified by event managers.
    system = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'editing_tags',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    # relationship backrefs:
    # - revisions (EditingRevision.tags)

    @property
    def verbose_title(self):
        """Properly formatted title, including tag code."""
        return '{}: {}'.format(self.code, self.title)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', system=False, _text=self.title)


db.Table(
    'revision_tags',
    db.metadata,
    db.Column(
        'revision_id',
        db.ForeignKey('event_editing.revisions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'tag_id',
        db.ForeignKey('event_editing.tags.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_editing'
)
