# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


def _get_next_position(cls):
    def __get_next_position(context):
        event_id = context.current_parameters['event_id']
        res = db.session.query(db.func.max(cls.position)).filter_by(event_id=event_id, is_deleted=False).one()
        return (res[0] or 0) + 1
    return __get_next_position


class ReviewQuestionMixin(object):
    #: name of backref from event to questions
    event_backref_name = None

    @declared_attr
    def id(cls):
        return db.Column(
            db.Integer,
            primary_key=True
        )

    @declared_attr
    def event_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.events.id'),
            index=True,
            nullable=False
        )

    @declared_attr
    def field_type(cls):
        return db.Column(
            db.String,
            nullable=False
        )

    @declared_attr
    def title(cls):
        return db.Column(
            db.Text,
            nullable=False
        )

    @declared_attr
    def _no_score(cls):
        return db.Column(
            'no_score',
            db.Boolean,
            nullable=False,
            default=False
        )

    @declared_attr
    def position(cls):
        return db.Column(
            db.Integer,
            nullable=False,
            default=_get_next_position(cls)
        )

    @declared_attr
    def is_deleted(cls):
        return db.Column(
            db.Boolean,
            nullable=False,
            default=False
        )

    @declared_attr
    def is_required(self):
        return db.Column(
            db.Boolean,
            nullable=False,
            default=False
        )

    @declared_attr
    def field_data(cls):
        return db.Column(
            db.JSON,
            nullable=False,
            default={}
        )

    @declared_attr
    def description(cls):
        return db.Column(
            db.Text,
            nullable=False,
            default=''
        )

    @declared_attr
    def event(cls):
        return db.relationship(
            'Event',
            lazy=True,
            backref=db.backref(
                cls.event_backref_name,
                primaryjoin='({0}.event_id == Event.id) & ~{0}.is_deleted'.format(cls.__name__),
                order_by=cls.position,
                cascade='all, delete-orphan',
                lazy=True
            )
        )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', no_score=False, is_deleted=False, _text=self.title)

    def get_review_rating(self, review, allow_create=False):
        """Get the rating given in particular review.

        :param review: the review object
        :param allow_create: if there is not rating for that review a new one is created
        """
        results = [rating for rating in review.ratings if rating.question == self]
        rating = results[0] if results else None
        if rating is None and allow_create:
            rating_class = type(self).ratings.prop.mapper.class_
            rating = rating_class(question=self, review=review)
        return rating

    @hybrid_property
    def no_score(self):
        return self.field_type != 'rating' or self._no_score

    @no_score.expression
    def no_score(cls):
        return (cls.field_type != 'rating') | cls._no_score

    @no_score.setter
    def no_score(self, value):
        self._no_score = value
