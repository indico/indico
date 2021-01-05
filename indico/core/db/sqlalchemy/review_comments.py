# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.util.date_time import now_utc


class ReviewCommentMixin(RenderModeMixin):
    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown
    user_backref_name = None
    user_modified_backref_name = None
    TIMELINE_TYPE = 'comment'

    @declared_attr
    def id(cls):
        return db.Column(
            db.Integer,
            primary_key=True
        )

    @declared_attr
    def user_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('users.users.id'),
            index=True,
            nullable=False
        )

    @declared_attr
    def _text(cls):
        return db.Column(
            'text',
            db.Text,
            nullable=False
        )

    @declared_attr
    def modified_by_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('users.users.id'),
            index=True,
            nullable=True
        )

    @declared_attr
    def created_dt(cls):
        return db.Column(
            UTCDateTime,
            nullable=False,
            default=now_utc
        )

    @declared_attr
    def modified_dt(cls):
        return db.Column(
            UTCDateTime,
            nullable=True
        )

    @declared_attr
    def is_deleted(cls):
        return db.Column(
            db.Boolean,
            nullable=False,
            default=False
        )

    @declared_attr
    def user(cls):
        return db.relationship(
            'User',
            lazy=True,
            foreign_keys=cls.user_id,
            backref=db.backref(
                cls.user_backref_name,
                primaryjoin='({0}.user_id == User.id) & ~{0}.is_deleted'.format(cls.__name__),
                lazy='dynamic'
            )
        )

    @declared_attr
    def modified_by(cls):
        return db.relationship(
            'User',
            lazy=True,
            foreign_keys=cls.modified_by_id,
            backref=db.backref(
                cls.user_modified_backref_name,
                primaryjoin='({0}.modified_by_id == User.id) & ~{0}.is_deleted'.format(cls.__name__),
                lazy='dynamic'
            )
        )

    text = RenderModeMixin.create_hybrid_property('_text')
