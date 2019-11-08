# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.util.date_time import now_utc
from indico.util.string import format_repr, return_ascii, text_to_repr
from indico.util.struct.enum import IndicoEnum


class EditableType(int, IndicoEnum):
    paper = 1
    slides = 2


class EditingRevisionComment(RenderModeMixin, db.Model):
    __tablename__ = 'comments'
    __table_args__ = (db.CheckConstraint('(user_id IS NULL) = system', name='system_comment_no_user'),
                      {'schema': 'event_editing'})

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    revision_id = db.Column(
        db.ForeignKey('event_editing.revisions.id'),
        index=True,
        nullable=False
    )
    user_id = db.Column(
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    modified_dt = db.Column(
        UTCDateTime,
        nullable=True,
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether the comment is only visible to editors
    internal = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether the comment is system-generated and cannot be deleted/modified.
    system = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    _text = db.Column(
        'text',
        db.Text,
        nullable=False,
        default=''
    )
    text = RenderModeMixin.create_hybrid_property('_text')

    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'editing_comments',
            lazy='dynamic'
        )
    )
    revision = db.relationship(
        'EditingRevision',
        lazy=True,
        backref=db.backref(
            'comments',
            primaryjoin=('(EditingRevisionComment.revision_id == EditingRevision.id) & '
                         '~EditingRevisionComment.is_deleted'),
            order_by=created_dt,
            cascade='all, delete-orphan',
            lazy=True,
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'revision_id', 'user_id', internal=False, _text=text_to_repr(self.text))
