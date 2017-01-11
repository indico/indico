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

from indico.core.db import db
from indico.util.string import return_ascii, format_repr
from sqlalchemy.ext.declarative import declared_attr


class ReviewRatingMixin(object):
    question_class = None
    review_class = None

    @declared_attr
    def id(cls):
        return db.Column(
            db.Integer,
            primary_key=True
        )

    @declared_attr
    def question_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('{}.id'.format(cls.question_class.__table__.fullname)),
            index=True,
            nullable=False
        )

    @declared_attr
    def review_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('{}.id'.format(cls.review_class.__table__.fullname)),
            index=True,
            nullable=False
        )

    @declared_attr
    def value(cls):
        return db.Column(
            db.Integer,
            nullable=False
        )

    @declared_attr
    def question(cls):
        return db.relationship(
            cls.question_class,
            lazy=True,
            backref=db.backref(
                'ratings',
                cascade='all, delete-orphan',
                lazy=True
            )
        )

    @declared_attr
    def review(cls):
        return db.relationship(
            cls.review_class,
            lazy=True,
            backref=db.backref(
                'ratings',
                cascade='all, delete-orphan',
                lazy=True
            )
        )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'review_id', 'question_id')
