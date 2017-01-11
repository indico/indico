# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderModeMixin, RenderMode
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
