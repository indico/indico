# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.editing.models.editable import EditableType
from indico.util.string import format_repr, return_ascii


class EditingFileType(db.Model):
    __tablename__ = 'file_types'

    @declared_attr
    def __table_args__(cls):
        return (
            db.Index(
                'ix_uq_file_types_event_id_type_name_lower',
                cls.event_id,
                cls.type,
                db.func.lower(cls.name),
                unique=True,
            ),
            {'schema': 'event_editing'},
        )

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    type = db.Column(
        PyIntEnum(EditableType),
        nullable=False
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    extensions = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    allow_multiple_files = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    required = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    publishable = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    filename_template = db.Column(
        db.String,
        nullable=True
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'editing_file_types',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    # relationship backrefs:
    # - files (EditingRevisionFile.file_type)
    # - review_conditions (EditingReviewCondition.file_types)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'extensions', allow_multiple_files=False, required=False,
                           publishable=False, filename_template=None, _text=self.name)
