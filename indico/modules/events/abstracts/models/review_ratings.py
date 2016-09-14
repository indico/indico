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

from indico.core.db.sqlalchemy import db
from indico.util.string import format_repr, return_ascii


class AbstractReviewRating(db.Model):
    __tablename__ = 'abstract_review_ratings'
    __table_args__ = (db.UniqueConstraint('review_id', 'question_id'),
                      {'schema': 'event_abstracts'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    question_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstract_review_questions.id'),
        index=True,
        nullable=False
    )
    review_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstract_reviews.id'),
        index=True,
        nullable=False
    )
    value = db.Column(
        db.Integer,
        nullable=False
    )
    question = db.relationship(
        'AbstractReviewQuestion',
        lazy=True,
        backref=db.backref(
            'ratings',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    review = db.relationship(
        'AbstractReview',
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
