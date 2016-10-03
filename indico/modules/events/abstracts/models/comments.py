# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import format_repr, return_ascii, text_to_repr


class AbstractComment(db.Model):
    __tablename__ = 'abstract_comments'
    __table_args__ = {'schema': 'event_abstracts'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    text = db.Column(
        db.Text,
        nullable=False
    )
    #: ID of the user who last modified the comment
    modified_by_id = db.Column(
        db.Integer,
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
        nullable=True
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    abstract = db.relationship(
        'Abstract',
        lazy=True,
        backref=db.backref(
            'comments',
            primaryjoin='(AbstractComment.abstract_id == Abstract.id) & ~AbstractComment.is_deleted',
            order_by=created_dt,
            cascade='all, delete-orphan',
            lazy=True,
        )
    )
    user = db.relationship(
        'User',
        lazy=True,
        foreign_keys=user_id,
        backref=db.backref(
            'abstract_comments',
            primaryjoin='(AbstractComment.user_id == User.id) & ~AbstractComment.is_deleted',
            lazy='dynamic'
        )
    )
    modified_by = db.relationship(
        'User',
        lazy=True,
        foreign_keys=modified_by_id,
        backref=db.backref(
            'modified_abstract_comments',
            primaryjoin='(AbstractComment.modified_by_id == User.id) & ~AbstractComment.is_deleted',
            lazy='dynamic'
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'abstract_id', is_deleted=False, _text=text_to_repr(self.text))

    def can_edit(self, user):
        if user is None:
            return False
        return self.user == user or self.abstract.event_new.can_manage(user)
