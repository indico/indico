# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.editing.models.editable import EditableType
from indico.util.string import format_repr, return_ascii


class EditingReviewCondition(db.Model):
    __tablename__ = 'review_conditions'
    __table_args__ = {'schema': 'event_editing'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    type = db.Column(
        PyIntEnum(EditableType),
        nullable=False
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'editing_review_conditions',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    file_types = db.relationship(
        'EditingFileType',
        secondary='event_editing.review_condition_file_types',
        collection_class=set,
        lazy=False,
        backref=db.backref(
            'review_conditions',
            collection_class=set,
            lazy=True
        )
    )

    # relationship backrefs:
    # - file_types (EditingFileType.review_conditions)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id')


db.Table(
    'review_condition_file_types',
    db.metadata,
    db.Column(
        'review_condition_id',
        db.ForeignKey('event_editing.review_conditions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'file_type_id',
        db.ForeignKey('event_editing.file_types.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_editing'
)
